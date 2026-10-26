import pytest
from tests.conftest import my_vcr
from didww.enums import AddressVerificationStatus
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.capacity_pool import CapacityPool
from didww.resources.shared_capacity_group import SharedCapacityGroup
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_group import SmsTrunkGroup
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup


class TestDidRelationships:
    def test_emergency_calling_service_relationship(self):
        did = Did()
        assert hasattr(did, 'emergency_calling_service')

    def test_emergency_verification_relationship(self):
        did = Did()
        assert hasattr(did, 'emergency_verification')

    def test_identity_relationship(self):
        did = Did()
        assert hasattr(did, 'identity')


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
        assert did.emergency_enabled is False

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

    @my_vcr.use_cassette("dids/show_with_address_verification_and_did_group.yaml")
    def test_find_did_with_included_relationships_has_no_dirty_flags(self, client):
        params = QueryParams().include("address_verification", "did_group")
        response = client.dids().find("21d0b02c-b556-4d3e-acbf-504b78295dbe", params)
        did = response.data
        assert len(did._dirty_attrs) == 0
        assert len(did._dirty_rels) == 0
        av = did.address_verification
        assert len(av._dirty_attrs) == 0
        assert len(av._dirty_rels) == 0
        dg = did.did_group
        assert len(dg._dirty_attrs) == 0
        assert len(dg._dirty_rels) == 0

    @my_vcr.use_cassette("dids/update_attributes.yaml")
    def test_update_did(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.capacity_limit = 2
        did.description = "something"
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"
        assert updated.blocked is False
        assert updated.capacity_limit == 2
        assert updated.description == "something"
        assert updated.terminated is False

    @my_vcr.use_cassette("dids/update_terminated.yaml")
    def test_update_did_terminated(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.terminated = True
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.blocked is True
        assert updated.terminated is True
        assert updated.billing_cycles_count == 0

    @my_vcr.use_cassette("dids/update_clear_description.yaml")
    def test_update_did_with_explicit_null_attribute(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.description = None
        response = client.dids().update(did)
        assert response.data.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"

    @my_vcr.use_cassette("dids/update_built_single_attr.yaml")
    def test_update_did_built_resource_sends_only_dirty_attributes(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.description = "a"
        response = client.dids().update(did)
        assert response.data.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"

    @my_vcr.use_cassette("dids/update_set_voice_in_trunk.yaml")
    def test_update_did_set_voice_in_trunk_clears_voice_in_trunk_group(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.voice_in_trunk = VoiceInTrunk.build("41b94706-325e-4704-a433-d65105758836")
        response = client.dids().update(did)
        assert response.data.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"

    @my_vcr.use_cassette("dids/update_voice_in_trunk_group.yaml")
    def test_update_did_set_voice_in_trunk_group_clears_voice_in_trunk(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        group = VoiceInTrunkGroup.build("837c5764-a6c3-456f-aa37-71fc8f8ca07b")
        did.voice_in_trunk_group = group
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"

    @my_vcr.use_cassette("dids/update_from_loaded.yaml")
    def test_update_did_from_loaded_resource_sends_only_dirty_attributes(self, client):
        did = client.dids().find("9df99644-f1a5-4a3c-99a4-559d758eb96b").data
        did.description = "patched from loaded resource"
        response = client.dids().update(did)
        assert response.data.description == "patched from loaded resource"

    @my_vcr.use_cassette("dids/update_from_loaded_set_voice_in_trunk.yaml")
    def test_update_did_from_loaded_resource_sends_only_dirty_relationship(self, client):
        did = client.dids().find("9df99644-f1a5-4a3c-99a4-559d758eb96b").data
        did.voice_in_trunk = VoiceInTrunk.build("41b94706-325e-4704-a433-d65105758836")
        response = client.dids().update(did)
        assert response.data.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"

    @my_vcr.use_cassette("dids/update_shared_capacity_group.yaml")
    def test_update_did_shared_capacity_group(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.shared_capacity_group = SharedCapacityGroup.build("206881de-7a92-4415-aa32-b05458c79623")
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"
        assert updated.capacity_limit == 2

    @my_vcr.use_cassette("dids/update_capacity_pool.yaml")
    def test_update_did_capacity_pool(self, client):
        did = Did.build("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did.capacity_pool = CapacityPool.build("f288d07c-e2fc-4ae6-9837-b18fb469c324")
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "9df99644-f1a5-4a3c-99a4-559d758eb96b"
        assert updated.number == "16091609123456797"
        assert updated.capacity_limit == 2

    @my_vcr.use_cassette("dids/update_invalid_trunk_group.yaml")
    def test_update_did_invalid_trunk_group_error(self, client):
        did = Did.build("unknown-id")
        did.voice_in_trunk_group = VoiceInTrunkGroup.build("invalid")
        with pytest.raises(DidwwApiError) as exc_info:
            client.dids().update(did)
        assert exc_info.value.status_code == 422
        assert len(exc_info.value.errors) == 1
        assert "voice_in_trunk_group" in exc_info.value.errors[0]["detail"]

    def test_unassign_emergency_calling_service_request_body(self):
        """Nulling emergency_calling_service must send relationship data: null."""
        did = Did.build("44957076-778a-4802-b60c-d22db0cda284")
        did._null_relationship("emergency_calling_service")
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc == {
            "id": "44957076-778a-4802-b60c-d22db0cda284",
            "type": "dids",
            "attributes": {},
            "relationships": {
                "emergency_calling_service": {"data": None},
            },
        }

    @my_vcr.use_cassette("dids/update_unassign_ecs.yaml")
    def test_update_did_unassign_emergency_calling_service(self, client):
        did = Did.build("44957076-778a-4802-b60c-d22db0cda284")
        did._null_relationship("emergency_calling_service")
        response = client.dids().update(did)
        updated = response.data
        assert updated.id == "44957076-778a-4802-b60c-d22db0cda284"
        assert updated.emergency_enabled is False


DID_ID = "9df99644-f1a5-4a3c-99a4-559d758eb96b"
SMS_TRUNK_ID = "1a2b3c4d-0002-4a5b-8c6d-7e8f9a0b1c02"
SMS_TRUNK_GROUP_ID = "2b3c4d5e-0001-4b6c-9d7e-8f9a0b1c2d01"


class TestDidSmsRouting:
    @my_vcr.use_cassette("dids/show_with_sms_trunk.yaml")
    def test_find_did_with_sms_trunk(self, client):
        did = client.dids().find(DID_ID, QueryParams().include("sms_trunk")).data
        assert isinstance(did.sms_trunk, SmsTrunk)
        assert did.sms_trunk.id == SMS_TRUNK_ID
        assert did.sms_trunk.name == "http_in trunk"
        assert did.sms_trunk_group is None
        assert did._dirty_attrs == set()
        assert did._dirty_rels == set()

    @my_vcr.use_cassette("dids/show_with_sms_trunk_group.yaml")
    def test_find_did_with_sms_trunk_group(self, client):
        did = client.dids().find(DID_ID, QueryParams().include("sms_trunk_group")).data
        assert isinstance(did.sms_trunk_group, SmsTrunkGroup)
        assert did.sms_trunk_group.id == SMS_TRUNK_GROUP_ID
        assert did.sms_trunk_group.name == "Inbound SMS"
        assert did.sms_trunk is None
        assert did._dirty_attrs == set()
        assert did._dirty_rels == set()

    @my_vcr.use_cassette("dids/update_assign_sms_trunk.yaml")
    def test_assign_sms_trunk_unassigns_sms_trunk_group(self, client):
        did = Did.build(DID_ID)
        did.sms_trunk = SmsTrunk.build(SMS_TRUNK_ID)
        assert did.sms_trunk_group is None
        assert client.dids().update(did).data.id == DID_ID

    @my_vcr.use_cassette("dids/update_assign_sms_trunk_group.yaml")
    def test_assign_sms_trunk_group_unassigns_sms_trunk(self, client):
        did = Did.build(DID_ID)
        did.sms_trunk_group = SmsTrunkGroup.build(SMS_TRUNK_GROUP_ID)
        assert did.sms_trunk is None
        assert client.dids().update(did).data.id == DID_ID

    @my_vcr.use_cassette("dids/update_unassign_sms_trunk.yaml")
    def test_unassign_sms_trunk_leaves_sms_trunk_group_alone(self, client):
        did = Did.build(DID_ID)
        did.sms_trunk = None
        assert did.sms_trunk is None
        assert client.dids().update(did).data.id == DID_ID

    @my_vcr.use_cassette("dids/update_unassign_sms_trunk_group.yaml")
    def test_unassign_sms_trunk_group_leaves_sms_trunk_alone(self, client):
        did = Did.build(DID_ID)
        did.sms_trunk_group = None
        assert did.sms_trunk_group is None
        assert client.dids().update(did).data.id == DID_ID

    @my_vcr.use_cassette("dids/update_unassign_sms.yaml")
    def test_unassign_both_sms_relationships(self, client):
        did = Did.build(DID_ID)
        did.sms_trunk = None
        did.sms_trunk_group = None
        assert client.dids().update(did).data.id == DID_ID

    @my_vcr.use_cassette("dids/show_with_sms_trunk.yaml")
    def test_unassign_loaded_sms_trunk_reads_back_as_none(self, client):
        did = client.dids().find(DID_ID, QueryParams().include("sms_trunk")).data
        did.sms_trunk = None
        assert did.sms_trunk is None
        assert did.to_jsonapi(include_id=True, dirty_only=True) == {
            "id": DID_ID,
            "type": "dids",
            "attributes": {},
            "relationships": {"sms_trunk": {"data": None}},
        }

    def test_unassign_voice_in_trunk_sends_only_that_relationship(self):
        did = Did.build(DID_ID)
        did.voice_in_trunk = None
        assert did.voice_in_trunk is None
        assert did.to_jsonapi(include_id=True, dirty_only=True) == {
            "id": DID_ID,
            "type": "dids",
            "attributes": {},
            "relationships": {"voice_in_trunk": {"data": None}},
        }
