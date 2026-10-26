import pytest

from tests.conftest import my_vcr
from didww.exceptions import DidwwApiError
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_regenerate_credential import SmsTrunkRegenerateCredential

HTTP_OUT_ID = "1a2b3c4d-0003-4a5b-8c6d-7e8f9a0b1c03"


class TestSmsTrunkRegenerateCredential:
    @my_vcr.use_cassette("sms_trunk_regenerate_credentials/create.yaml")
    def test_create(self, client):
        credential = SmsTrunkRegenerateCredential()
        credential.sms_trunk = SmsTrunk.build(HTTP_OUT_ID)
        created = client.sms_trunk_regenerate_credentials().create(credential).data
        assert created.id == "3c4d5e6f-0001-4c7d-8e9f-0a1b2c3d4e01"
        assert created.type == "sms_trunk_regenerate_credentials"

    @my_vcr.use_cassette("sms_trunk_regenerate_credentials/create_error.yaml")
    def test_create_error(self, client):
        credential = SmsTrunkRegenerateCredential()
        credential.sms_trunk = SmsTrunk.build(HTTP_OUT_ID)
        with pytest.raises(DidwwApiError) as exc_info:
            client.sms_trunk_regenerate_credentials().create(credential)
        assert exc_info.value.status_code == 422
        assert "credentials" in exc_info.value.errors[0]["detail"]
