import importlib.util
import logging
import sys
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from didww.auth import MemoryTokenStore
from didww.client import DidwwClient, _SDK_VERSION
from didww.configuration import DEFAULT_API_VERSION, Environment, Scope
from didww.exceptions import DidwwClientError
from didww.resources.address_requirement import AddressRequirement
from didww.resources.base import RelationField
from didww.resources.did_group import DidGroup
from didww.resources.emergency_calling_service import EmergencyCallingService
from didww.resources.emergency_requirement import EmergencyRequirement
from didww.resources.voice_in_trunk import VoiceInTrunk
from tests.conftest import seed_token


def test_sandbox_url():
    client = DidwwClient(api_key="test", environment=Environment.SANDBOX)
    assert client.base_url == "https://sandbox-api.didww.com/v3"


def test_production_url():
    client = DidwwClient(api_key="test", environment=Environment.PRODUCTION)
    assert client.base_url == "https://api.didww.com/v3"


def test_custom_base_url():
    client = DidwwClient(api_key="test", base_url="http://localhost:3000/v3")
    assert client.base_url == "http://localhost:3000/v3"


def test_custom_base_url_trailing_slash_trimmed():
    client = DidwwClient(api_key="test", base_url="http://localhost:3000/v3/")
    assert client.base_url == "http://localhost:3000/v3"


def test_empty_base_url_means_environment_url():
    client = DidwwClient(api_key="test", base_url="", environment=Environment.PRODUCTION)
    assert client.base_url == "https://api.didww.com/v3"


@pytest.mark.parametrize("environment, auth_url, voice_in, voice_out, sms", [
    (Environment.SANDBOX, "https://auth-sandbox.didww.com", "https://api-vin-sandbox.didww.com/v3",
     "https://api-vout-sandbox.didww.com/v3", "https://api-sms-sandbox.didww.com/v3"),
    (Environment.PRODUCTION, "https://auth.didww.com", "https://api-vin.didww.com/v3",
     "https://api-vout.didww.com/v3", "https://api-sms.didww.com/v3"),
])
def test_environment_endpoints(environment, auth_url, voice_in, voice_out, sms):
    client = DidwwClient(api_key="test", environment=environment)
    assert (client.auth_url, client.voice_in_prices_url, client.voice_out_prices_url, client.sms_prices_url) == \
        (auth_url, voice_in, voice_out, sms)
    assert (environment.auth_url, environment.voice_in_prices_url, environment.voice_out_prices_url,
            environment.sms_prices_url) == (auth_url, voice_in, voice_out, sms)


def test_environment_values_are_unchanged():
    assert Environment("https://api.didww.com/v3") is Environment.PRODUCTION
    assert Environment("https://sandbox-api.didww.com/v3") is Environment.SANDBOX


def test_custom_service_urls():
    client = DidwwClient(api_key="test", auth_url="https://auth.example.com/",
                         voice_in_prices_url="https://vin.example.com",
                         voice_out_prices_url="https://vout.example.com/v3",
                         sms_prices_url="http://127.0.0.1:8080/v3")
    assert client.auth_url == "https://auth.example.com"
    assert client.voice_in_prices_url == "https://vin.example.com"
    assert client.voice_out_prices_url == "https://vout.example.com/v3"
    assert client.sms_prices_url == "http://127.0.0.1:8080/v3"


def test_empty_api_key_rejected():
    with pytest.raises(DidwwClientError, match="API key is required"):
        DidwwClient(api_key="")


def test_none_api_key_rejected():
    with pytest.raises(DidwwClientError, match="API key is required"):
        DidwwClient(api_key=None)


def test_non_string_api_key_rejected():
    with pytest.raises(DidwwClientError, match="API key is required"):
        DidwwClient(api_key=b"secret-bytes")


