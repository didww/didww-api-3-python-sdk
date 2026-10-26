"""The prices services: price lookups and price files."""

from __future__ import annotations

import collections
import dataclasses
import itertools
import os
import secrets
import time
import zlib
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from didww import _http, _json
from didww.configuration import _AUDIENCE_SMS, _AUDIENCE_VOICE_IN, _AUDIENCE_VOICE_OUT
from didww.exceptions import DidwwClientError, DidwwPricesError, PricesErrorKind
from didww.prices import _headers
from didww.prices._rows import SmsInPrice, SmsOutPrice, VoiceInPrice, VoiceOutPrice, parse_lookup

_FILE_NAME = "prices.csv.gz"
_LOOKUP_PATH = "lookup/prices"
_CODE_PRICE_PLAN_NOT_ASSIGNED = "price_plan_not_assigned"
_CODE_PRICE_NOT_FOUND = "price_not_found"
_MAX_UNAVAILABLE_RETRIES = 2
_MAX_UNAVAILABLE_RETRY_AFTER = 60
_RANDOM = secrets.SystemRandom()

_PriceList = collections.namedtuple(
    "_PriceList", "url_attribute audience prefix row_class required optional any_of")

VOICE_IN = _PriceList("_voice_in_prices_url", _AUDIENCE_VOICE_IN, "", VoiceInPrice,
                      ("number",), ("src_country_iso",), ())
VOICE_OUT = _PriceList("_voice_out_prices_url", _AUDIENCE_VOICE_OUT, "", VoiceOutPrice, ("number",), (), ())
SMS_OUT_A2P = _PriceList("_sms_prices_url", _AUDIENCE_SMS, "sms_out/a2p/", SmsOutPrice,
                         (), (), ("dst_number", "dst_country_iso"))
SMS_OUT_P2P = SMS_OUT_A2P._replace(prefix="sms_out/p2p/")
SMS_OUT_OTP = SMS_OUT_A2P._replace(prefix="sms_out/otp/")
SMS_IN = _PriceList("_sms_prices_url", _AUDIENCE_SMS, "sms_in/", SmsInPrice,
                    (), (), ("dst_number", "dst_country_iso"))

_KINDS = {
    400: PricesErrorKind.BAD_REQUEST,
    401: PricesErrorKind.NOT_AUTHORIZED,
    403: PricesErrorKind.ACCESS_DENIED,
    406: PricesErrorKind.NOT_ACCEPTABLE,
    429: PricesErrorKind.TOO_MANY_REQUESTS,
    503: PricesErrorKind.SERVICE_UNAVAILABLE,
}


@dataclasses.dataclass(frozen=True)
class PriceFile:
    """The answer to a price file request.

    Attributes:
        status_code: 200, or 304 when the file has not changed since If-Modified-Since.
        last_modified: the Last-Modified of the answer as an aware UTC datetime, or None.
        content_length: the size of the file in bytes, or None when unknown (always on 304).
        filename: the file name of the Content-Disposition, or None.
        bytes_written: the bytes written by a download; 0 for ``head`` and 304.
    """

    status_code: int
    last_modified: Optional[datetime] = None
    content_length: Optional[int] = None
    filename: Optional[str] = None
    bytes_written: int = 0

    @property
    def not_modified(self):
        """Whether the file has not changed since the If-Modified-Since date sent (304)."""
        return self.status_code == 304


def join_v3(base, path):
    base = base[:-1] if base.endswith("/") else base
    if not base.endswith("/v3"):
        base += "/v3"
    return f"{base}/{path}"


