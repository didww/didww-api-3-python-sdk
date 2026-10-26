import gzip
import json
import logging
import socket
import time
from decimal import Decimal

import pytest
import requests

from didww.auth import AccessToken, MemoryTokenStore
from didww.configuration import Scope
from didww.exceptions import AuthErrorKind, DidwwApiError, DidwwAuthError, DidwwClientError
from tests.support.http_stub import RawServer, Reply, jsonapi_reply, token_reply

API = "api.didww.com"


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


def bearer_reply(valid, ok=None):
    """Answers 401 unless the request carries ``Bearer <valid>``."""

    def reply(request):
        if request.headers.get("Authorization") == f"Bearer {valid}":
            return ok or jsonapi_reply(200, {"data": []})
        return jsonapi_reply(401, {"errors": [{"title": "Unauthorized", "status": "401"}]})

    return reply


class TestHeaders:
    def test_api_call_carries_bearer_only(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/countries", jsonapi_reply())
        make_client().get("countries", params={"page[size]": "1"})

        (hit,) = stub.hits("GET", "/v3/countries")
        assert hit.headers["Authorization"] == "Bearer test-access-token"
        assert "Api-Key" not in hit.headers
        assert "X-DIDWW-API-Version" not in hit.headers
        assert hit.headers["Accept"] == "application/vnd.api+json"
        assert "Content-Type" not in hit.headers
        assert hit.query == {"page[size]": ["1"]}

    def test_api_call_accepts_only_codings_an_error_body_can_undo(self, stub, make_client, monkeypatch):
        monkeypatch.setattr(requests.utils, "DEFAULT_ACCEPT_ENCODING", "gzip, deflate, br, zstd")
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/countries", jsonapi_reply())
        make_client().get("countries")

        (hit,) = stub.hits("GET", "/v3/countries")
        assert hit.headers["Accept-Encoding"] == "gzip, deflate"

    def test_json_body_carries_content_type(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("POST", "/v3/dids", jsonapi_reply(201, {"data": {"id": "1", "type": "dids"}}))
        make_client().post("dids", {"data": {"type": "dids", "attributes": {"capacity_limit": 2}}})

        (hit,) = stub.hits("POST", "/v3/dids")
        assert hit.headers["Content-Type"] == "application/vnd.api+json"
        assert hit.json() == {"data": {"type": "dids", "attributes": {"capacity_limit": 2}}}

    def test_public_keys_carry_no_credentials(self, stub, make_client):
        session = requests.Session()
        session.auth = ("user", "secret-session")
        stub.on("GET", "/v3/public_keys", jsonapi_reply())
        make_client(session=session).get("public_keys")

        (hit,) = stub.hits("GET", "/v3/public_keys")
        assert "Authorization" not in hit.headers
        assert "Api-Key" not in hit.headers
        assert stub.hits("POST", "/token") == []

    def test_paths_that_only_contain_public_keys_are_authenticated(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/not_public_keys", jsonapi_reply())
        stub.on("GET", "/v3/public_keys_extra", jsonapi_reply())
        client = make_client()
        client.get("not_public_keys")
        client.get("public_keys_extra")
        assert all(h.headers.get("Authorization") == "Bearer test-access-token"
                   for h in stub.hits("GET"))

    def test_session_auth_does_not_replace_bearer(self, stub, make_client):
        session = requests.Session()
        session.auth = ("user", "secret-session")
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/countries", jsonapi_reply())
        make_client(session=session).get("countries")
        assert stub.hits("GET", "/v3/countries")[0].headers["Authorization"] == "Bearer test-access-token"

    def test_netrc_does_not_replace_bearer(self, stub, make_client, tmp_path, monkeypatch):
        netrc = tmp_path / "netrc"
        netrc.write_text("machine 127.0.0.1 login user password secret-netrc\n")
        monkeypatch.setenv("NETRC", str(netrc))
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/countries", jsonapi_reply())
        stub.on("GET", "/v3/public_keys", jsonapi_reply())
        client = make_client()
        client.get("countries")
        client.get("public_keys")
        assert stub.hits("GET", "/v3/countries")[0].headers["Authorization"] == "Bearer test-access-token"
        assert "Authorization" not in stub.hits("GET", "/v3/public_keys")[0].headers
        assert "Authorization" not in stub.hits("POST", "/token")[0].headers

    def test_audience_per_request(self, stub, make_client):
        stub.on("POST", "/token", lambda r: token_reply(access_token="tok-" + r.json()["aud"][0],
                                                         aud=r.json()["aud"]))
        stub.on("GET", "/v3/lookup/prices", jsonapi_reply())
        make_client().get("lookup/prices", audience="api-vin.didww.com")
        assert stub.hits("POST", "/token")[0].json()["aud"] == ["api-vin.didww.com"]
        assert stub.hits("GET")[0].headers["Authorization"] == "Bearer tok-api-vin.didww.com"

    def test_client_options_reach_the_mint(self, stub, make_client, caplog):
        caplog.set_level(logging.WARNING)
        stub.on("POST", "/token", token_reply(scope="full", api_version="2026-10-22"))
        stub.on("GET", "/v3/balance", jsonapi_reply())
        make_client(scope=Scope.READ, api_version="2027-01-01", logger=logging.getLogger("my.app")).get("balance")

        assert stub.hits("POST", "/token")[0].json() == \
            {"aud": [API], "api_version": "2027-01-01", "scope": "read"}
        assert {r.name for r in caplog.records} == {"my.app"}
        assert len(caplog.records) == 2


class TestUnauthorized:
    def test_401_mints_again_and_retries_once(self, stub, make_client):
        stub.on("POST", "/token", token_reply("old-token"), token_reply("new-token"))
        stub.on("GET", "/v3/balance", bearer_reply("new-token"))
        assert make_client().get("balance") == {"data": []}
        assert [h.headers["Authorization"] for h in stub.hits("GET", "/v3/balance")] == \
            ["Bearer old-token", "Bearer new-token"]
        assert len(stub.hits("POST", "/token")) == 2

    def test_patch_body_is_replayed(self, stub, make_client):
        stub.on("POST", "/token", token_reply("old-token"), token_reply("new-token"))
        stub.on("PATCH", "/v3/dids/1", bearer_reply("new-token", jsonapi_reply(200, {"data": {"id": "1"}})))
        doc = {"data": {"id": "1", "type": "dids", "attributes": {"description": "x", "price": Decimal("1.10")}}}
        make_client().patch("dids/1", doc)
        first, second = stub.hits("PATCH", "/v3/dids/1")
        assert first.body == second.body
        assert b'"price":1.10' in second.body

    def test_second_401_evicts_the_replacement(self, stub, make_client):
        stub.on("POST", "/token", token_reply("old-token"), token_reply("new-token"))
        stub.on("GET", "/v3/balance", bearer_reply("never"))
        store = MemoryTokenStore()
        client = make_client(token_store=store)
        e = capture(lambda: client.get("balance"))
        assert isinstance(e, DidwwApiError)
        assert e.status_code == 401
        assert len(stub.hits("POST", "/token")) == 2
        assert store.get(client._tokens.cache_key(API)) is None

    def test_403_is_not_retried(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/balance", jsonapi_reply(403, {"errors": [{"title": "Forbidden",
                                                                      "detail": "insufficient_scope"}]}))
        e = capture(lambda: make_client().get("balance"))
        assert isinstance(e, DidwwApiError)
        assert e.status_code == 403
        assert str(e) == "insufficient_scope"
        assert len(stub.hits("GET", "/v3/balance")) == 1
        assert len(stub.hits("POST", "/token")) == 1

    def test_keeps_a_token_minted_by_another_caller(self, stub, make_client):
        store = MemoryTokenStore()
        client = make_client(token_store=store)
        key = client._tokens.cache_key(API)
        store.set(key, AccessToken("old-token", aud=(API,)), 0)

        def reply(request):
            # Another caller replaces the token while this request is refused.
            store.set(key, AccessToken("newer-token", aud=(API,)), 0)
            return bearer_reply("newer-token")(request)

        stub.on("GET", "/v3/balance", reply)
        assert client.get("balance") == {"data": []}
        assert stub.hits("POST", "/token") == []
        assert store.get(key).access_token == "newer-token"

    def test_auth_errors_surface_unchanged(self, stub, make_client):
        stub.on("POST", "/token", Reply(401, {"error": "invalid_client"}))
        e = capture(lambda: make_client().balance().find())
        assert isinstance(e, DidwwAuthError)
        assert e.kind is AuthErrorKind.INVALID_CLIENT
        assert stub.hits("GET") == []


