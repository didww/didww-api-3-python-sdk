from unittest.mock import patch, MagicMock

import requests
from requests.adapters import HTTPAdapter
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


def test_auth_headers_not_false_positive_for_public_keys_substring():
    client = DidwwClient(api_key="my-secret-key")
    # Paths that contain "public_keys" as a substring should still get auth headers
    assert client._auth_headers("not_public_keys") == {"Api-Key": "my-secret-key"}
    assert client._auth_headers("some_public_keys_extra") == {"Api-Key": "my-secret-key"}


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


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = b'{"data": []}'
    resp.json.return_value = json_data or {"data": []}
    return resp


def test_get_sends_api_key_header(monkeypatch):
    client = DidwwClient(api_key="my-secret-key", base_url="http://test")
    mock_get = MagicMock(return_value=_mock_response())
    monkeypatch.setattr(client._session, "get", mock_get)
    client.get("countries")
    _, kwargs = mock_get.call_args
    assert kwargs["headers"]["Api-Key"] == "my-secret-key"


def test_get_omits_api_key_for_public_keys(monkeypatch):
    client = DidwwClient(api_key="my-secret-key", base_url="http://test")
    mock_get = MagicMock(return_value=_mock_response())
    monkeypatch.setattr(client._session, "get", mock_get)
    client.get("public_keys")
    _, kwargs = mock_get.call_args
    assert "Api-Key" not in kwargs["headers"]


def test_custom_session_proxy_used_in_request(monkeypatch):
    session = requests.Session()
    session.proxies = {"https": "http://proxy.example.com:8080"}
    client = DidwwClient(api_key="test", base_url="http://test", session=session)
    assert client._session.proxies["https"] == "http://proxy.example.com:8080"
    mock_get = MagicMock(return_value=_mock_response())
    monkeypatch.setattr(client._session, "get", mock_get)
    client.get("countries")
    # Verify the session (which has proxies configured) was used
    mock_get.assert_called_once()
