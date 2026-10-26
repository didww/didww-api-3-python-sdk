"""HTTP plumbing shared by the SDK: sessions, the bearer transport and bounded reads."""

import http.client
import io
import os
import re
import secrets
import socket
import ssl
import time
import zlib
from http.cookiejar import CookiePolicy
from urllib.parse import urlsplit

import requests
import urllib3
from requests.adapters import DEFAULT_POOLBLOCK, DEFAULT_POOLSIZE, HTTPAdapter
from requests.auth import AuthBase

JSONAPI_MEDIA_TYPE = "application/vnd.api+json"
MAX_ERROR_BODY = 1 << 20
DEFAULT_ERROR_BODY_TIMEOUT = 60.0
_CHUNK = 64 * 1024

# Exceptions a read of a streamed body can raise below requests.
READ_ERRORS = (urllib3.exceptions.HTTPError, http.client.HTTPException, OSError)


class _BearerAuth(AuthBase):
    """Sets ``Authorization: Bearer``; per request, so netrc and ``session.auth`` cannot replace it."""

    __slots__ = ("_value",)

    def __init__(self, access_token):
        self._value = "Bearer " + access_token

    def __call__(self, r):
        r.headers["Authorization"] = self._value
        return r

    def __repr__(self):
        return "_BearerAuth([FILTERED])"


class _NoAuth(AuthBase):
    """Sends no ``Authorization`` header, whatever netrc or ``session.auth`` hold."""

    def __call__(self, r):
        r.headers.pop("Authorization", None)
        return r


class _BlockAllCookies(CookiePolicy):
    netscape = True
    rfc2965 = False
    hide_cookie2 = True

    def set_ok(self, cookie, request):
        return False

    def return_ok(self, cookie, request):
        return False

    def domain_return_ok(self, domain, request):
        return False

    def path_return_ok(self, path, request):
        return False


class _Session(requests.Session):
    # Redirects are never followed: requests must not read a 3xx body or parse its Location.
    def get_redirect_target(self, resp):
        return None


def build_session(user_session, user_agent, keep_retries):
    """Builds an SDK session from the settings of ``user_session``, which is never changed.

    Proxies, TLS settings, ``trust_env`` and the adapters' pool sizes are kept;
    ``auth``, headers, hooks and cookies are not. ``keep_retries`` keeps the
    adapters' ``max_retries``; otherwise urllib3 resends nothing. Only gzip and
    deflate are accepted as content codings, the ones an error body can undo.
    """
    session = _Session()
    if user_session is not None:
        session.proxies.update(user_session.proxies)
        session.verify = user_session.verify
        session.cert = user_session.cert
        session.trust_env = user_session.trust_env
        for prefix, adapter in user_session.adapters.items():
            session.mount(
                prefix,
                HTTPAdapter(
                    pool_connections=getattr(adapter, "_pool_connections", DEFAULT_POOLSIZE),
                    pool_maxsize=getattr(adapter, "_pool_maxsize", DEFAULT_POOLSIZE),
                    max_retries=getattr(adapter, "max_retries", 0) if keep_retries else 0,
                    pool_block=getattr(adapter, "_pool_block", DEFAULT_POOLBLOCK),
                ),
            )
    session.cookies.set_policy(_BlockAllCookies())
    session.headers["User-Agent"] = user_agent
    session.headers["Accept-Encoding"] = "gzip, deflate"
    return session


class _Transport:
    """Sends one request with the access token of an audience.

    Redirects are never followed and the response is always streamed, so the
    caller reads it and must close it. A 401 evicts the refused token and
    sends the request once more with a new one; a 403 is returned as is.
    """

    def __init__(self, session, tokens, timeout):
        self.session = session
        self.tokens = tokens
        self.timeout = timeout

    def request(self, method, url, *, audience, headers=None, params=None, data=None,
                files=None, timeout=None):
        kwargs = {
            "headers": headers,
            "params": params,
            "data": data,
            "files": files,
            "allow_redirects": False,
            "stream": True,
            "timeout": timeout if timeout is not None else self.timeout,
        }
        if audience is None:
            return self.session.request(method, url, auth=_NoAuth(), **kwargs)

        token = self.tokens.token(audience)
        resp = self.session.request(method, url, auth=_BearerAuth(token.access_token), **kwargs)
        if resp.status_code != 401 or not _replayable(data, files):
            return resp

        self.tokens.invalidate(audience, token.access_token)
        resp.close()
        token = self.tokens.token(audience)
        resp = self.session.request(method, url, auth=_BearerAuth(token.access_token), **kwargs)
        if resp.status_code == 401:
            self.tokens.invalidate(audience, token.access_token)
        return resp


def _replayable(data, files):
    if data is not None and not isinstance(data, (bytes, str)):
        return False
    for _, value in files or ():
        content = value[1] if isinstance(value, tuple) else value
        if content is not None and not isinstance(content, (bytes, str)):
            return False
    return True