@pytest.mark.parametrize("api_key", [
    "secret key", " secret-lead", "secret-trail ", "secret\nkey", "secret\rkey", "secret\tkey",
    "secret\x01key", "secret\x7fkey", "secret’key", "secretékey",
])
def test_api_key_with_characters_outside_printable_ascii_rejected(api_key):
    with pytest.raises(DidwwClientError, match="not allowed in an HTTP header") as exc:
        DidwwClient(api_key=api_key)
    assert "secret" not in str(exc.value)
    assert "secret" not in repr(exc.value)


def test_printable_api_key_accepted():
    assert DidwwClient(api_key="!~AZaz09-_.+/=").api_key == "!~AZaz09-_.+/="


def test_api_key_is_read_only():
    client = DidwwClient(api_key="test-api-key")
    with pytest.raises(AttributeError):
        client.api_key = "other-key"


def test_environment_must_be_an_environment():
    with pytest.raises(DidwwClientError, match="environment"):
        DidwwClient(api_key="test", environment="https://api.didww.com/v3")


def test_default_api_version():
    client = DidwwClient(api_key="test")
    assert client.api_version == DEFAULT_API_VERSION == DidwwClient.DEFAULT_API_VERSION == "2026-10-22"
    assert not hasattr(DidwwClient, "API_VERSION")


def test_removed_resources_stay_removed():
    assert not hasattr(DidwwClient, "pops")
    assert not hasattr(DidwwClient, "did_group_types")
    assert importlib.util.find_spec("didww.resources.pop") is None
    assert importlib.util.find_spec("didww.resources.did_group_type") is None
    for cls in (DidGroup, AddressRequirement, EmergencyRequirement, EmergencyCallingService):
        assert not hasattr(cls, "did_group_type"), cls.__name__
    assert not isinstance(vars(VoiceInTrunk)["pop"], RelationField)


def test_later_api_version_accepted():
    assert DidwwClient(api_key="test", api_version="2027-03-01").api_version == "2027-03-01"


def test_older_api_version_points_to_release_3():
    with pytest.raises(DidwwClientError) as exc:
        DidwwClient(api_key="test", api_version="2026-04-16")
    assert str(exc.value) == (
        "API version 2026-04-16 is not supported: this SDK requires 2026-10-22 or later; "
        "use didww 3.x (branch release-3) for 2026-04-16"
    )


@pytest.mark.parametrize("api_version", [
    "2026-4-1", "abc", "2026-10-22\n", "２０２６-10-22", "", None, 20261022,
])
def test_malformed_api_version_rejected(api_version):
    with pytest.raises(DidwwClientError, match="YYYY-MM-DD"):
        DidwwClient(api_key="test", api_version=api_version)


@pytest.mark.parametrize("scope, expected", [
    (None, None), (Scope.READ, Scope.READ), (Scope.FULL, Scope.FULL), ("read", Scope.READ), ("full", Scope.FULL),
])
def test_scope(scope, expected):
    assert DidwwClient(api_key="test", scope=scope).scope is expected


@pytest.mark.parametrize("scope", ["admin", "READ", 1])
def test_unknown_scope_rejected(scope):
    with pytest.raises(DidwwClientError, match="scope"):
        DidwwClient(api_key="test", scope=scope)


URL_OPTIONS = [
    ("base_url", "API base"),
    ("auth_url", "Token service"),
    ("voice_in_prices_url", "Voice IN prices"),
    ("voice_out_prices_url", "Voice OUT prices"),
    ("sms_prices_url", "SMS prices"),
]


@pytest.mark.parametrize("option, name", URL_OPTIONS)
@pytest.mark.parametrize("url", [
    "ftp://host.example.com/v3",
    "http://",
    "host.example.com/v3",
    "https://host.example.com/v3?x=1",
    "https://host.example.com/v3#f",
    "https://host.example.com/v 3",
    "https://host.example.com\n/v3",
    "https://host.example.com\t/v3",
    "https://host.example.com\\v3",
    "https://host.example.com:99999/v3",
    "https://host.example.com:port/v3",
    42,
])
def test_invalid_service_urls_rejected(option, name, url):
    with pytest.raises(DidwwClientError, match=f"^{name} URL must be an http or https URL"):
        DidwwClient(api_key="test", **{option: url})


