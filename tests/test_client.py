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