class BodyReadError(Exception):
    """A read of a response body failed or ran out of time; ``cause`` is the failure."""

    def __init__(self, cause):
        super().__init__(type(cause).__name__)
        self.cause = cause

    @property
    def incomplete(self):
        return any(
            isinstance(e, (http.client.IncompleteRead, urllib3.exceptions.IncompleteRead))
            for e in exception_chain(self.cause)
        )


def _is_urllib3_response(raw):
    return isinstance(raw, urllib3.response.HTTPResponse)


def raw_read(raw, n):
    """Reads up to ``n`` bytes of the body as served, without content decoding."""
    if _is_urllib3_response(raw):
        return raw.read(n, decode_content=False)
    return raw.read(n)


def _read1(raw):
    # One socket read per call: urllib3 2.x has read1; urllib3 1.26 does not,
    # but its http.client response does. Other objects (test doubles) are
    # read with their own read1 or read.
    if _is_urllib3_response(raw):
        read1 = getattr(raw, "read1", None)
        if read1 is not None:
            return lambda n: read1(n, decode_content=False)
        fp_read1 = getattr(getattr(raw, "_fp", None), "read1", None)
        if fp_read1 is not None:
            return fp_read1
        return lambda n: raw.read(n, decode_content=False)
    read1 = getattr(raw, "read1", None)
    return read1 if read1 is not None else raw.read


def read_bounded(resp, limit=MAX_ERROR_BODY, timeout=DEFAULT_ERROR_BODY_TIMEOUT, strict=False):
    """Reads at most ``limit`` raw bytes of ``resp`` within about ``timeout`` seconds.

    Each read waits for at most one socket read, so a trickling body cannot
    hold it past the deadline by more than one read timeout. Without
    ``strict`` a failed or late read returns what was read so far; with it,
    ``BodyReadError`` is raised.
    """
    deadline = time.monotonic() + timeout
    read = _read1(resp.raw)
    buf = bytearray()
    first = True
    try:
        while len(buf) < limit:
            if not first and time.monotonic() >= deadline:
                if strict:
                    raise BodyReadError(TimeoutError("the response body was not read in time"))
                break
            first = False
            chunk = read(min(_CHUNK, limit - len(buf)))
            if not chunk:
                break
            buf += chunk
    except READ_ERRORS as e:
        if strict:
            raise BodyReadError(e) from e
    if strict:
        expected = content_length(resp)
        if expected is not None and len(buf) < min(expected, limit):
            raise BodyReadError(http.client.IncompleteRead(b"", expected - len(buf)))
    return bytes(buf)


def read_error_body(resp, timeout=DEFAULT_ERROR_BODY_TIMEOUT):
    """Reads an error body bounded in size and time, undoing gzip or deflate content coding."""
    body = read_bounded(resp, MAX_ERROR_BODY, timeout)
    coding = (resp.headers.get("Content-Encoding") or "identity").strip().lower()
    if coding in ("", "identity"):
        return body
    if coding not in ("gzip", "x-gzip", "deflate"):
        return b""
    for wbits in (47, -15):
        try:
            return zlib.decompressobj(wbits).decompress(body, MAX_ERROR_BODY)
        except zlib.error:
            continue
    return b""


def copy_raw(resp, write):
    """Copies the raw (still content-coded) body of ``resp`` to ``write`` and returns the byte count.

    A read failure raises ``BodyReadError``; a failure of ``write`` propagates as is.
    """
    raw = resp.raw
    count = 0
    while True:
        try:
            chunk = raw_read(raw, _CHUNK)
        except READ_ERRORS as e:
            raise BodyReadError(e) from e
        if not chunk:
            return count
        write_all(write, chunk)
        count += len(chunk)


def write_all(write, chunk):
    """Writes all of ``chunk``, looping over short writes of raw file objects.

    ``None`` from a raw file object means it would block and wrote nothing;
    from any other writer it means the whole chunk was taken.
    """
    raw = isinstance(getattr(write, "__self__", None), io.RawIOBase)
    while chunk:
        n = write(chunk)
        if n is None and not raw:
            return
        if n is None or n <= 0:
            raise OSError("the destination accepted no data")
        if n >= len(chunk):
            return
        chunk = chunk[n:]


def content_length(resp):
    """The Content-Length of ``resp`` as an int, or None when absent, malformed or chunked."""
    value = resp.headers.get("Content-Length")
    if value is None or "chunked" in resp.headers.get("Transfer-Encoding", "").lower():
        return None
    # A repeated header arrives joined with commas; equal values count once.
    values = {v.strip(" \t") for v in value.split(",")}
    if len(values) != 1:
        return None
    value = values.pop()
    if not re.fullmatch(r"[0-9]{1,18}", value):
        return None
    return int(value)