@pytest.mark.parametrize("option, name", URL_OPTIONS)
@pytest.mark.parametrize("url, password", [
    ("https://user:secret-pw@host.example.com/v3", "secret-pw"),
    ("https://user:p#ss@host/v3", "p#ss"),
    ("https://user:p?ss@host/v3", "p?ss"),
    ("https://u:p/w@host/v3", "p/w"),
    (b"https://user:pw@host/v3", "pw"),
    (bytearray(b"https://user:pw@host/v3"), "pw"),
])
def test_service_url_with_user_info_rejected_without_echo(option, name, url, password):
    with pytest.raises(DidwwClientError) as exc:
        DidwwClient(api_key="test", **{option: url})
    assert str(exc.value) == f"{name} URL must be an http or https URL without a query or fragment, " \
                             "got a URL with user info"
    assert password not in repr(exc.value)


@pytest.mark.parametrize("option", ["connect_timeout", "read_timeout"])
@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan"), True, "10",
                                   pytest.param(10 ** 400, id="huge"), pytest.param(-10 ** 400, id="-huge"), pytest.param(sys.maxsize, id="maxsize"), pytest.param(1e12, id="1e12"), pytest.param(1_000_001, id="over-cap")])
def test_invalid_timeouts_rejected(option, value):
    with pytest.raises(DidwwClientError, match=option):
        DidwwClient(api_key="test", **{option: value})


def test_timeouts_may_be_disabled():
    client = DidwwClient(api_key="test", connect_timeout=None, read_timeout=None)
    assert client._timeout == (None, None)


def test_token_store_must_have_get_set_delete():
    class NoDelete:
        def get(self, key):
            return None

        def set(self, key, token, ttl):
            pass

    with pytest.raises(DidwwClientError, match="token_store"):
        DidwwClient(api_key="test", token_store=NoDelete())


def test_token_store_class_rejected():
    with pytest.raises(DidwwClientError, match="^token_store must provide get, set and delete$"):
        DidwwClient(api_key="test", token_store=MemoryTokenStore)


def test_duck_typed_token_store_accepted():
    class Store:
        def get(self, key):
            return None

        def set(self, key, token, ttl):
            pass

        def delete(self, key):
            pass

    store = Store()
    assert DidwwClient(api_key="test", token_store=store).token_store is store


def test_default_token_store_is_shared():
    assert DidwwClient(api_key="a").token_store is DidwwClient(api_key="b").token_store


def test_logger_must_be_a_logger():
    with pytest.raises(DidwwClientError, match="logger"):
        DidwwClient(api_key="test", logger="didww")


@pytest.mark.parametrize("logger", [logging.Logger, logging.LoggerAdapter])
def test_logger_class_rejected(logger):
    with pytest.raises(DidwwClientError, match="^logger must be a logging.Logger or LoggerAdapter$"):
        DidwwClient(api_key="test", logger=logger)


def test_default_logger_is_silent_didww_logger():
    logger = logging.getLogger("didww")
    assert DidwwClient(api_key="test")._logger is logger
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)


def test_api_key_not_in_repr_or_str():
    client = DidwwClient(api_key="secret-api-key-1")
    for text in (repr(client), str(client), repr(client._tokens), repr(client._transport.tokens)):
        assert "secret-api-key-1" not in text


def test_custom_session_preserves_proxy():
    session = requests.Session()
    session.proxies = {"https": "http://proxy.example.com:8080"}
    client = DidwwClient(api_key="test", session=session)
    assert client._session.proxies["https"] == "http://proxy.example.com:8080"
    assert client._service_session.proxies["https"] == "http://proxy.example.com:8080"


def test_custom_session_is_not_mutated():
    session = requests.Session()
    original_headers = dict(session.headers)
    DidwwClient(api_key="test", session=session)
    # The caller's session must not have SDK headers added
    assert "Api-Key" not in session.headers
    assert dict(session.headers) == original_headers


