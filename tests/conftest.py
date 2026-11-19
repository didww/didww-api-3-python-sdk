import json
import os
import pytest
import vcr

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

TEST_ACCESS_TOKEN = "test-access-token"


def _json_body_matcher(r1, r2):
    if r1.body is None and r2.body is None:
        return True
    if r1.body is None or r2.body is None:
        return False
    try:
        b1 = r1.body if isinstance(r1.body, str) else r1.body.decode("utf-8")
        b2 = r2.body if isinstance(r2.body, str) else r2.body.decode("utf-8")
        return json.loads(b1) == json.loads(b2)
    except (TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return r1.body == r2.body


# Request headers are not matched: the cassettes predate bearer tokens, and the
# bearer header is covered by the local-server tests.
my_vcr = vcr.VCR(
    cassette_library_dir=FIXTURES_DIR,
    record_mode="none",
    match_on=["method", "path", "body"],
)
my_vcr.register_matcher("body", _json_body_matcher)

my_vcr_no_body = vcr.VCR(
    cassette_library_dir=FIXTURES_DIR,
    record_mode="none",
    match_on=["method", "path"],
)


@pytest.fixture(autouse=True)
def _reset_didww_coordination():
    from didww import auth

    auth._reset_coordination()
    yield
    auth._reset_coordination()


def seed_token(client, audience="api.didww.com", access_token=TEST_ACCESS_TOKEN):
    """Stores a valid token for ``audience`` in the client's store, so no mint is needed."""
    from didww.auth import AccessToken

    token = AccessToken(access_token=access_token, token_type="Bearer", expires_in=900,
                        aud=(audience,), scope="full", api_version=client.api_version)
    client.token_store.set(client._tokens.cache_key(audience), token, 0)
    return token


@pytest.fixture
def client():
    from didww.auth import MemoryTokenStore
    from didww.client import DidwwClient
    from didww.configuration import Environment

    c = DidwwClient(api_key="test-api-key", environment=Environment.SANDBOX, token_store=MemoryTokenStore())
    seed_token(c)
    return c


@pytest.fixture
def stub():
    from tests.support.http_stub import StubServer

    server = StubServer()
    yield server
    server.close()


@pytest.fixture
def make_client(stub):
    """Builds a client whose base, token and prices URLs all point at the stub server."""
    from didww.auth import MemoryTokenStore
    from didww.client import DidwwClient

    def build(**kwargs):
        options = {
            "base_url": stub.url + "/v3",
            "auth_url": stub.url,
            "voice_in_prices_url": stub.url + "/v3",
            "voice_out_prices_url": stub.url + "/v3",
            "sms_prices_url": stub.url + "/v3",
            "token_store": MemoryTokenStore(),
            "read_timeout": 2,
        }
        options.update(kwargs)
        api_key = options.pop("api_key", "test-api-key")
        c = DidwwClient(api_key, **options)
        c._tokens._sleep = lambda seconds: None
        return c

    return build
