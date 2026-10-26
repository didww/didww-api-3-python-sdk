import pytest

from tests.conftest import my_vcr
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_group import SmsTrunkGroup

GROUP_ID = "2b3c4d5e-0001-4b6c-9d7e-8f9a0b1c2d01"
HTTP_IN_ID = "1a2b3c4d-0002-4a5b-8c6d-7e8f9a0b1c02"
SMSC_ID = "1a2b3c4d-0005-4a5b-8c6d-7e8f9a0b1c05"
DID_ID = "9df99644-f1a5-4a3c-99a4-559d758eb96b"


class TestSmsTrunkGroup:
    @my_vcr.use_cassette("sms_trunk_groups/list.yaml")
    def test_list(self, client):
        response = client.sms_trunk_groups().list()
        groups = response.data
        assert [g.name for g in groups] == ["Inbound SMS", "Outbound SMS"]
        assert [g.sms_trunks_count for g in groups] == [2, 0]
        assert groups[0].external_reference_id is None
        assert groups[0].created_at.year == 2026
        assert response.meta["total_records"] == 2

    @my_vcr.use_cassette("sms_trunk_groups/show_with_sms_trunks.yaml")
    def test_find_with_sms_trunks(self, client):
        group = client.sms_trunk_groups().find(GROUP_ID, QueryParams().include("sms_trunks")).data
        assert group.id == GROUP_ID
        assert group.sms_trunks_count == 2
        trunks = group.sms_trunks
        assert [t.id for t in trunks] == [HTTP_IN_ID, SMSC_ID]
        assert all(isinstance(t, SmsTrunk) for t in trunks)
        assert group._dirty_rels == set()

    @my_vcr.use_cassette("sms_trunk_groups/show_not_found.yaml")
    def test_find_not_found(self, client):
        with pytest.raises(DidwwApiError) as exc_info:
            client.sms_trunk_groups().find(GROUP_ID)
        assert exc_info.value.status_code == 404

    @my_vcr.use_cassette("sms_trunk_groups/create.yaml")
    def test_create_keeps_meta(self, client):
        group = SmsTrunkGroup()
        group.name = "Inbound SMS"
        group.sms_trunks = [SmsTrunk.build(HTTP_IN_ID)]
        created = client.sms_trunk_groups().create(group).data
        assert created.id == GROUP_ID
        assert created.sms_trunks_count == 1
        assert [t.id for t in created.sms_trunks] == [HTTP_IN_ID]

    @my_vcr.use_cassette("sms_trunk_groups/update_external_reference_id.yaml")
    def test_update_external_reference_id(self, client):
        group = SmsTrunkGroup.build(GROUP_ID)
        group.external_reference_id = "updated-ext-ref-99"
        updated = client.sms_trunk_groups().update(group).data
        assert updated.external_reference_id == "updated-ext-ref-99"

    @my_vcr.use_cassette("sms_trunk_groups/update_sms_trunks.yaml")
    def test_update_replaces_sms_trunks(self, client):
        group = SmsTrunkGroup.build(GROUP_ID)
        group.sms_trunks = [SmsTrunk.build(HTTP_IN_ID), SmsTrunk.build(SMSC_ID)]
        updated = client.sms_trunk_groups().update(group).data
        assert [t.id for t in updated.sms_trunks] == [HTTP_IN_ID, SMSC_ID]
        assert updated.sms_trunks_count == 2

    @my_vcr.use_cassette("sms_trunk_groups/update_clear_sms_trunks.yaml")
    def test_update_with_empty_list_clears_sms_trunks(self, client):
        group = SmsTrunkGroup.build(GROUP_ID)
        group.sms_trunks = []
        updated = client.sms_trunk_groups().update(group).data
        assert updated.id == GROUP_ID
        assert updated.sms_trunks_count == 0

    @my_vcr.use_cassette("sms_trunk_groups/update_clear_sms_trunks.yaml")
    def test_update_with_none_clears_sms_trunks(self, client):
        group = SmsTrunkGroup.build(GROUP_ID)
        group.sms_trunks = None
        assert group.sms_trunks == []
        updated = client.sms_trunk_groups().update(group).data
        assert updated.id == GROUP_ID
        assert updated.sms_trunks_count == 0

    @my_vcr.use_cassette("sms_trunk_groups/update_name_with_included_relationships.yaml")
    def test_included_incoming_dids_are_not_sent_back(self, client):
        group = client.sms_trunk_groups().find(GROUP_ID, QueryParams().include("incoming_dids")).data
        assert [d.id for d in group.incoming_dids] == [DID_ID]
        group.name = "Inbound SMS EU"
        assert client.sms_trunk_groups().update(group).data.name == "Inbound SMS EU"

    def test_incoming_dids_cannot_be_assigned(self):
        group = SmsTrunkGroup.build(GROUP_ID)
        with pytest.raises(AttributeError):
            group.incoming_dids = [Did.build(DID_ID)]
        assert "relationships" not in group.to_jsonapi(include_id=True, dirty_only=True)

    def test_create_from_a_loaded_group_drops_incoming_dids(self):
        group = SmsTrunkGroup.from_jsonapi({
            "id": GROUP_ID,
            "type": "sms_trunk_groups",
            "attributes": {"name": "copy"},
            "relationships": {
                "sms_trunks": {"data": [{"type": "sms_trunks", "id": HTTP_IN_ID}]},
                "incoming_dids": {"data": [{"type": "dids", "id": DID_ID}]},
            },
        })
        assert group.to_jsonapi()["relationships"] == {
            "sms_trunks": {"data": [{"type": "sms_trunks", "id": HTTP_IN_ID}]},
        }

    @my_vcr.use_cassette("sms_trunk_groups/delete.yaml")
    def test_delete(self, client):
        assert client.sms_trunk_groups().delete(GROUP_ID) is None

    @my_vcr.use_cassette("sms_trunk_groups/delete_error.yaml")
    def test_delete_error(self, client):
        with pytest.raises(DidwwApiError) as exc_info:
            client.sms_trunk_groups().delete(GROUP_ID)
        assert exc_info.value.status_code == 422