def test_custom_session_preserves_verify():
    session = requests.Session()
    session.verify = "/path/to/ca-bundle.crt"
    client = DidwwClient(api_key="test", session=session)
    assert client._session.verify == "/path/to/ca-bundle.crt"


def test_custom_session_preserves_trust_env():
    session = requests.Session()
    session.trust_env = False
    client = DidwwClient(api_key="test", session=session)
    assert client._session.trust_env is False
    assert client._service_session.trust_env is False


def test_custom_session_auth_and_headers_are_not_copied():
    session = requests.Session()
    session.auth = ("user", "password")
    session.headers["Authorization"] = "Basic abc"
    client = DidwwClient(api_key="test", session=session)
    assert client._session.auth is None
    assert "Authorization" not in client._session.headers


def test_custom_session_adapters_are_independent():
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=5, pool_maxsize=20)
    session.mount("https://", adapter)
    client = DidwwClient(api_key="test", session=session)
    client_adapter = client._session.get_adapter("https://example.com")
    # The client's adapter should not be the same object
    assert client_adapter is not adapter
    # But should preserve configuration
    assert client_adapter._pool_connections == 5
    assert client_adapter._pool_maxsize == 20


def test_service_session_drops_adapter_retries():
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, status_forcelist=[503])))
    client = DidwwClient(api_key="test", session=session)
    assert client._session.get_adapter("https://example.com").max_retries.total == 3
    assert client._service_session.get_adapter("https://example.com").max_retries.total == 0


def test_user_agent_header_set_on_session():
    client = DidwwClient(api_key="my-secret-key")
    expected = f"didww-python-sdk/{_SDK_VERSION}"
    assert client._session.headers["User-Agent"] == expected
    assert client._service_session.headers["User-Agent"] == expected


def test_no_api_key_or_version_header_on_session():
    client = DidwwClient(api_key="my-secret-key")
    for session in (client._session, client._service_session):
        assert "Api-Key" not in session.headers
        assert "X-DIDWW-API-Version" not in session.headers
        assert "Content-Type" not in session.headers


def test_sessions_block_cookies():
    client = DidwwClient(api_key="test")
    for session in (client._session, client._service_session):
        policy = session.cookies.get_policy()
        assert policy.set_ok(MagicMock(), MagicMock()) is False
        assert policy.return_ok(MagicMock(), MagicMock()) is False


def test_every_request_disables_redirects_and_sets_timeouts(monkeypatch):
    client = DidwwClient(api_key="test", base_url="http://test/v3", connect_timeout=3, read_timeout=7,
                         token_store=MemoryTokenStore())
    seed_token(client)
    response = MagicMock(status_code=200, content=b'{"data": []}')
    mock_request = MagicMock(return_value=response)
    monkeypatch.setattr(client._session, "request", mock_request)

    client.get("countries")

    _, kwargs = mock_request.call_args
    assert kwargs["allow_redirects"] is False
    assert kwargs["timeout"] == (3, 7)
    assert kwargs["stream"] is True


def test_custom_session_proxy_used_in_request(monkeypatch):
    session = requests.Session()
    session.proxies = {"https": "http://proxy.example.com:8080"}
    client = DidwwClient(api_key="test", base_url="http://test", session=session)
    assert client._session.proxies["https"] == "http://proxy.example.com:8080"
    mock_request = MagicMock(return_value=MagicMock(status_code=200, content=b'{"data": []}'))
    monkeypatch.setattr(client._session, "request", mock_request)
    client.get("public_keys")
    # Verify the session (which has proxies configured) was used
    mock_request.assert_called_once()


def test_close_and_context_manager(monkeypatch):
    closed = []
    with DidwwClient(api_key="test", token_store=MemoryTokenStore()) as client:
        assert isinstance(client, DidwwClient)
        monkeypatch.setattr(client._session, "close", lambda: closed.append("api"))
        monkeypatch.setattr(client._service_session, "close", lambda: closed.append("service"))
    assert closed == ["api", "service"]
