"""Access tokens for the DIDWW API.

The client exchanges its API key for short-lived access tokens at the token
service (``POST {auth_url}/token``), one per service host (audience), and
sends them as ``Authorization: Bearer``. Tokens are kept in a ``TokenStore``
and replaced when a service refuses them (401), never ahead of their expiry.
"""

from __future__ import annotations

import abc
import copy
import contextvars
import dataclasses
import hashlib
import hmac
import logging
import math
import os
import re
import secrets
import threading
import time
import weakref
from datetime import datetime, timezone
from typing import Optional, Tuple

import requests

from didww import _json
from didww._http import (
    BodyReadError,
    MAX_ERROR_BODY,
    _NoAuth,
    detached,
    is_tls_error,
    log,
    log_enabled,
    read_bounded,
    retry_after_seconds,
    spread,
)
from didww.exceptions import AuthErrorKind, DidwwAuthError

_HEADER_TOKEN_RE = re.compile(r"[\x21-\x7e]+")


@dataclasses.dataclass(frozen=True, repr=False)
class AccessToken:
    """An access token granted by the token service. Immutable.

    ``repr()`` and ``str()`` never show the access token; ``to_dict()`` does,
    so that a ``TokenStore`` can persist it: protect what it returns like the
    API key.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 0
    aud: Tuple[str, ...] = ()
    scope: Optional[str] = None
    api_version: Optional[str] = None
    minted_at: Optional[datetime] = None

    def __post_init__(self):
        aud = self.aud
        if aud is None:
            aud = ()
        elif isinstance(aud, str):
            aud = (aud,)
        object.__setattr__(self, "aud", tuple(aud))

    def __repr__(self):
        return (
            f"AccessToken(access_token='[FILTERED]', token_type={self.token_type!r}, "
            f"expires_in={self.expires_in!r}, aud={self.aud!r}, scope={self.scope!r}, "
            f"api_version={self.api_version!r}, minted_at={self.minted_at!r})"
        )

    __str__ = __repr__

    def to_dict(self):
        """The token under its wire names, ``minted_at`` as ISO 8601; it includes the access token."""
        minted_at = None
        if self.minted_at is not None:
            minted_at = self.minted_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "aud": list(self.aud),
            "scope": self.scope,
            "api_version": self.api_version,
            "minted_at": minted_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Builds a token from ``to_dict()`` output. Unknown keys are ignored.

        Raises ValueError for a value of the wrong type; the message never
        contains the access token.
        """
        if not isinstance(data, dict):
            raise ValueError("token data must be a dict")
        access_token = data.get("access_token")
        if not isinstance(access_token, str):
            raise ValueError("access_token must be a string")
        expires_in = data.get("expires_in", 0)
        if not isinstance(expires_in, int) or isinstance(expires_in, bool):
            raise ValueError("expires_in must be an integer")
        aud = data.get("aud", ())
        if isinstance(aud, str):
            aud = (aud,)
        if not isinstance(aud, (list, tuple)) or not all(isinstance(a, str) for a in aud):
            raise ValueError("aud must be a string or a list of strings")
        fields = {}
        for name in ("token_type", "scope", "api_version"):
            value = data.get(name)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{name} must be a string")
            fields[name] = value
        return cls(
            access_token=access_token,
            token_type=fields["token_type"] or "Bearer",
            expires_in=expires_in,
            aud=tuple(aud),
            scope=fields["scope"],
            api_version=fields["api_version"],
            minted_at=_parse_minted_at(data.get("minted_at")),
        )


def _parse_minted_at(value):
    if not isinstance(value, str):
        return None
    m = re.fullmatch(r"([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{1,9}))?(Z|[+-][0-9]{2}:[0-9]{2})", value)
    if not m:
        return None
    fraction = (m.group(2) or "").ljust(6, "0")[:6]
    zone = "+00:00" if m.group(3) == "Z" else m.group(3)
    try:
        return datetime.fromisoformat(f"{m.group(1)}.{fraction}{zone}")
    except ValueError:
        return None