class PricesService:
    """One price list of a prices service: its price file, a gzipped CSV, and its lookup.

    Obtain it from the price accessors of ``DidwwClient``, such as
    ``client.voice_in_prices()``. Requests carry an access token for the
    service host. Without a price plan of the service every call fails with
    ``PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED``.

    A failed call raises ``DidwwPricesError`` (see its ``kind``), or
    ``DidwwAuthError`` when no access token could be obtained. Redirects are
    never followed: a 3xx answer is ``UNEXPECTED_STATUS``. A 503 answer to a
    file request whose Retry-After is at most a minute is retried up to twice,
    after that Retry-After (at least a second) plus a small random delay; no
    other answer is retried, except once with a new token after a 401. Error
    bodies are read up to 1 MiB and within about the read timeout.
    """

    def __init__(self, client, price_list):
        self._client = client
        self._list = price_list
        self._base_url = getattr(client, price_list.url_attribute)
        self._sleep = time.sleep
        self._random = _RANDOM.random
        self._error_body_timeout = None

    @property
    def file_path(self):
        """The path of the price file under ``/v3``, such as ``sms_out/a2p/prices.csv.gz``."""
        return self._list.prefix + _FILE_NAME

    @property
    def lookup_path(self):
        """The path of the lookup under ``/v3``, such as ``sms_out/a2p/lookup/prices``."""
        return self._list.prefix + _LOOKUP_PATH

    @property
    def allowed_filters(self):
        """The lookup filter names this service accepts."""
        return self._list.required + self._list.optional + self._list.any_of

    def __repr__(self):
        parts = urlsplit(join_v3(self._base_url, self.lookup_path))
        netloc = parts.netloc.rpartition("@")[2]
        return f"PricesService({urlunsplit((parts.scheme, netloc, parts.path, '', ''))!r})"

    # --- Lookup ---

    def lookup(self, filters):
        """Returns the prices matching ``filters``, such as ``{"number": "18005550123"}``.

        Filter names are given without ``filter[...]``. None and blank values
        are dropped. A missing or unknown filter raises ``ValueError`` before
        any request; the formats of the values are checked by the service
        (``BAD_REQUEST``). The rows are frozen dataclasses with money as
        ``decimal.Decimal``.

        Raises:
            ValueError: A filter is missing or not allowed.
            DidwwPricesError: The service answered with another status than 200, or could not be reached.
            DidwwClientError: The 200 answer cannot be parsed or holds no prices.
        """
        params = self._lookup_params(filters)
        resp = self._send("GET", join_v3(self._base_url, self.lookup_path),
                          {"Accept": _http.JSONAPI_MEDIA_TYPE, "Accept-Encoding": "identity"}, params)
        try:
            if resp.status_code != 200:
                raise self._error(resp)
            body = bytearray()
            try:
                count = _http.copy_raw(resp, body.extend)
            except _http.BodyReadError as e:
                raise _read_error(e) from _http.detached(e.cause)
            _check_complete(count, _http.content_length(resp))
            coding = (resp.headers.get("Content-Encoding") or "identity").strip().lower()
        finally:
            resp.close()
        try:
            document = _json.loads(_decode_content(bytes(body), coding))
        except (ValueError, RecursionError, zlib.error) as e:
            raise DidwwClientError(f"Failed to parse price lookup: {type(e).__name__}: {e}") from e
        return parse_lookup(document, self._list.row_class)

    def _lookup_params(self, filters):
        if filters is None:
            filters = {}
        if not callable(getattr(filters, "items", None)):
            raise TypeError("filters must be a dict of filter names to values")
        given = {}
        for name, value in filters.items():
            if not isinstance(name, str):
                raise TypeError("filter names must be strings")
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (str, int)):
                raise TypeError(f"filter {name} must be a string")
            # str() of a str or int Enum member gives its name, not its value.
            value = str.__str__(value) if isinstance(value, str) else int.__repr__(value)
            if value.strip():
                given[name] = value

        allowed = self.allowed_filters
        unknown = [name for name in sorted(given) if name not in allowed]
        missing = [name for name in self._list.required if name not in given]
        if unknown:
            raise ValueError(f"Filter {', '.join(unknown)} is not allowed on {self.lookup_path}"
                             f" (allowed: {', '.join(allowed)})")
        if missing:
            raise ValueError(f"Filter {', '.join(missing)} is required on {self.lookup_path}")
        if self._list.any_of and not any(name in given for name in self._list.any_of):
            raise ValueError(f"One of filters {', '.join(self._list.any_of)} is required on {self.lookup_path}")
        return [(f"filter[{name}]", given[name]) for name in sorted(given)]

    # --- Price file ---

    def head(self, if_modified_since=None):
        """Returns the metadata of the price file without its content.

        A given ``if_modified_since``, a timezone-aware ``datetime``, is sent
        as If-Modified-Since in whole seconds; a file that has not changed
        since answers 304 (``PriceFile.not_modified``).

        Raises:
            ValueError: ``if_modified_since`` is a naive datetime or out of range.
            DidwwPricesError: The service answered with another status than 200 or 304, or could not be reached.
        """
        _headers.check_aware(if_modified_since)
        return self._request_file("HEAD", if_modified_since, None)

    def download(self, fileobj, if_modified_since=None):
        """Writes the price file to the binary file object ``fileobj`` exactly as served.

        The file stays gzipped (see ``PriceFileReader``) and ``fileobj`` is
        left open. A given ``if_modified_since`` is sent as in ``head``; a 304
        answer writes nothing. Only a 200 answer is written, but ``fileobj``
        may hold partial data when the transfer fails; a body shorter than its
        Content-Length is ``CONNECTION_ERROR``.

        Raises:
            ValueError: ``if_modified_since`` is a naive datetime or out of range.
            DidwwPricesError: The service answered with another status than 200 or 304, or the transfer failed.
            OSError: ``fileobj`` could not be written (raised as is).
        """
        if not callable(getattr(fileobj, "write", None)):
            raise TypeError("fileobj must be a binary file object")
        _headers.check_aware(if_modified_since)
        return self._request_file("GET", if_modified_since, fileobj.write)

    def download_to_file(self, path):
        """Downloads the price file to ``path``.

        The file is written to a temporary file next to ``path``, flushed to
        the disk and moved over ``path`` only when the whole file has arrived,
        so a failed download leaves an existing file as it was. The new file
        gets the mode of a new file (0666 minus the umask) and the
        Last-Modified of the answer as its modification time. On Windows the
        replacement fails while ``path`` is open, for example by a
        ``PriceFileReader``.

        Raises:
            DidwwPricesError: The service answered with another status than 200, or the transfer failed.
            OSError: The file could not be written, for example in a missing directory (then without a request).
        """
        return self._download_to_file(path, None)

    def fetch(self, path):
        """Downloads the price file to ``path`` like ``download_to_file`` unless the file there is current.

        The modification time of an existing file is sent as
        If-Modified-Since, and a 304 answer leaves the file untouched
        (``PriceFile.not_modified``). It trusts the modification time of any
        file at ``path``.

        Raises:
            DidwwPricesError: The service answered with another status than 200 or 304, or the transfer failed.
            OSError: The file could not be read or written.
        """
        if not _http.is_destination_path(path):
            raise TypeError("path must be a file path")
        try:
            seconds = os.stat(path).st_mtime_ns // 1_000_000_000
        except FileNotFoundError:
            if_modified_since = None
        else:
            try:
                if_modified_since = datetime.fromtimestamp(seconds, timezone.utc)
            except (OverflowError, OSError, ValueError):
                if_modified_since = None
        return self._download_to_file(path, if_modified_since)

    def _download_to_file(self, path, if_modified_since):
        if not _http.is_destination_path(path):
            raise TypeError("path must be a file path")
        with _http.AtomicFile(path) as target:
            price_file = self._request_file("GET", if_modified_since, target.file.write)
            if price_file.status_code == 200:
                last_modified = price_file.last_modified
                target.commit(mtime=int(last_modified.timestamp()) if last_modified is not None else None)
        return price_file

    def _request_file(self, method, if_modified_since, write):
        url = join_v3(self._base_url, self.file_path)
        headers = {"Accept": None, "Accept-Encoding": "identity"}
        if if_modified_since is not None:
            headers["If-Modified-Since"] = _headers.format_http_date(if_modified_since)
        for attempt in itertools.count(1):
            resp = self._send(method, url, headers)
            try:
                status = resp.status_code
                if status in (200, 304):
                    return self._price_file(resp, write if status == 200 else None)
                wait = self._unavailable_wait(resp, attempt)
                if wait is None:
                    raise self._error(resp)
                _http.read_bounded(resp, _http.MAX_ERROR_BODY, self._body_timeout())
            finally:
                resp.close()
            self._sleep(wait)

    def _unavailable_wait(self, resp, attempt):
        if resp.status_code != 503 or attempt > _MAX_UNAVAILABLE_RETRIES:
            return None
        retry_after = _http.retry_after_seconds(resp.headers.get("Retry-After"))
        if retry_after is None or retry_after > _MAX_UNAVAILABLE_RETRY_AFTER:
            return None
        return _http.spread(max(retry_after, 1), self._random)

    def _price_file(self, resp, write):
        status = resp.status_code
        length = _http.content_length(resp) if status == 200 else None
        written = 0
        if write is not None:
            try:
                written = _http.copy_raw(resp, write)
            except _http.BodyReadError as e:
                raise _read_error(e) from _http.detached(e.cause)
            _check_complete(written, length)
        return PriceFile(
            status_code=status,
            last_modified=_headers.parse_http_date(resp.headers.get("Last-Modified")),
            content_length=length,
            filename=_headers.content_disposition_filename(resp.headers.get("Content-Disposition")),
            bytes_written=written,
        )

    # --- Transport and errors ---

    def _send(self, method, url, headers, params=None):
        try:
            return self._client._service_transport.request(
                method, url, audience=self._list.audience, headers=headers, params=params)
        except _http.READ_ERRORS as e:
            raise DidwwPricesError(f"Prices service request failed: {type(e).__name__}",
                                   kind=PricesErrorKind.CONNECTION_ERROR) from _http.detached(e)

    def _body_timeout(self):
        if self._error_body_timeout is not None:
            return self._error_body_timeout
        return self._client._error_body_timeout

    def _error(self, resp):
        status = resp.status_code
        errors = _parse_errors(_http.read_error_body(resp, self._body_timeout()))
        code = _code(errors[0]) if errors else None
        if status == 404:
            code = code or _CODE_PRICE_PLAN_NOT_ASSIGNED
            kind = PricesErrorKind.PRICE_NOT_FOUND if code == _CODE_PRICE_NOT_FOUND \
                else PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED
        else:
            kind = _KINDS.get(status, PricesErrorKind.UNEXPECTED_STATUS)
        return DidwwPricesError(kind=kind, status_code=status, code=code, errors=errors,
                                retry_after=_http.retry_after_seconds(resp.headers.get("Retry-After")))


