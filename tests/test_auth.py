import contextvars
import logging
import os
import signal
import socket
import ssl
import threading
import time

import pytest
import requests
import urllib3

from didww import auth
from didww._http import is_tls_error, spread
from didww.auth import AccessToken, MemoryTokenStore, TokenStore
from didww.client import DidwwClient
from didww.configuration import Scope
from didww.exceptions import AuthErrorKind, DidwwAuthError
from tests.support.http_stub import (
    RawServer,
    Reply,
    fixture_bytes,
    fixture_json,
    http_response,
    self_signed_context,
    token_reply,
)

API = "api.didww.com"
SMS = "api-sms.didww.com"


def token_error(status, fixture, headers=None):
    return Reply(status, fixture_bytes(f"token/{fixture}"),
                 {"Content-Type": "application/json", **(headers or {})})


def mints(stub):
    return stub.hits("POST", "/token")


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


def record_sleeps(client, random=1.0):
    sleeps = []
    client._tokens._sleep = sleeps.append
    client._tokens._random = lambda: random
    return sleeps


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class DictStore(TokenStore):
    def __init__(self):
        self.data = {}
        self.ttls = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, token, ttl):
        self.data[key] = token
        self.ttls[key] = ttl

    def delete(self, key):
        self.data.pop(key, None)


