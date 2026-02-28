import pytest
from tests.conftest import my_vcr
from didww.enums import AddressVerificationStatus
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.capacity_pool import CapacityPool
from didww.resources.shared_capacity_group import SharedCapacityGroup
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup


class TestDid:
    @my_vcr.use_cassette("dids/list.yaml")
    def test_list_dids(self, client):
        params = QueryParams().include("order")
        response = client.dids().list(params)
        assert len(response.data) > 0
        first = response.data[0]
        assert first.order is not None
        assert first.order.reference == "TZO-560180"

    @my_vcr.use_cassette("dids/show.yaml")
    def test_find_did(self, client):
        response = client.dids().find("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did = response.data
        assert did.number == "16091609123456797"
        assert did.blocked is False
        assert did.capacity_limit == 2
        assert did.description == "something"
        assert did.terminated is False
        assert did.awaiting_registration is False
        assert did.billing_cycles_count is None
        assert did.channels_included_count == 0
        assert did.dedicated_channels_count == 0

    @my_vcr.use_cassette("dids/show_with_address_verification_and_did_group.yaml")
    def test_find_did_with_address_verification_and_did_group(self, client):
        params = QueryParams().include("address_verification", "did_group")
        response = client.dids().find("21d0b02c-b556-4d3e-acbf-504b78295dbe", params)
        did = response.data
        assert did.number == "61488943592"
        assert did.blocked is False
        av = did.address_verification
        assert av is not None
        assert av.status == AddressVerificationStatus.APPROVED
        assert av.reference == "AHB-291174"
        dg = did.did_group
        assert dg is not None
        assert dg.prefix == "4"
        assert dg.area_name == "Mobile"

    @my_vcr.use_cassette("dids/update_attributes.yaml")
    def test_update_did_attributes(self, client):
        did = Did()
        did.id = "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        did.capacity_limit = 2
        did.description = "something"
        did.terminated = True
        did.billing_cycles_count = 0
        did.dedicated_channels_count = 0
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"
        assert updated.capacity_limit == 2
        assert updated.description == "something"
        assert updated.terminated is True
        assert updated.billing_cycles_count == 0

    @my_vcr.use_cassette("dids/update_voice_in_trunk_group.yaml")
    def test_update_did_with_voice_in_trunk_group(self, client):
        did = Did()
        did.id = "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        group = VoiceInTrunkGroup()
        group.id = "837c5764-a6c3-456f-aa37-71fc8f8ca07b"
        did.voice_in_trunk_group = group
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"

    @my_vcr.use_cassette("dids/update_shared_capacity_group.yaml")
    def test_update_did_shared_capacity_group(self, client):
        did = Did()
        did.id = "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        did.shared_capacity_group = SharedCapacityGroup.build("206881de-7a92-4415-aa32-b05458c79623")
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"
        assert updated.capacity_limit == 2

    @my_vcr.use_cassette("dids/update_capacity_pool.yaml")
    def test_update_did_capacity_pool(self, client):
        did = Did()
        did.id = "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        did.capacity_pool = CapacityPool.build("f288d07c-e2fc-4ae6-9837-b18fb469c324")
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"
        assert updated.capacity_limit == 2

    @my_vcr.use_cassette("dids/update_invalid_trunk_group.yaml")
    def test_update_did_invalid_trunk_group_error(self, client):
        did = Did()
        did.id = "unknown-id"
        did.voice_in_trunk_group = VoiceInTrunkGroup.build("invalid")
        with pytest.raises(DidwwApiError) as exc_info:
            client.dids().update(did)
        assert exc_info.value.status_code == 422
        assert len(exc_info.value.errors) == 1
        assert "voice_in_trunk_group" in exc_info.value.errors[0]["detail"]