class TestResponses:
    def test_floats_become_decimals(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/balance", Reply(200, b'{"data":{"attributes":{"rate":0.0045}}}'))
        rate = make_client().get("balance")["data"]["attributes"]["rate"]
        assert isinstance(rate, Decimal)
        assert str(rate) == "0.0045"

    def test_empty_body_and_204_give_none(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("DELETE", "/v3/dids/1", Reply(204))
        stub.on("GET", "/v3/empty", Reply(200, b""))
        client = make_client()
        assert client.delete("dids/1") is None
        assert client.get("empty") is None

    def test_invalid_json_success_body(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/balance", Reply(200, b'{"secret": "credential", '))
        e = capture(lambda: make_client().get("balance"))
        assert isinstance(e, DidwwClientError)
        assert "credential" not in str(e)
        assert e.__context__ is None

    def test_redirect_is_an_error_and_not_followed(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/dids", Reply(302, b"", {"Location": stub.url + "/elsewhere"}))
        e = capture(lambda: make_client().get("dids"))
        assert isinstance(e, DidwwApiError)
        assert e.status_code == 302
        assert e.errors == [{"title": "HTTP 302"}]
        assert stub.hits(path="/elsewhere") == []

    def test_redirect_with_unparsable_location(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/dids", Reply(302, b"", {"Location": "http://[::1/x"}))
        e = capture(lambda: make_client().get("dids"))
        assert isinstance(e, DidwwApiError)
        assert (e.status_code, e.errors) == (302, [{"title": "HTTP 302"}])

    def test_redirect_body_is_read_within_a_deadline(self, stub, make_client):
        def trickle(conn, request):
            conn.sendall(b"HTTP/1.1 302 Found\r\nLocation: /elsewhere\r\nContent-Length: 200\r\n\r\n{")
            for _ in range(200):
                conn.sendall(b" ")
                time.sleep(0.05)

        server = RawServer(trickle)
        stub.on("POST", "/token", token_reply())
        try:
            client = make_client(base_url=server.url + "/v3")
            client._error_body_timeout = 0.3
            started = time.monotonic()
            e = capture(lambda: client.get("dids"))
            elapsed = time.monotonic() - started
        finally:
            server.close()
        assert isinstance(e, DidwwApiError)
        assert e.status_code == 302
        assert elapsed < 3

    def test_errors_document_parsed(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/dids", jsonapi_reply(422, {"errors": [
            {"title": "is invalid", "detail": "capacity_limit - is invalid", "code": "100"}, "garbage"]}))
        e = capture(lambda: make_client().get("dids"))
        assert e.status_code == 422
        assert e.errors == [{"title": "is invalid", "detail": "capacity_limit - is invalid", "code": "100"}]

    def test_error_without_errors_document(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/dids", Reply(500, b"<html>oops</html>"))
        e = capture(lambda: make_client().get("dids"))
        assert (e.status_code, e.errors) == (500, [{"title": "HTTP 500"}])

    def test_error_body_with_a_number_out_of_range(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/dids", Reply(422, b'{"errors":[{"title":"t","meta":{"n":1e99999999999999999999}}]}'))
        e = capture(lambda: make_client().get("dids"))
        assert isinstance(e, DidwwApiError)
        assert (e.status_code, e.errors) == (422, [{"title": "HTTP 422"}])

    def test_gzip_error_body_is_decoded(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        body = gzip.compress(json.dumps({"errors": [{"title": "t", "detail": "zipped"}]}).encode())
        stub.on("GET", "/v3/dids", Reply(404, body, {"Content-Encoding": "gzip"}))
        e = capture(lambda: make_client().get("dids"))
        assert e.errors == [{"title": "t", "detail": "zipped"}]

    def test_error_body_is_limited_in_size(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        body = json.dumps({"errors": [{"title": "t", "detail": "real"}], "pad": "x" * (2 << 20)}).encode()
        stub.on("GET", "/v3/dids", Reply(404, body))
        e = capture(lambda: make_client().get("dids"))
        # Cut at 1 MiB, the document no longer parses and the status decides.
        assert (e.status_code, e.errors) == (404, [{"title": "HTTP 404"}])

    def test_error_body_is_read_within_a_deadline(self, stub, make_client):
        def trickle(conn, request):
            conn.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 200\r\n\r\n{")
            for _ in range(200):
                conn.sendall(b" ")
                time.sleep(0.05)

        server = RawServer(trickle)
        stub.on("POST", "/token", token_reply())
        try:
            client = make_client(base_url=server.url + "/v3")
            client._error_body_timeout = 0.3
            started = time.monotonic()
            e = capture(lambda: client.get("dids"))
            elapsed = time.monotonic() - started
        finally:
            server.close()
        assert isinstance(e, DidwwApiError)
        assert e.status_code == 404
        assert elapsed < 3

    def test_cookies_are_never_sent_back(self, stub, make_client):
        stub.on("POST", "/token", Reply(200, token_reply().body,
                                        {"Content-Type": "application/json", "Set-Cookie": "a=1; Path=/"}))
        stub.on("GET", "/v3/countries", Reply(200, b'{"data":[]}', {"Set-Cookie": "sid=abc; Path=/"}))
        client = make_client()
        client.get("countries")
        client.get("countries")
        assert all("Cookie" not in h.headers for h in stub.requests)


class TestTransportErrors:
    def test_connection_failure_is_wrapped(self, make_client):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        client = make_client(base_url=f"http://127.0.0.1:{port}/v3")
        client.token_store.set(client._tokens.cache_key(API),
                               AccessToken("secret-access-token", aud=(API,)), 0)
        e = capture(lambda: client.get("dids"))
        assert isinstance(e, DidwwClientError)
        assert str(e) == "Request GET dids failed: ConnectionError"
        assert isinstance(e.__cause__, requests.exceptions.ConnectionError)
        assert e.__cause__.request is None
        assert "secret-access-token" not in repr(e) + repr(e.__cause__)

    def test_read_timeout_is_wrapped(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", "/v3/dids", Reply(200, b"{}", delay=1.0))
        e = capture(lambda: make_client(read_timeout=0.2).get("dids"))
        assert isinstance(e, DidwwClientError)
        assert isinstance(e.__cause__, requests.exceptions.ReadTimeout)


@pytest.mark.parametrize("method", ["get", "delete"])
def test_bodyless_methods_send_no_content_type(stub, make_client, method):
    stub.on("POST", "/token", token_reply())
    stub.on(method.upper(), "/v3/dids/1", Reply(204))
    getattr(make_client(), method)("dids/1")
    assert "Content-Type" not in stub.hits(method.upper(), "/v3/dids/1")[0].headers