class TokenStore(abc.ABC):
    """Where access tokens are kept between calls.

    Keys cover the token service, a digest of the API key, the audience, the
    API version and the scope, so one store can serve several clients and
    processes. The store holds live bearer tokens: protect it like the API key.

    The SDK calls only ``get``, ``set`` and ``delete``, so any object with
    these methods works; subclassing is optional. Calls to a store other than
    ``MemoryTokenStore`` are given 10 seconds each; a store that fails or
    takes longer is logged and skipped, never failing the API call.
    Processes that share a store are not serialized: on a cold start each
    may mint its own token.
    """

    @abc.abstractmethod
    def get(self, key: str) -> Optional[AccessToken]:
        """Returns the token stored under ``key``, or None when there is none or it expired."""

    @abc.abstractmethod
    def set(self, key: str, token: AccessToken, ttl: float) -> None:
        """Stores ``token`` under ``key`` for ``ttl`` seconds; ``ttl <= 0`` means no expiry."""

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Removes the token stored under ``key``, if any."""


_MEMORY_STORES = weakref.WeakSet()


class MemoryTokenStore(TokenStore):
    """A thread-safe in-process ``TokenStore``. Expired tokens are dropped on read."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._entries = {}
        _MEMORY_STORES.add(self)

    def get(self, key):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            token, deadline = entry
            if deadline is not None and self._clock() >= deadline:
                del self._entries[key]
                return None
            return token

    def set(self, key, token, ttl):
        deadline = self._clock() + ttl if ttl and ttl > 0 else None
        with self._lock:
            self._entries[key] = (token, deadline)

    def delete(self, key):
        with self._lock:
            self._entries.pop(key, None)

    def clear(self):
        """Removes every token."""
        with self._lock:
            self._entries.clear()

    def __repr__(self):
        return f"MemoryTokenStore(entries={len(self._entries)})"


# The store of clients built without one: shared by the whole process.
_DEFAULT_STORE = MemoryTokenStore()

CACHE_KEY_PREFIX = "didww:token:v1:"
MAX_MINT_ATTEMPTS = 4
_BACKOFF_BASE = 0.5
_BACKOFF_CAP = 8.0
_MINT_TIMEOUT = 10.0
_STORE_TIMEOUT = 10.0
_FLIGHT_WAIT_TIMEOUT = 300.0
_RANDOM = secrets.SystemRandom()

_STORE_READ_FAILED = "DIDWW token store read failed"
_STORE_WRITE_FAILED = "DIDWW token store write failed"
_STORE_WRITE_SKIPPED = "DIDWW token store write skipped"
_STORE_DELETE_FAILED = "DIDWW token store delete failed"
_FAILED = object()

# Coordination state of the process, keyed by (id(store), cache key): mints in
# flight, the per-key store locks and the tokens refused by the API. The 429
# windows are keyed by token service and API key digest.
_REGISTRY_LOCK = threading.Lock()
_FLIGHTS = {}
_KEY_LOCKS = {}
_REFUSED = {}
_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMITS = {}


def _after_fork_in_child():
    # Locks held by other threads at fork time would stay held forever.
    global _REGISTRY_LOCK, _FLIGHTS, _KEY_LOCKS, _RATE_LIMIT_LOCK
    _REGISTRY_LOCK = threading.Lock()
    _FLIGHTS = {}
    _KEY_LOCKS = {}
    _RATE_LIMIT_LOCK = threading.Lock()
    for store in list(_MEMORY_STORES):
        store._lock = threading.Lock()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_after_fork_in_child)


def _reset_coordination():
    """Forgets every flight, store lock, refused token and 429 window (tests)."""
    global _REFUSED, _RATE_LIMITS
    _after_fork_in_child()
    _REFUSED = {}
    _RATE_LIMITS = {}
    _DEFAULT_STORE.clear()


def _forget_rate_limits():
    """Forgets every 429 window of the process (tests)."""
    with _RATE_LIMIT_LOCK:
        _RATE_LIMITS.clear()