def _parse_errors(body):
    try:
        document = _json.loads(body)
    except (ValueError, RecursionError):
        return []
    if not isinstance(document, dict) or not isinstance(document.get("errors"), list):
        return []
    return [e for e in document["errors"] if isinstance(e, dict)]


def _code(error):
    code = error.get("code")
    if isinstance(code, str):
        return code or None
    if isinstance(code, int) and not isinstance(code, bool):
        return str(code)
    return None


def _read_error(error):
    if error.incomplete:
        message = "Prices service: incomplete body"
    else:
        message = f"Prices service: failed to read the answer: {type(error.cause).__name__}"
    return DidwwPricesError(message, kind=PricesErrorKind.CONNECTION_ERROR, status_code=200)


def _check_complete(count, expected):
    if expected is not None and count != expected:
        raise DidwwPricesError(f"Prices service: incomplete body: {count} of {expected} bytes",
                               kind=PricesErrorKind.CONNECTION_ERROR, status_code=200)


def _decode_content(body, coding):
    if coding in ("", "identity"):
        return body
    if coding not in ("gzip", "x-gzip", "deflate"):
        raise ValueError(f"unsupported Content-Encoding {coding!r}")
    try:
        return zlib.decompressobj(47).decompress(body)
    except zlib.error:
        if coding != "deflate":
            raise
    return zlib.decompressobj(-15).decompress(body)