class TestMintRequest:
    def test_body_and_headers(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        client = make_client()

        token = client._tokens.token(API)

        assert token.access_token == "test-access-token"
        (hit,) = mints(stub)
        assert hit.json() == fixture_json("token/create_request.json")
        assert hit.headers["Api-Key"] == "test-api-key"
        assert hit.headers["Content-Type"] == "application/json"
        assert hit.headers["Accept"] == "application/json"
        assert "Authorization" not in hit.headers
        assert "expires_in" not in hit.json()

    def test_body_with_scope(self, stub, make_client):
        stub.on("POST", "/token", token_reply(scope="read"))
        make_client(scope=Scope.READ)._tokens.token(API)
        assert mints(stub)[0].json() == fixture_json("token/create_request_read_scope.json")

    def test_body_with_api_version(self, stub, make_client):
        stub.on("POST", "/token", token_reply(api_version="2027-01-01"))
        make_client(api_version="2027-01-01")._tokens.token(API)
        assert mints(stub)[0].json()["api_version"] == "2027-01-01"

    def test_no_authorization_from_session_auth_or_netrc(self, stub, make_client, tmp_path, monkeypatch):
        netrc = tmp_path / "netrc"
        netrc.write_text("machine 127.0.0.1 login user password secret-netrc\n")
        monkeypatch.setenv("NETRC", str(netrc))
        session = requests.Session()
        session.auth = ("user", "secret-session")
        stub.on("POST", "/token", token_reply())

        make_client(session=session)._tokens.token(API)

        assert "Authorization" not in mints(stub)[0].headers

    def test_token_from_fixture(self, stub, make_client):
        stub.on("POST", "/token", Reply(200, fixture_bytes("token/create.json")))
        token = make_client()._tokens.token(API)
        assert token.access_token == "test-access-token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 900
        assert token.aud == (API,)
        assert token.scope == "full"
        assert token.api_version == "2026-10-22"
        assert token.minted_at.tzinfo is not None


class TestCaching:
    def test_token_reused(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        client = make_client()
        assert client._tokens.token(API) == client._tokens.token(API)
        assert len(mints(stub)) == 1

    def test_one_token_per_audience(self, stub, make_client):
        stub.on("POST", "/token", lambda r: token_reply(access_token="tok-" + r.json()["aud"][0],
                                                         aud=r.json()["aud"]))
        client = make_client()
        assert client._tokens.token(API).access_token == "tok-" + API
        assert client._tokens.token(SMS).access_token == "tok-" + SMS
        assert [h.json()["aud"] for h in mints(stub)] == [[API], [SMS]]

    def test_shared_through_store(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        store = MemoryTokenStore()
        make_client(token_store=store)._tokens.token(API)
        make_client(token_store=store)._tokens.token(API)
        assert len(mints(stub)) == 1

    def test_default_store_is_shared_by_the_process(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        make_client(token_store=None)._tokens.token(API)
        make_client(token_store=None)._tokens.token(API)
        assert len(mints(stub)) == 1

    def test_cached_for_granted_lifetime(self, stub, make_client):
        stub.on("POST", "/token", token_reply(expires_in=123))
        store = DictStore()
        client = make_client(token_store=store)
        client._tokens.token(API)
        assert store.ttls == {client._tokens.cache_key(API): 123}

    def test_cache_key_vector(self):
        def key(api_key="key-1", **kwargs):
            options = {"auth_url": "https://auth.example.com", "token_store": MemoryTokenStore()}
            options.update(kwargs)
            return DidwwClient(api_key, **options)._tokens.cache_key

        base = key()(API)
        assert base == "didww:token:v1:2e1c5435f0e67f91d34497fabf69840a945923a47982fad172c353b3f26be539"
        assert "key-1" not in base
        assert key(auth_url="https://auth.example.com/")(API) == base
        assert key()(SMS) != base
        assert key(api_version="2099-01-01")(API) != base
        assert key(scope=Scope.READ)(API) != base
        assert key(auth_url="https://auth-sandbox.example.com")(API) != base
        assert key(api_key="key-2")(API) != base

    def test_flight_rereads_store_before_minting(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stored = AccessToken("stored-token", aud=(API,), expires_in=900)

        class SecondReadHits(DictStore):
            reads = 0

            def get(self, key):
                self.reads += 1
                return stored if self.reads > 1 else None

        token = make_client(token_store=SecondReadHits())._tokens.token(API)

        assert token is stored
        assert mints(stub) == []

    def test_stored_value_that_is_not_a_token_is_a_miss(self, stub, make_client):
        stub.on("POST", "/token", token_reply())

        class Garbage(DictStore):
            def get(self, key):
                return {"access_token": "x"}

        assert make_client(token_store=Garbage())._tokens.token(API).access_token == "test-access-token"


class TestSingleFlight:
    def test_concurrent_callers_share_one_mint(self, stub, make_client):
        client = make_client()
        joined = count_waiters(client, 9)

        def reply(request):
            joined.wait(10)
            return token_reply()

        stub.on("POST", "/token", reply)
        barrier = threading.Barrier(10)
        results = []

        def run():
            barrier.wait()
            results.append(client._tokens.token(API).access_token)

        threads = [threading.Thread(target=run) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)

        assert joined.is_set()
        assert results == ["test-access-token"] * 10
        assert len(mints(stub)) == 1

    def test_waiters_get_the_leaders_error(self, stub, make_client):
        client = make_client()
        joined = count_waiters(client, 4)

        def reply(request):
            joined.wait(10)
            return Reply(401, fixture_bytes("token/invalid_client.json"), {"Content-Type": "application/json"})

        stub.on("POST", "/token", reply)
        barrier = threading.Barrier(5)
        errors = []

        def run():
            barrier.wait()
            try:
                client._tokens.token(API)
            except DidwwAuthError as e:
                errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)

        assert joined.is_set()
        assert len(errors) == 5
        assert {e.kind for e in errors} == {AuthErrorKind.INVALID_CLIENT}
        assert len(mints(stub)) == 1

    def test_interrupted_leader_fails_waiters_and_next_call_mints(self, stub, make_client):
        client = make_client()
        minting = threading.Event()
        joined = count_waiters(client, 1)

        def reply(request):
            minting.set()
            joined.wait(10)
            return Reply(503, b"")

        stub.on("POST", "/token", reply, token_reply())

        def interrupt(seconds):
            raise KeyboardInterrupt

        client._tokens._sleep = interrupt
        outcome = {}

        def leader():
            try:
                client._tokens.token(API)
            except BaseException as e:
                outcome["leader"] = e

        def waiter():
            try:
                client._tokens.token(API)
            except BaseException as e:
                outcome["waiter"] = e

        first = threading.Thread(target=leader)
        first.start()
        assert minting.wait(10)
        second = threading.Thread(target=waiter)
        second.start()
        first.join(10)
        second.join(10)

        assert isinstance(outcome["leader"], KeyboardInterrupt)
        assert isinstance(outcome["waiter"], DidwwAuthError)
        assert outcome["waiter"].kind is AuthErrorKind.CONNECTION_ERROR
        assert auth._FLIGHTS == {}
        assert client._tokens.token(API).access_token == "test-access-token"

    def test_waiter_gives_up_when_the_leader_does_not_finish(self, stub, make_client, monkeypatch):
        monkeypatch.setattr(auth, "_FLIGHT_WAIT_TIMEOUT", 0.2)
        client = make_client()
        minting = threading.Event()
        release = threading.Event()

        def reply(request):
            minting.set()
            release.wait(5)
            return token_reply()

        stub.on("POST", "/token", reply)
        leader = threading.Thread(target=client._tokens.token, args=(API,))
        leader.start()
        try:
            assert minting.wait(5)
            error = capture(lambda: client._tokens.token(API))
        finally:
            release.set()
            leader.join(10)

        assert isinstance(error, DidwwAuthError)
        assert error.kind is AuthErrorKind.CONNECTION_ERROR
        assert str(error) == "Token service: the token request did not finish in time"
        assert len(mints(stub)) == 1


def count_waiters(client, n):
    """An event set once ``n`` callers wait on a flight of ``client``."""
    joined = threading.Event()
    lock = threading.Lock()
    waiting = [0]
    wait = client._tokens._await

    def counting(flight):
        with lock:
            waiting[0] += 1
            if waiting[0] >= n:
                joined.set()
        return wait(flight)

    client._tokens._await = counting
    return joined


class TestStoreContext:
    def test_store_sees_the_callers_contextvars(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        tenant = contextvars.ContextVar("tenant")

        class TenantStore(DictStore):
            def get(self, key):
                return super().get(tenant.get() + key)

            def set(self, key, token, ttl):
                super().set(tenant.get() + key, token, ttl)

        store = TenantStore()
        client = make_client(token_store=store)
        tenant.set("acme:")
        client._tokens.token(API)
        client._tokens.token(API)

        assert len(mints(stub)) == 1
        assert [k.startswith("acme:") for k in store.data] == [True]


class TestStoreFailures:
    def test_failing_store_is_logged_and_skipped(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply())

        class Broken(TokenStore):
            def get(self, key):
                raise RuntimeError("store down")

            def set(self, key, token, ttl):
                raise RuntimeError("store down")

            def delete(self, key):
                raise RuntimeError("store down")

        client = make_client(token_store=Broken())
        assert client._tokens.token(API).access_token == "test-access-token"
        client._tokens.invalidate(API, "test-access-token")

        messages = [r.getMessage() for r in caplog.records]
        assert "DIDWW token store read failed" in messages
        assert "DIDWW token store write failed" in messages
        assert all("test-access-token" not in m for m in messages)

    def test_store_returning_a_dict_is_logged_and_a_miss(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply())

        class ToDict(DictStore):
            def get(self, key):
                token = self.data.get(key)
                return token.to_dict() if token else None

        store = ToDict()
        client = make_client(token_store=store)
        client._tokens.token(API)
        client._tokens.token(API)
        client._tokens.invalidate(API, "test-access-token")

        assert len(mints(stub)) == 2
        assert client._tokens.cache_key(API) in store.data
        failures = [r for r in caplog.records if r.getMessage() == "DIDWW token store read failed"]
        assert len(failures) == 3
        assert all(type(r.exc_info[1]) is TypeError for r in failures)
        assert all(str(r.exc_info[1]) == "get returned dict, not an AccessToken" for r in failures)
        assert "test-access-token" not in caplog.text

    def test_store_returning_an_invalid_access_token_is_logged_and_a_miss(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply())

        class Invalid(DictStore):
            def get(self, key):
                return AccessToken("bad token", aud=(API,))

        assert make_client(token_store=Invalid())._tokens.token(API).access_token == "test-access-token"
        failures = [r for r in caplog.records if r.getMessage() == "DIDWW token store read failed"]
        assert failures
        assert all(type(r.exc_info[1]) is ValueError for r in failures)
        assert "bad token" not in caplog.text

    def test_failing_delete_is_logged(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")

        class NoDelete(DictStore):
            def delete(self, key):
                raise RuntimeError("store down")

        store = NoDelete()
        client = make_client(token_store=store)
        store.data[client._tokens.cache_key(API)] = AccessToken("old-token", aud=(API,))
        client._tokens.invalidate(API, "old-token")
        assert "DIDWW token store delete failed" in [r.getMessage() for r in caplog.records]

    def test_stalled_store_is_bounded(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply())
        release = threading.Event()

        class Stalled(DictStore):
            def get(self, key):
                release.wait(30)

            def set(self, key, token, ttl):
                release.wait(30)

        client = make_client(token_store=Stalled())
        client._tokens._store_timeout = 0.2
        try:
            started = time.monotonic()
            assert client._tokens.token(API).access_token == "test-access-token"
            assert time.monotonic() - started < 5
        finally:
            release.set()
        messages = [r.getMessage() for r in caplog.records]
        assert "DIDWW token store read failed" in messages
        assert "DIDWW token store write failed" in messages

    def test_write_skipped_when_store_lock_is_busy(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply())
        store = MemoryTokenStore()
        client = make_client(token_store=store)
        client._tokens._store_timeout = 0.1
        lock = client._tokens._key_lock((id(store), client._tokens.cache_key(API)))
        lock.acquire()
        try:
            assert client._tokens.token(API).access_token == "test-access-token"
        finally:
            lock.release()
        assert "DIDWW token store write skipped" in [r.getMessage() for r in caplog.records]
        assert store.get(client._tokens.cache_key(API)) is None


class TestInvalidate:
    def test_evicts_the_refused_token(self, stub, make_client):
        store = MemoryTokenStore()
        client = make_client(token_store=store)
        key = client._tokens.cache_key(API)
        store.set(key, AccessToken("refused-token", aud=(API,)), 0)
        client._tokens.invalidate(API, "refused-token")
        assert store.get(key) is None

    def test_keeps_a_token_minted_by_another_caller(self, stub, make_client):
        store = MemoryTokenStore()
        client = make_client(token_store=store)
        key = client._tokens.cache_key(API)
        store.set(key, AccessToken("newer-token", aud=(API,)), 0)
        client._tokens.invalidate(API, "older-token")
        assert store.get(key).access_token == "newer-token"

    @pytest.mark.parametrize("failing_delete", [False, True])
    def test_refused_token_kept_by_store_is_not_reused(self, stub, make_client, failing_delete):
        stub.on("POST", "/token", token_reply(access_token="new-token"))

        class Keeping(DictStore):
            def delete(self, key):
                if failing_delete:
                    raise RuntimeError("cannot delete")

        store = Keeping()
        client = make_client(token_store=store)
        key = client._tokens.cache_key(API)
        store.data[key] = AccessToken("old-token", aud=(API,))

        client._tokens.invalidate(API, "old-token")

        assert client._tokens.token(API).access_token == "new-token"
        assert len(mints(stub)) == 1
        assert client._tokens.token(API).access_token == "new-token"
        assert len(mints(stub)) == 1


class TestErrorStatuses:
    def test_invalid_request(self, stub, make_client):
        stub.on("POST", "/token", token_error(400, "invalid_scope.json"))
        e = capture(lambda: make_client(scope="full")._tokens.token(API))
        assert e.kind is AuthErrorKind.INVALID_REQUEST
        assert (e.status_code, e.error) == (400, "invalid_scope")
        assert str(e) == "Token service: invalid_scope: scope is not a known scope"
        assert len(mints(stub)) == 1

    def test_invalid_client_not_retried(self, stub, make_client):
        stub.on("POST", "/token", token_error(401, "invalid_client.json"))
        client = make_client()
        sleeps = record_sleeps(client)
        e = capture(lambda: client._tokens.token(API))
        assert e.kind is AuthErrorKind.INVALID_CLIENT
        assert (e.status_code, e.error, e.error_description) == \
            (401, "invalid_client", "Client authentication failed.")
        assert len(mints(stub)) == 1
        assert sleeps == []

    def test_unexpected_status_is_not_followed(self, stub, make_client):
        stub.on("POST", "/token", Reply(307, b"", {"Location": stub.url + "/elsewhere"}))
        e = capture(lambda: make_client()._tokens.token(API))
        assert e.kind is AuthErrorKind.UNEXPECTED_STATUS
        assert e.status_code == 307
        assert "redirect" in str(e)
        assert stub.hits(path="/elsewhere") == []

    def test_redirect_with_unparsable_location_is_unexpected(self, stub, make_client):
        stub.on("POST", "/token", Reply(302, b"", {"Location": "http://[::1/x"}))
        e = capture(lambda: make_client()._tokens.token(API))
        assert e.kind is AuthErrorKind.UNEXPECTED_STATUS
        assert e.status_code == 302
        assert "redirect" in str(e)

    def test_other_status_is_unexpected(self, stub, make_client):
        stub.on("POST", "/token", Reply(404, b"not here"))
        e = capture(lambda: make_client()._tokens.token(API))
        assert e.kind is AuthErrorKind.UNEXPECTED_STATUS
        assert str(e) == "Token service responded with status 404"

    def test_later_call_mints_again_after_failure(self, stub, make_client):
        stub.on("POST", "/token", token_error(401, "invalid_client.json"), token_reply())
        client = make_client()
        capture(lambda: client._tokens.token(API))
        assert client._tokens.token(API).access_token == "test-access-token"


class TestRateLimit:
    def test_rate_limited_opens_a_window(self, stub, make_client):
        stub.on("POST", "/token", token_error(429, "rate_limit_exceeded.json", {"Retry-After": "7"}),
                token_reply())
        client = make_client()
        client._tokens._random = lambda: 0.0

        first = capture(lambda: client._tokens.token(API))
        second = capture(lambda: client._tokens.token(SMS))

        assert first.kind is AuthErrorKind.RATE_LIMITED
        assert (first.status_code, first.error, first.retry_after) == (429, "rate_limit_exceeded", 7)
        assert second.kind is AuthErrorKind.RATE_LIMITED
        assert second.retry_after == 7
        assert len(mints(stub)) == 1

    @pytest.mark.parametrize("header, seconds", [
        ("0", 1), (None, 1), ("Wed, 21 Oct 2026 07:28:00 GMT", 1), (" 3 ", 3), ("-5", 1), ("1.5", 1),
    ])
    def test_retry_after_values(self, stub, make_client, header, seconds):
        headers = {"Retry-After": header} if header is not None else {}
        stub.on("POST", "/token", token_error(429, "rate_limit_exceeded.json", headers))
        e = capture(lambda: make_client()._tokens.token(API))
        assert e.retry_after == seconds

    def test_window_rounds_up_and_ends(self, stub, make_client):
        stub.on("POST", "/token", token_error(429, "rate_limit_exceeded.json", {"Retry-After": "10"}),
                token_reply())
        client = make_client()
        now = [1000.0]
        client._tokens._monotonic = lambda: now[0]
        client._tokens._random = lambda: 0.5

        capture(lambda: client._tokens.token(API))
        now[0] += 0.5
        assert capture(lambda: client._tokens.token(API)).retry_after == 11
        now[0] += 10.5
        assert client._tokens.token(API).access_token == "test-access-token"
        assert len(mints(stub)) == 2

    def test_window_covers_other_clients_of_the_same_key_only(self, stub, make_client):
        stub.on("POST", "/token", token_error(429, "rate_limit_exceeded.json", {"Retry-After": "30"}),
                token_reply())
        capture(lambda: make_client()._tokens.token(API))

        e = capture(lambda: make_client(scope=Scope.READ)._tokens.token(API))
        assert e.kind is AuthErrorKind.RATE_LIMITED
        assert make_client(api_key="other-key")._tokens.token(API).access_token == "test-access-token"
        assert len(mints(stub)) == 2

    def test_retry_stops_inside_a_window(self, stub, make_client):
        stub.on("POST", "/token", token_error(503, "server_error.json"), token_reply())
        client = make_client()
        provider = client._tokens

        def open_window(seconds):
            auth._RATE_LIMITS[provider._rate_limit_key()] = provider._monotonic() + 30

        provider._sleep = open_window
        e = capture(lambda: provider.token(API))
        assert e.kind is AuthErrorKind.RATE_LIMITED
        assert len(mints(stub)) == 1


class TestRetries:
    def test_server_error_retried_with_backoff(self, stub, make_client):
        stub.on("POST", "/token", Reply(503, b""), Reply(503, b""), token_reply())
        client = make_client()
        sleeps = record_sleeps(client, random=1.0)
        assert client._tokens.token(API).access_token == "test-access-token"
        assert len(mints(stub)) == 3
        assert sleeps == [1.0, 2.0]

    def test_backoff_is_full_jitter_with_a_cap(self, make_client):
        provider = make_client()._tokens
        provider._random = lambda: 1.0
        assert [provider.backoff(n) for n in (1, 2, 3, 4, 5, 30)] == [1.0, 2.0, 4.0, 8.0, 8.0, 8.0]
        provider._random = lambda: 0.25
        assert provider.backoff(3) == 1.0

    def test_spread_retry_after(self):
        assert spread(1, lambda: 0.0) == 1
        assert spread(1, lambda: 1.0) == 2
        assert spread(30, lambda: 0.0) == 30
        assert spread(30, lambda: 1.0) == 36
        assert spread(30, lambda: 0.5) == 33

    def test_jitter_uses_a_system_random(self):
        import random

        assert isinstance(auth._RANDOM, random.SystemRandom)

    def test_server_error_exhausted(self, stub, make_client):
        stub.on("POST", "/token", token_error(500, "server_error.json"))
        client = make_client()
        sleeps = record_sleeps(client)
        e = capture(lambda: client._tokens.token(API))
        assert e.kind is AuthErrorKind.SERVER_ERROR
        assert (e.status_code, e.error) == (500, "server_error")
        assert len(mints(stub)) == auth.MAX_MINT_ATTEMPTS == 4
        assert len(sleeps) == 3

    def test_server_error_without_json_body(self, stub, make_client):
        stub.on("POST", "/token", Reply(502, b"<html>bad gateway</html>"))
        e = capture(lambda: make_client()._tokens.token(API))
        assert e.kind is AuthErrorKind.SERVER_ERROR
        assert e.error is None
        assert str(e) == "Token service responded with status 502"

    def test_timeout_retried(self, stub, make_client):
        stub.on("POST", "/token", Reply(200, b"{}", delay=0.6), token_reply())
        client = make_client()
        client._tokens._mint_timeout = 0.2
        assert client._tokens.token(API).access_token == "test-access-token"
        assert len(mints(stub)) == 2

    def test_timeout_exhausts_attempts(self, stub, make_client):
        stub.on("POST", "/token", Reply(200, b"{}", delay=0.6))
        client = make_client()
        client._tokens._mint_timeout = 0.2
        e = capture(lambda: client._tokens.token(API))
        assert e.kind is AuthErrorKind.CONNECTION_ERROR
        assert e.status_code is None
        assert len(mints(stub)) == 4

    def test_connection_error_retried_then_raised_without_secrets(self, make_client):
        url = f"http://127.0.0.1:{free_port()}"
        client = make_client(api_key="secret-api-key-1", auth_url=url)
        sleeps = record_sleeps(client)
        e = capture(lambda: client._tokens.token(API))
        assert e.kind is AuthErrorKind.CONNECTION_ERROR
        assert len(sleeps) == 3
        assert isinstance(e.__cause__, requests.exceptions.ConnectionError)
        assert e.__cause__.request is None
        for text in (str(e), repr(e), str(e.__cause__), repr(e.__cause__)):
            assert "secret-api-key-1" not in text


class TestTls:
    def _client(self, make_client, server):
        client = make_client(auth_url=f"https://127.0.0.1:{server.port}")
        return client, record_sleeps(client)

    def test_certificate_error_not_retried(self, make_client):
        context = self_signed_context()

        def handshake(conn, request):
            context.wrap_socket(conn, server_side=True).recv(1)

        server = RawServer(handshake, read_request=False)
        try:
            client, sleeps = self._client(make_client, server)
            e = capture(lambda: client._tokens.token(API))
        finally:
            server.close()
        assert e.kind is AuthErrorKind.CONNECTION_ERROR
        assert isinstance(e.__cause__, requests.exceptions.SSLError)
        assert server.accepts == 1
        assert sleeps == []

    def test_alert_not_retried(self, make_client):
        def alert(conn, request):
            conn.recv(4096)
            conn.sendall(bytes.fromhex("15030300020228"))

        server = RawServer(alert, read_request=False)
        try:
            client, sleeps = self._client(make_client, server)
            e = capture(lambda: client._tokens.token(API))
        finally:
            server.close()
        assert e.kind is AuthErrorKind.CONNECTION_ERROR
        assert server.accepts == 1
        assert sleeps == []

    def test_connection_closed_during_handshake_is_retried(self, make_client):
        server = RawServer(lambda conn, request: conn.recv(4096), read_request=False)
        try:
            client, sleeps = self._client(make_client, server)
            e = capture(lambda: client._tokens.token(API))
        finally:
            server.close()
        assert e.kind is AuthErrorKind.CONNECTION_ERROR
        assert server.accepts == 4
        assert len(sleeps) == 3

    def test_tls_error_found_behind_a_proxy_error(self):
        alert = ssl.SSLError(1, "[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] handshake failure")
        wrapped = requests.exceptions.ProxyError(urllib3.exceptions.MaxRetryError(None, "/token", alert))
        assert is_tls_error(wrapped)
        reset = requests.exceptions.ConnectionError(
            urllib3.exceptions.ProtocolError("aborted", ConnectionResetError(54, "reset")))
        assert not is_tls_error(reset)
        eof = requests.exceptions.SSLError(urllib3.exceptions.MaxRetryError(
            None, "/token", urllib3.exceptions.SSLError(ssl.SSLEOFError(8, "EOF"))))
        assert not is_tls_error(eof)

    @pytest.mark.parametrize("reason, message", [
        ("UNEXPECTED_EOF_WHILE_READING", "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol"),
        (None, "[SSL] unexpected eof while reading (_ssl.c:1129)"),
    ])
    def test_plain_ssl_error_for_an_eof_during_the_handshake_is_a_dropped_connection(self, reason, message):
        err = ssl.SSLError(1, message)
        err.reason = reason
        wrapped = requests.exceptions.SSLError(urllib3.exceptions.MaxRetryError(
            None, "/token", urllib3.exceptions.SSLError(err)))
        assert not is_tls_error(wrapped)


class TestGrant:
    @pytest.mark.parametrize("reply", [
        token_reply(aud=("api-vin.didww.com",)),
        token_reply(aud=()),
        token_reply(access_token=""),
        token_reply(access_token="has space"),
        token_reply(access_token="line\nbreak"),
        token_reply(access_token="café"),
        Reply(200, b"not json"),
        Reply(200, b"[1, 2]"),
    ])
    def test_invalid_grant_is_not_cached(self, stub, make_client, reply):
        stub.on("POST", "/token", reply)
        client = make_client()
        for _ in range(2):
            e = capture(lambda: client._tokens.token(API))
            assert e.kind is AuthErrorKind.INVALID_GRANT
            assert e.status_code == 200
        assert len(mints(stub)) == 2

    def test_audience_mismatch_message(self, stub, make_client):
        stub.on("POST", "/token", token_reply(aud=("api-vin.didww.com",)))
        e = capture(lambda: make_client()._tokens.token(API))
        assert str(e) == "Token service: granted audience ['api-vin.didww.com'], requested api.didww.com"

    def test_unparsable_200_never_exposes_the_token(self, stub, make_client):
        stub.on("POST", "/token", Reply(200, b'{"access_token":"secret-tok-999","aud":'))
        e = capture(lambda: make_client()._tokens.token(API))
        assert e.kind is AuthErrorKind.INVALID_GRANT
        assert "secret-tok-999" not in str(e) + repr(e)
        assert e.__cause__ is None
        assert e.__context__ is None

    def test_cut_200_is_retried_and_never_exposes_the_token(self, make_client):
        body = b'{"access_token":"secret-tok-999","token_type":"Bearer","expires_in":900,"aud":["api.didww.com"]}'

        def cut(conn, request):
            conn.sendall(http_response(200, body[:30], [("Content-Type", "application/json")],
                                       content_length=len(body)))

        server = RawServer(cut)
        try:
            client = make_client(auth_url=server.url)
            sleeps = record_sleeps(client)
            e = capture(lambda: client._tokens.token(API))
        finally:
            server.close()
        assert e.kind is AuthErrorKind.CONNECTION_ERROR
        assert e.status_code == 200
        assert server.accepts == 4
        assert len(sleeps) == 3
        assert "secret-tok" not in str(e) + repr(e)
        assert e.__cause__ is None
        assert e.__context__ is None


class TestLogging:
    def _messages(self, caplog):
        return [r.getMessage() for r in caplog.records]

    def test_scope_mismatch_warning(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply(scope="full"))
        make_client(scope=Scope.READ)._tokens.token(API)
        assert "DIDWW token scope mismatch: requested read, granted full" in self._messages(caplog)

    def test_api_version_mismatch_warning(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply(api_version="2026-10-22"))
        make_client(api_version="2027-01-01")._tokens.token(API)
        assert "DIDWW token api_version mismatch: requested 2027-01-01, granted 2026-10-22" \
            in self._messages(caplog)

    def test_no_warning_when_grant_matches(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply(scope="full"))
        make_client(scope=Scope.FULL)._tokens.token(API)
        assert self._messages(caplog) == []

    def test_no_scope_warning_without_requested_scope(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING, logger="didww")
        stub.on("POST", "/token", token_reply(scope="read"))
        make_client()._tokens.token(API)
        assert self._messages(caplog) == []

    def test_minted_debug_log_without_secrets(self, stub, make_client, caplog):
        caplog.set_level(logging.DEBUG, logger="didww")
        stub.on("POST", "/token", token_reply())
        make_client(api_key="secret-api-key-1")._tokens.token(API)
        messages = self._messages(caplog)
        assert any(m.startswith("DIDWW token minted: aud ['api.didww.com'], scope full, "
                                "api_version 2026-10-22, expires_in 900, duration_ms ") for m in messages)
        assert all("test-access-token" not in m and "secret-api-key-1" not in m for m in messages)

    def test_custom_logger_receives_warnings(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING)
        stub.on("POST", "/token", token_reply(scope="full"))
        make_client(scope=Scope.READ, logger=logging.getLogger("my.app"))._tokens.token(API)
        assert [r.name for r in caplog.records] == ["my.app"]

    def test_failing_logger_never_fails_the_call(self, stub, make_client):
        stub.on("POST", "/token", token_reply(scope="full"))

        class Exploding:
            def log(self, *args, **kwargs):
                raise RuntimeError("logger down")

            def isEnabledFor(self, level):
                raise RuntimeError("logger down")

        client = make_client(scope=Scope.READ, logger=Exploding())
        assert client._tokens.token(API).access_token == "test-access-token"

    def test_failing_filter_and_handler_never_fail_the_call(self, stub, make_client):
        stub.on("POST", "/token", token_reply(scope="full"))

        class ExplodingHandler(logging.Handler):
            def emit(self, record):
                raise RuntimeError("handler down")

        class ExplodingFilter(logging.Filter):
            def filter(self, record):
                raise RuntimeError("filter down")

        for name, attach in (("didww.test.handler", lambda lg: lg.addHandler(ExplodingHandler())),
                             ("didww.test.filter", lambda lg: lg.addFilter(ExplodingFilter()))):
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            attach(logger)
            try:
                client = make_client(scope=Scope.READ, logger=logger)
                assert client._tokens.token(API).access_token == "test-access-token"
            finally:
                logger.handlers.clear()
                logger.filters.clear()
            auth._reset_coordination()


class TestForkReset:
    def test_locks_and_flights_are_recreated(self):
        held = auth._REGISTRY_LOCK
        held.acquire()
        store = MemoryTokenStore()
        store._lock.acquire()
        auth._FLIGHTS[("x", "y")] = auth._Flight()
        try:
            auth._after_fork_in_child()
            assert auth._REGISTRY_LOCK is not held
            assert auth._REGISTRY_LOCK.acquire(timeout=1)
            auth._REGISTRY_LOCK.release()
            assert auth._RATE_LIMIT_LOCK.acquire(timeout=1)
            auth._RATE_LIMIT_LOCK.release()
            assert auth._FLIGHTS == {}
            assert store._lock.acquire(timeout=1)
        finally:
            held.release()

    @pytest.mark.skipif(not hasattr(os, "fork"), reason="needs os.fork")
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_forked_child_does_not_inherit_held_lock_or_flights(self):
        holding = threading.Event()
        done = threading.Event()

        def hold():
            with auth._REGISTRY_LOCK:
                auth._FLIGHTS[("x", "y")] = auth._Flight()
                holding.set()
                done.wait(10)

        helper = threading.Thread(target=hold)
        helper.start()
        try:
            assert holding.wait(10)
            pid = os.fork()
            if pid == 0:
                code = 2
                try:
                    code = 0 if auth._REGISTRY_LOCK.acquire(timeout=1) and auth._FLIGHTS == {} else 1
                finally:
                    os._exit(code)
            deadline = time.monotonic() + 10
            while True:
                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited:
                    break
                if time.monotonic() > deadline:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                    pytest.fail("the forked child hung")
                time.sleep(0.01)
        finally:
            done.set()
            helper.join(10)

        assert os.waitstatus_to_exitcode(status) == 0