def _sha256_hex(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _same_token(a, b):
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _is_header_token(value):
    return isinstance(value, str) and _HEADER_TOKEN_RE.fullmatch(value) is not None


class _Flight:
    __slots__ = ("event", "token", "error")

    def __init__(self):
        self.event = threading.Event()
        self.token = None
        self.error = None


class _TokenProvider:
    """Mints access tokens per audience, caches them in the store and shares one mint among concurrent callers.

    The mint runs on the thread of the first caller. 5xx answers and
    transport failures other than TLS errors are tried up to
    ``MAX_MINT_ATTEMPTS`` times in all, with a full-jitter backoff. Each
    attempt connects within 10 s, waits up to 10 s for each read of the
    answer, and must receive the body within 10 s of sending. A 429
    blocks further mints of the same token service and API key, in this
    process, until its Retry-After plus a small random delay has passed.
    """

    def __init__(self, session, auth_url, api_key, api_version, scope, store, logger, user_agent):
        self._session = session
        self._auth_url = auth_url
        self._token_url = auth_url + "/token"
        self._api_key = api_key
        self._api_key_digest = _sha256_hex(api_key)
        self._api_version = api_version
        self._scope = scope
        self._store = store
        self._logger = logger
        self._user_agent = user_agent
        self._sleep = time.sleep
        self._random = _RANDOM.random
        self._monotonic = time.monotonic
        self._now = lambda: datetime.now(timezone.utc)
        self._mint_timeout = _MINT_TIMEOUT
        self._store_timeout = _STORE_TIMEOUT

    def __repr__(self):
        return f"_TokenProvider(auth_url={self._auth_url!r})"

    def cache_key(self, audience):
        material = "\n".join([self._auth_url, self._api_key_digest, audience, self._api_version, self._scope or "-"])
        return CACHE_KEY_PREFIX + _sha256_hex(material)

    def token(self, audience):
        """Returns the cached token of ``audience`` or mints one; raises DidwwAuthError."""
        key = self.cache_key(audience)
        cached = self._read_cached(key)
        if cached is not None:
            return cached

        flight_key = (id(self._store), key)
        with _REGISTRY_LOCK:
            flight = _FLIGHTS.get(flight_key)
            leader = flight is None
            if leader:
                flight = _FLIGHTS[flight_key] = _Flight()
        if not leader:
            return self._await(flight)

        try:
            token = self._read_cached(key)
            if token is None:
                token = self._mint(audience)
                self._store_token(key, token)
            flight.token = token
            return token
        except DidwwAuthError as e:
            flight.error = e
            raise
        except BaseException as e:
            reason = "was interrupted" if not isinstance(e, Exception) else f"failed ({type(e).__name__})"
            flight.error = DidwwAuthError(f"Token service: the token request {reason}",
                                          kind=AuthErrorKind.CONNECTION_ERROR)
            raise
        finally:
            with _REGISTRY_LOCK:
                if _FLIGHTS.get(flight_key) is flight:
                    del _FLIGHTS[flight_key]
            flight.event.set()

    def invalidate(self, audience, refused_access_token):
        """Evicts the cached token of ``audience`` only while it is still the refused one.

        The refused token is remembered, so that a store that keeps it is not
        trusted until a new token has been stored.
        """
        key = self.cache_key(audience)
        registry_key = (id(self._store), key)
        _REFUSED[registry_key] = refused_access_token
        lock = self._key_lock(registry_key)
        if not lock.acquire(timeout=self._store_timeout):
            return
        try:
            stored = self._get_stored(key)
            if stored is not None and _same_token(stored.access_token, refused_access_token):
                self._call_store(lambda: self._store.delete(key), _STORE_DELETE_FAILED)
        finally:
            lock.release()

    def backoff(self, attempt):
        return self._random() * min(_BACKOFF_CAP, _BACKOFF_BASE * 2 ** min(attempt, 16))

    def _key_lock(self, registry_key):
        with _REGISTRY_LOCK:
            lock = _KEY_LOCKS.get(registry_key)
            if lock is None:
                lock = _KEY_LOCKS[registry_key] = threading.Lock()
            return lock

    def _read_cached(self, key):
        stored = self._get_stored(key)
        if stored is None:
            return None
        refused = _REFUSED.get((id(self._store), key))
        if refused is not None and _same_token(refused, stored.access_token):
            return None
        return stored

    def _get_stored(self, key):
        stored = self._call_store(lambda: self._store.get(key), _STORE_READ_FAILED)
        if stored is None or stored is _FAILED:
            return None
        if not isinstance(stored, AccessToken):
            failure = TypeError(f"get returned {type(stored).__name__}, not an AccessToken")
        elif not _is_header_token(stored.access_token):
            failure = ValueError("get returned an AccessToken whose access_token is not valid")
        else:
            return stored
        self._warn(_STORE_READ_FAILED, failure)
        return None

    def _store_token(self, key, token):
        registry_key = (id(self._store), key)
        refused_before = _REFUSED.get(registry_key)
        lock = self._key_lock(registry_key)
        if not lock.acquire(timeout=self._store_timeout):
            self._warn(_STORE_WRITE_SKIPPED, TimeoutError(
                f"the store lock was not free within {self._store_timeout:g} s"))
            return
        try:
            result = self._call_store(lambda: self._store.set(key, token, token.expires_in), _STORE_WRITE_FAILED)
            if result is not _FAILED and refused_before is not None \
                    and _REFUSED.get(registry_key) is refused_before:
                _REFUSED.pop(registry_key, None)
        finally:
            lock.release()

    def _call_store(self, call, failure_message):
        # The in-memory store is called directly; any other store runs on a
        # daemon thread bounded by the store timeout, so a hung store can
        # neither block the call nor the interpreter's exit.
        if type(self._store) is MemoryTokenStore:
            try:
                return call()
            except Exception as e:
                self._warn(failure_message, e)
                return _FAILED

        box = {}
        done = threading.Event()

        def run():
            try:
                box["value"] = call()
            except BaseException as e:
                box["error"] = e
            finally:
                done.set()

        try:
            # The caller's contextvars go along, as with asyncio.to_thread.
            threading.Thread(target=contextvars.copy_context().run, args=(run,),
                             name="didww-token-store", daemon=True).start()
        except RuntimeError as e:
            self._warn(failure_message, e)
            return _FAILED
        if not done.wait(self._store_timeout):
            self._warn(failure_message, TimeoutError(
                f"the store call did not finish within {self._store_timeout:g} s"))
            return _FAILED
        if "error" in box:
            self._warn(failure_message, box["error"])
            return _FAILED
        return box.get("value")

    def _await(self, flight):
        if not flight.event.wait(_FLIGHT_WAIT_TIMEOUT):
            raise DidwwAuthError("Token service: the token request did not finish in time",
                                 kind=AuthErrorKind.CONNECTION_ERROR)
        error = flight.error
        if error is not None:
            raise copy.copy(error) from error.__cause__
        return flight.token

    def _mint(self, audience):
        self._raise_if_rate_limited()
        request = {"aud": [audience], "api_version": self._api_version}
        if self._scope is not None:
            request["scope"] = self._scope
        payload = _json.dumps(request)

        start = self._monotonic()
        status, retry_after, body = self._post(payload)
        token = self._token_from(status, retry_after, body, audience)
        if log_enabled(self._logger, logging.DEBUG):
            log(self._logger, logging.DEBUG,
                "DIDWW token minted: aud %s, scope %s, api_version %s, expires_in %s, duration_ms %d",
                list(token.aud), token.scope, token.api_version, token.expires_in,
                int((self._monotonic() - start) * 1000))
        return token

    def _post(self, payload):
        # Sends the token request, retrying 5xx answers and transport failures
        # other than TLS errors with a full-jitter backoff. Errors are raised
        # outside the except blocks, so that no exception that may quote a
        # header value or hold a cut token body stays attached as context.
        attempt = 0
        while True:
            attempt += 1
            failure = unread = fatal = None
            try:
                status, retry_after, body = self._attempt(payload)
            except BodyReadError as e:
                unread = type(e.cause).__name__
            except (requests.exceptions.InvalidURL, requests.exceptions.InvalidHeader,
                    requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema,
                    requests.exceptions.URLRequired) as e:
                fatal = f"could not be sent ({type(e).__name__})"
            except requests.exceptions.RequestException as e:
                failure = e
            except Exception as e:
                fatal = f"failed ({type(e).__name__})"
            else:
                if status < 500 or attempt >= MAX_MINT_ATTEMPTS:
                    return status, retry_after, body

            if fatal is not None:
                raise DidwwAuthError(f"Token service: the token request {fatal}",
                                     kind=AuthErrorKind.CONNECTION_ERROR)
            if unread is not None and attempt >= MAX_MINT_ATTEMPTS:
                # The cut body of a 200 may hold the token: no cause is kept.
                raise DidwwAuthError(f"Token service: the token response could not be read ({unread})",
                                     kind=AuthErrorKind.CONNECTION_ERROR, status_code=200)
            if failure is not None and (attempt >= MAX_MINT_ATTEMPTS or is_tls_error(failure)):
                raise DidwwAuthError(f"Token service: {type(failure).__name__}: {failure}",
                                     kind=AuthErrorKind.CONNECTION_ERROR) from detached(failure)

            self._sleep(self.backoff(attempt))
            self._raise_if_rate_limited()

    def _attempt(self, payload):
        start = self._monotonic()
        resp = self._session.request(
            "POST",
            self._token_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "Api-Key": self._api_key,
                "User-Agent": self._user_agent,
            },
            auth=_NoAuth(),
            allow_redirects=False,
            stream=True,
            timeout=(self._mint_timeout, self._mint_timeout),
        )
        try:
            remaining = max(0.0, self._mint_timeout - (self._monotonic() - start))
            body = read_bounded(resp, MAX_ERROR_BODY, remaining, strict=resp.status_code == 200)
            return resp.status_code, resp.headers.get("Retry-After"), body
        finally:
            resp.close()

    def _token_from(self, status, retry_after, body, audience):
        fields = _json_object(body)
        error = _text(fields, "error")
        description = _text(fields, "error_description")

        if status == 200:
            token = AccessToken(
                access_token=_text(fields, "access_token") or "",
                token_type=_text(fields, "token_type") or "Bearer",
                expires_in=_non_negative_int(fields, "expires_in"),
                aud=_audience(fields),
                scope=_text(fields, "scope"),
                api_version=_text(fields, "api_version"),
                minted_at=self._now(),
            )
            self._verify_grant(token, audience)
            return token
        if status == 429:
            seconds = retry_after_seconds(retry_after)
            seconds = max(1, seconds) if seconds is not None else 1
            with _RATE_LIMIT_LOCK:
                _RATE_LIMITS[self._rate_limit_key()] = self._monotonic() + spread(seconds, self._random)
            raise DidwwAuthError(kind=AuthErrorKind.RATE_LIMITED, status_code=status, error=error,
                                 error_description=description, retry_after=seconds)
        if status == 400:
            kind = AuthErrorKind.INVALID_REQUEST
        elif status == 401:
            kind = AuthErrorKind.INVALID_CLIENT
        elif 500 <= status <= 599:
            kind = AuthErrorKind.SERVER_ERROR
        else:
            kind = AuthErrorKind.UNEXPECTED_STATUS
            if 300 <= status <= 399 and error is None and description is None:
                description = "the token request was redirected; redirects are not followed"
        raise DidwwAuthError(kind=kind, status_code=status, error=error, error_description=description)

    def _verify_grant(self, token, audience):
        if not _is_header_token(token.access_token):
            raise DidwwAuthError(kind=AuthErrorKind.INVALID_GRANT, status_code=200,
                                 error_description="the granted access token is empty or not a valid header value")
        if audience not in token.aud:
            raise DidwwAuthError(kind=AuthErrorKind.INVALID_GRANT, status_code=200,
                                 error_description=f"granted audience {list(token.aud)}, requested {audience}")
        if self._scope is not None and token.scope != self._scope:
            log(self._logger, logging.WARNING, "DIDWW token scope mismatch: requested %s, granted %s",
                self._scope, token.scope)
        if token.api_version != self._api_version:
            log(self._logger, logging.WARNING, "DIDWW token api_version mismatch: requested %s, granted %s",
                self._api_version, token.api_version)

    def _raise_if_rate_limited(self):
        key = self._rate_limit_key()
        with _RATE_LIMIT_LOCK:
            until = _RATE_LIMITS.get(key)
            if until is None:
                return
            remaining = until - self._monotonic()
            if remaining <= 0:
                del _RATE_LIMITS[key]
                return
        raise DidwwAuthError(kind=AuthErrorKind.RATE_LIMITED, status_code=429, error="rate_limit_exceeded",
                             retry_after=max(1, math.ceil(remaining)))

    def _rate_limit_key(self):
        return self._auth_url + "\n" + self._api_key_digest

    def _warn(self, message, failure):
        log(self._logger, logging.WARNING, message, exc_info=failure)


def _json_object(body):
    try:
        parsed = _json.loads(body)
    except (ValueError, RecursionError):
        parsed = None
    return parsed if isinstance(parsed, dict) else {}


def _text(fields, name):
    value = fields.get(name)
    return value if isinstance(value, str) else None


def _non_negative_int(fields, name):
    value = fields.get(name)
    if isinstance(value, int) and not isinstance(value, bool):
        return max(0, value)
    return 0


def _audience(fields):
    value = fields.get("aud")
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(a for a in value if isinstance(a, str))
    return ()