class RawReader:
    """A binary file object over the raw body of ``resp`` that counts the bytes read.

    Read failures raise ``BodyReadError``; ``eof`` tells whether the end of the body was reached.
    """

    def __init__(self, resp):
        self._raw = resp.raw
        self.count = 0
        self.eof = False

    def readable(self):
        return True

    def read(self, n=-1):
        if n is None or n < 0:
            n = _CHUNK
        try:
            chunk = raw_read(self._raw, n)
        except READ_ERRORS as e:
            raise BodyReadError(e) from e
        if not chunk and n:
            self.eof = True
        self.count += len(chunk)
        return chunk


class AtomicFile:
    """A temporary file next to ``path`` that replaces it only on ``commit``.

    It is created with mode 0666 minus the umask, as a new file opened with
    ``open(path, "wb")`` would be; it replaces a file or symlink at ``path``,
    which does not keep that file's permissions. Leaving the context without
    a commit removes it.
    """

    def __init__(self, path):
        path = os.fsdecode(os.fspath(path))
        directory, name = os.path.split(path)
        self.path = path
        self.temp_path = os.path.join(directory, f".{name}.{secrets.token_hex(8)}.tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
        fd = os.open(self.temp_path, flags, 0o666)
        try:
            self.file = os.fdopen(fd, "wb")
        except BaseException:
            os.close(fd)
            _unlink(self.temp_path)
            raise
        self._committed = False

    def commit(self, mtime=None):
        """Flushes the file to disk and moves it over ``path``; ``mtime`` is in whole seconds."""
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
        if mtime is not None:
            ns = int(mtime) * 1_000_000_000
            os.utime(self.temp_path, ns=(ns, ns))
        os.replace(self.temp_path, self.path)
        self._committed = True

    def discard(self):
        try:
            self.file.close()
        finally:
            if not self._committed:
                _unlink(self.temp_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self._committed:
            self.discard()
        return False


def _unlink(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def is_destination_path(dest):
    return isinstance(dest, (str, bytes, os.PathLike))


def exception_chain(exc):
    """``exc`` and every exception it wraps through causes, contexts, args and ``reason``."""
    seen = set()
    stack = [exc]
    out = []
    while stack:
        e = stack.pop()
        if not isinstance(e, BaseException) or id(e) in seen:
            continue
        seen.add(id(e))
        out.append(e)
        stack.append(e.__cause__)
        stack.append(e.__context__)
        stack.append(getattr(e, "reason", None))
        stack.extend(a for a in getattr(e, "args", ()) if isinstance(a, BaseException))
    return out


_DROPPED_CONNECTION = (ssl.SSLEOFError, ConnectionResetError, ConnectionAbortedError,
                       BrokenPipeError, socket.timeout, TimeoutError)
_TLS_ERRORS = (ssl.SSLError, urllib3.exceptions.SSLError, requests.exceptions.SSLError)


def is_tls_error(exc):
    """Whether ``exc`` is a certificate or TLS protocol failure, which a retry cannot fix.

    A connection dropped or timed out during the handshake is not one.
    """
    chain = exception_chain(exc)
    if any(isinstance(e, _DROPPED_CONNECTION) or _is_unexpected_eof(e) for e in chain):
        return False
    return any(isinstance(e, _TLS_ERRORS) for e in chain)


def _is_unexpected_eof(e):
    # Python 3.9 with OpenSSL 3 raises a plain SSLError where 3.10+ raises SSLEOFError.
    if not isinstance(e, ssl.SSLError):
        return False
    return (getattr(e, "reason", None) == "UNEXPECTED_EOF_WHILE_READING"
            or "unexpected eof while reading" in str(e).lower())


def detached(exc):
    """Drops the requests and responses that ``requests`` exceptions in the chain hold.

    Their headers carry the API key or the access token.
    """
    for e in exception_chain(exc):
        if isinstance(e, requests.exceptions.RequestException):
            e.request = None
            e.response = None
    return exc


def retry_after_seconds(value):
    """The delay-seconds of a Retry-After header, or None for an HTTP date or anything else."""
    if value is None:
        return None
    value = value.strip(" \t")
    if not re.fullmatch(r"[0-9]{1,9}", value):
        return None
    return int(value)


def spread(seconds, random):
    """``seconds`` plus up to a fifth of it, or up to a second when that is more."""
    return seconds + random() * max(1.0, seconds / 5)


def origin(url):
    """``(scheme, host, port)`` of an absolute http or https URL without user info, or None."""
    if not isinstance(url, str) or "\\" in url or any(c <= " " or c == "\x7f" for c in url):
        return None
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https") or not parts.hostname or "@" in parts.netloc:
        return None
    host = parts.hostname
    if host.endswith("."):
        host = host[:-1]
    return scheme, host, port or (443 if scheme == "https" else 80)


def format_origin(o):
    scheme, host, port = o
    if ":" in host:
        host = f"[{host}]"
    return f"{scheme}://{host}:{port}"


def log(logger, level, msg, *args, exc_info=None):
    """Logs through ``logger``; a failing logger never fails the call."""
    try:
        logger.log(level, msg, *args, exc_info=exc_info)
    except Exception:
        pass


def log_enabled(logger, level):
    try:
        return bool(logger.isEnabledFor(level))
    except Exception:
        return False
