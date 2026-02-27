import requests
import pytest
from didww.client import DidwwClient
from didww.configuration import Environment
from didww.exceptions import DidwwClientError


def test_sandbox_url():
    client = DidwwClient(api_key="test", environment=Environment.SANDBOX)
    assert client.base_url == "https://sandbox-api.didww.com/v3"


def test_production_url():
    client = DidwwClient(api_key="test", environment=Environment.PRODUCTION)
    assert client.base_url == "https://api.didww.com/v3"


def test_custom_base_url():
    client = DidwwClient(api_key="test", base_url="http://localhost:3000/v3")
    assert client.base_url == "http://localhost:3000/v3"


def test_empty_api_key_rejected():
    with pytest.raises(DidwwClientError, match="API key is required"):
        DidwwClient(api_key="")


def test_none_api_key_rejected():
    with pytest.raises(DidwwClientError, match="API key is required"):
        DidwwClient(api_key=None)


def test_custom_session_preserves_proxy():
    session = requests.Session()
    session.proxies = {"https": "http://proxy.example.com:8080"}
    client = DidwwClient(api_key="test", session=session)
    assert client._session.proxies["https"] == "http://proxy.example.com:8080"


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


def test_auth_headers_sent_for_regular_paths():
    client = DidwwClient(api_key="my-secret-key")
    assert client._auth_headers("countries") == {"Api-Key": "my-secret-key"}
    assert client._auth_headers("dids") == {"Api-Key": "my-secret-key"}
    assert client._auth_headers("voice_in_trunks") == {"Api-Key": "my-secret-key"}


def test_auth_headers_not_sent_for_public_keys():
    client = DidwwClient(api_key="my-secret-key")
    assert client._auth_headers("public_keys") == {}
    assert client._auth_headers("public_keys/some-uuid") == {}
