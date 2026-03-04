"""Tests for serialization: writable-attribute filtering and dirty-only PATCH.

When a resource is fetched from the API it contains read-only fields
(created_at, status, etc). These must NOT be included when the resource
is serialized for create/update requests.

PATCH (update) requests must include only fields explicitly changed by user
code ("dirty fields"). Explicit null assignments must be preserved.
"""

from didww.resources.did import Did
from didww.resources.order import Order
from didww.resources.export import Export
from didww.resources.identity import Identity
from didww.resources.address import Address
from didww.resources.address_verification import AddressVerification
from didww.resources.shared_capacity_group import SharedCapacityGroup
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup
from didww.resources.voice_out_trunk import VoiceOutTrunk
from didww.enums import (
    CallbackMethod,
    ExportType,
    IdentityType,
    enum_value,
)


class TestDidSerialization:
    def test_excludes_read_only_fields(self):
        did = Did.from_jsonapi({
            "id": "abc",
            "type": "dids",
            "attributes": {
                "number": "123456789",
                "blocked": False,
                "awaiting_registration": False,
                "created_at": "2021-01-01T00:00:00Z",
                "expires_at": "2022-01-01T00:00:00Z",
                "channels_included_count": 1,
                "capacity_limit": 10,
                "description": "test",
                "billing_cycles_count": 1,
                "terminated": False,
                "dedicated_channels_count": 0,
            },
        })
        doc = did.to_jsonapi(include_id=True)
        attrs = doc["attributes"]
        assert "number" not in attrs
        assert "blocked" not in attrs
        assert "awaiting_registration" not in attrs
        assert "created_at" not in attrs
        assert "expires_at" not in attrs
        assert "channels_included_count" not in attrs
        # writable fields must be present
        assert attrs["capacity_limit"] == 10
        assert attrs["description"] == "test"
        assert attrs["billing_cycles_count"] == 1
        assert attrs["terminated"] is False
        assert attrs["dedicated_channels_count"] == 0

    def test_nullifies_voice_in_trunk_when_trunk_group_assigned(self):
        did = Did()
        did.id = "abc"
        group = VoiceInTrunkGroup()
        group.id = "group-1"
        did.voice_in_trunk_group = group
        doc = did.to_jsonapi(include_id=True)
        rels = doc["relationships"]
        assert rels["voice_in_trunk_group"]["data"]["type"] == "voice_in_trunk_groups"
        assert rels["voice_in_trunk_group"]["data"]["id"] == "group-1"
        assert rels["voice_in_trunk"]["data"] is None

    def test_nullifies_voice_in_trunk_group_when_trunk_assigned(self):
        did = Did()
        did.id = "abc"
        trunk = VoiceInTrunk()
        trunk.id = "trunk-1"
        did.voice_in_trunk = trunk
        doc = did.to_jsonapi(include_id=True)
        rels = doc["relationships"]
        assert rels["voice_in_trunk"]["data"]["type"] == "voice_in_trunks"
        assert rels["voice_in_trunk"]["data"]["id"] == "trunk-1"
        assert rels["voice_in_trunk_group"]["data"] is None


class TestOrderSerialization:
    def test_excludes_read_only_fields(self):
        order = Order.from_jsonapi({
            "id": "abc",
            "type": "orders",
            "attributes": {
                "amount": "99.99",
                "status": "Completed",
                "created_at": "2021-01-01T00:00:00Z",
                "description": "Order desc",
                "reference": "REF-123",
                "callback_url": "http://example.com",
                "callback_method": "POST",
                "allow_back_ordering": True,
                "items": [],
            },
        })
        doc = order.to_jsonapi()
        attrs = doc["attributes"]
        assert "amount" not in attrs
        assert "status" not in attrs
        assert "created_at" not in attrs
        assert "description" not in attrs
        assert "reference" not in attrs
        # writable fields must be present
        assert attrs["callback_url"] == "http://example.com"
        assert attrs["callback_method"] == enum_value(CallbackMethod.POST)
        assert attrs["allow_back_ordering"] is True
        assert attrs["items"] == []


class TestExportSerialization:
    def test_excludes_read_only_fields(self):
        export = Export.from_jsonapi({
            "id": "abc",
            "type": "exports",
            "attributes": {
                "status": "Completed",
                "created_at": "2021-01-01T00:00:00Z",
                "url": "https://example.com/export.csv",
                "export_type": "cdr_in",
                "filters": {"year": "2021"},
                "callback_url": "http://example.com",
                "callback_method": "POST",
            },
        })
        doc = export.to_jsonapi()
        attrs = doc["attributes"]
        assert "status" not in attrs
        assert "created_at" not in attrs
        assert "url" not in attrs
        # writable fields must be present
        assert attrs["export_type"] == enum_value(ExportType.CDR_IN)
        assert attrs["filters"] == {"year": "2021"}
        assert attrs["callback_url"] == "http://example.com"
        assert attrs["callback_method"] == enum_value(CallbackMethod.POST)


class TestIdentitySerialization:
    def test_excludes_read_only_fields(self):
        identity = Identity.from_jsonapi({
            "id": "abc",
            "type": "identities",
            "attributes": {
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+123",
                "id_number": "ID-1",
                "birth_date": "1990-01-01",
                "company_name": "ACME",
                "company_reg_number": "REG-1",
                "vat_id": "VAT-1",
                "description": "desc",
                "personal_tax_id": "TAX-1",
                "identity_type": "Personal",
                "external_reference_id": "EXT-1",
                "contact_email": "john@example.com",
                "created_at": "2021-01-01T00:00:00Z",
                "verified": True,
            },
        })
        doc = identity.to_jsonapi()
        attrs = doc["attributes"]
        assert "created_at" not in attrs
        assert "verified" not in attrs
        # writable fields must be present
        assert attrs["first_name"] == "John"
        assert attrs["last_name"] == "Doe"
        assert attrs["identity_type"] == enum_value(IdentityType.PERSONAL)
        assert attrs["contact_email"] == "john@example.com"


class TestAddressSerialization:
    def test_excludes_read_only_fields(self):
        address = Address.from_jsonapi({
            "id": "abc",
            "type": "addresses",
            "attributes": {
                "city_name": "Brussels",
                "postal_code": "1000",
                "address": "123 Main St",
                "description": "desc",
                "created_at": "2021-01-01T00:00:00Z",
                "verified": True,
            },
        })
        doc = address.to_jsonapi()
        attrs = doc["attributes"]
        assert "created_at" not in attrs
        assert "verified" not in attrs
        # writable fields must be present
        assert attrs["city_name"] == "Brussels"
        assert attrs["postal_code"] == "1000"
        assert attrs["address"] == "123 Main St"
        assert attrs["description"] == "desc"


class TestAddressVerificationSerialization:
    def test_excludes_read_only_fields(self):
        av = AddressVerification.from_jsonapi({
            "id": "abc",
            "type": "address_verifications",
            "attributes": {
                "status": "Pending",
                "service_description": "svc",
                "callback_url": "http://example.com",
                "callback_method": "GET",
                "reject_reasons": "reason",
                "reference": "REF-1",
                "created_at": "2021-01-01T00:00:00Z",
            },
        })
        doc = av.to_jsonapi()
        attrs = doc["attributes"]
        assert "status" not in attrs
        assert "reject_reasons" not in attrs
        assert "reference" not in attrs
        assert "created_at" not in attrs
        # writable fields must be present
        assert attrs["service_description"] == "svc"
        assert attrs["callback_url"] == "http://example.com"
        assert attrs["callback_method"] == enum_value(CallbackMethod.GET)


class TestSharedCapacityGroupSerialization:
    def test_excludes_read_only_fields(self):
        scg = SharedCapacityGroup.from_jsonapi({
            "id": "abc",
            "type": "shared_capacity_groups",
            "attributes": {
                "name": "My Group",
                "shared_channels_count": 10,
                "metered_channels_count": 5,
                "created_at": "2021-01-01T00:00:00Z",
            },
        })
        doc = scg.to_jsonapi()
        attrs = doc["attributes"]
        assert "created_at" not in attrs
        # writable fields must be present
        assert attrs["name"] == "My Group"
        assert attrs["shared_channels_count"] == 10
        assert attrs["metered_channels_count"] == 5


class TestVoiceInTrunkSerialization:
    def test_excludes_read_only_fields(self):
        trunk = VoiceInTrunk.from_jsonapi({
            "id": "abc",
            "type": "voice_in_trunks",
            "attributes": {
                "name": "Trunk 1",
                "priority": 1,
                "weight": 100,
                "capacity_limit": 10,
                "cli_format": "e164",
                "cli_prefix": "+1",
                "description": "desc",
                "ringing_timeout": 30,
                "created_at": "2021-01-01T00:00:00Z",
                "configuration": {"type": "pstn_configurations", "attributes": {"dst": "123"}},
            },
        })
        doc = trunk.to_jsonapi()
        attrs = doc["attributes"]
        assert "created_at" not in attrs
        # writable fields must be present
        assert attrs["name"] == "Trunk 1"
        assert attrs["priority"] == 1
        assert attrs["capacity_limit"] == 10
        assert "configuration" in attrs


class TestVoiceInTrunkGroupSerialization:
    def test_excludes_read_only_fields(self):
        group = VoiceInTrunkGroup.from_jsonapi({
            "id": "abc",
            "type": "voice_in_trunk_groups",
            "attributes": {
                "name": "Group 1",
                "capacity_limit": 10,
                "created_at": "2021-01-01T00:00:00Z",
            },
        })
        doc = group.to_jsonapi()
        attrs = doc["attributes"]
        assert "created_at" not in attrs
        # writable fields must be present
        assert attrs["name"] == "Group 1"
        assert attrs["capacity_limit"] == 10


class TestVoiceOutTrunkSerialization:
    def test_excludes_read_only_fields(self):
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": "abc",
            "type": "voice_out_trunks",
            "attributes": {
                "name": "Trunk 1",
                "allowed_sip_ips": ["1.2.3.4"],
                "on_cli_mismatch_action": "reject",
                "capacity_limit": 10,
                "status": "Active",
                "username": "user123",
                "password": "pass456",
                "threshold_reached": False,
                "created_at": "2021-01-01T00:00:00Z",
            },
        })
        doc = trunk.to_jsonapi()
        attrs = doc["attributes"]
        assert "username" not in attrs
        assert "password" not in attrs
        assert "threshold_reached" not in attrs
        assert "created_at" not in attrs
        # writable fields must be present
        assert attrs["name"] == "Trunk 1"
        assert attrs["allowed_sip_ips"] == ["1.2.3.4"]
        assert attrs["capacity_limit"] == 10
        assert attrs["status"] == "Active"


# ---------------------------------------------------------------------------
# Dirty-only PATCH serialization tests
# ---------------------------------------------------------------------------


class TestDirtyTrackingAttributes:
    """PATCH must include only explicitly changed attributes."""

    def test_build_set_one_attr_only_that_attr_sent(self):
        """Scenario 1: build(id), set one attribute -> only that attribute."""
        did = Did.build("abc")
        did.capacity_limit = 20
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["id"] == "abc"
        assert doc["type"] == "dids"
        assert doc["attributes"] == {"capacity_limit": 20}
        assert "relationships" not in doc

    def test_set_attribute_to_null_sends_explicit_null(self):
        """Scenario 2: set attribute to None -> explicit null in PATCH."""
        did = Did.build("abc")
        did.description = None
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"] == {"description": None}

    def test_loaded_object_set_one_field_only_changed_sent(self):
        """Scenario 3: load from API, set one field -> only that field."""
        did = Did.from_jsonapi({
            "id": "abc",
            "type": "dids",
            "attributes": {
                "number": "123456789",
                "blocked": False,
                "capacity_limit": 10,
                "description": "original",
                "billing_cycles_count": 1,
                "terminated": False,
                "dedicated_channels_count": 0,
            },
        })
        did.capacity_limit = 20
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["id"] == "abc"
        assert doc["attributes"] == {"capacity_limit": 20}
        assert "relationships" not in doc

    def test_multiple_dirty_attrs_all_included(self):
        did = Did.build("abc")
        did.capacity_limit = 20
        did.description = "updated"
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"] == {"capacity_limit": 20, "description": "updated"}

    def test_no_dirty_fields_empty_attributes(self):
        did = Did.build("abc")
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc == {"type": "dids", "id": "abc", "attributes": {}}

    def test_dirty_state_cleared_after_deserialization(self):
        did = Did.from_jsonapi({
            "id": "abc",
            "type": "dids",
            "attributes": {
                "capacity_limit": 10,
                "description": "test",
            },
        })
        assert len(did._dirty_attrs) == 0
        assert len(did._dirty_rels) == 0

    def test_read_only_attrs_excluded_even_when_dirty(self):
        """Non-writable attributes must never appear in PATCH."""
        did = Did.build("abc")
        did.attributes["number"] = "999"  # number is read-only
        did.capacity_limit = 20
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert "number" not in doc["attributes"]
        assert doc["attributes"] == {"capacity_limit": 20}

    def test_build_with_kwargs_includes_attrs_in_dirty_patch(self):
        """Attributes passed as kwargs to build() must be dirty."""
        did = Did.build("abc", description="test", capacity_limit=5)
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"] == {"description": "test", "capacity_limit": 5}

    def test_create_sends_all_non_null_writable_attrs(self):
        """CREATE (non-dirty) serialization sends all non-null writable attrs."""
        did = Did()
        did.capacity_limit = 10
        did.description = "test"
        did.billing_cycles_count = 1
        doc = did.to_jsonapi()
        attrs = doc["attributes"]
        assert attrs["capacity_limit"] == 10
        assert attrs["description"] == "test"
        assert attrs["billing_cycles_count"] == 1


class TestDirtyTrackingRelationships:
    """PATCH must include only dirty relationships + explicit null clears."""

    def test_set_voice_in_trunk_nullifies_trunk_group(self):
        """Scenario 4: set voice_in_trunk -> voice_in_trunk_group is null."""
        did = Did.build("abc")
        trunk = VoiceInTrunk()
        trunk.id = "trunk-1"
        did.voice_in_trunk = trunk
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        rels = doc["relationships"]
        assert rels["voice_in_trunk"]["data"]["type"] == "voice_in_trunks"
        assert rels["voice_in_trunk"]["data"]["id"] == "trunk-1"
        assert rels["voice_in_trunk_group"]["data"] is None

    def test_set_voice_in_trunk_group_nullifies_trunk(self):
        """Scenario 5: set voice_in_trunk_group -> voice_in_trunk is null."""
        did = Did.build("abc")
        group = VoiceInTrunkGroup()
        group.id = "group-1"
        did.voice_in_trunk_group = group
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        rels = doc["relationships"]
        assert rels["voice_in_trunk_group"]["data"]["type"] == "voice_in_trunk_groups"
        assert rels["voice_in_trunk_group"]["data"]["id"] == "group-1"
        assert rels["voice_in_trunk"]["data"] is None

    def test_loaded_object_no_dirty_rels_omitted(self):
        """Loaded object with relationships -> no rels in dirty PATCH."""
        did = Did.from_jsonapi({
            "id": "abc",
            "type": "dids",
            "attributes": {"capacity_limit": 10},
            "relationships": {
                "did_group": {"data": {"type": "did_groups", "id": "g1"}},
            },
        })
        did.capacity_limit = 20
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        assert "relationships" not in doc

    def test_loaded_object_change_relationship(self):
        """Loaded object with rel, change rel -> only changed rel sent."""
        did = Did.from_jsonapi({
            "id": "abc",
            "type": "dids",
            "attributes": {"capacity_limit": 10},
            "relationships": {
                "did_group": {"data": {"type": "did_groups", "id": "g1"}},
                "voice_in_trunk": {"data": {"type": "voice_in_trunks", "id": "t1"}},
            },
        })
        trunk = VoiceInTrunk()
        trunk.id = "t2"
        did.voice_in_trunk = trunk
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        rels = doc["relationships"]
        # did_group was not touched, must be absent
        assert "did_group" not in rels
        # voice_in_trunk was changed
        assert rels["voice_in_trunk"]["data"]["id"] == "t2"
        # exclusive null
        assert rels["voice_in_trunk_group"]["data"] is None

    def test_set_regular_relationship(self):
        """Non-exclusive relationship set -> only that rel in PATCH."""
        from didww.resources.did_group import DidGroup
        did = Did.build("abc")
        group = DidGroup()
        group.id = "dg-1"
        did.did_group = group
        doc = did.to_jsonapi(include_id=True, dirty_only=True)
        rels = doc["relationships"]
        assert rels["did_group"]["data"]["type"] == "did_groups"
        assert rels["did_group"]["data"]["id"] == "dg-1"
        assert len(rels) == 1


class TestMutableAttributeTracking:
    """In-place mutations on mutable attribute values must mark the key dirty."""

    def _voice_out_trunk(self, **attrs):
        from didww.resources.voice_out_trunk import VoiceOutTrunk
        attrs.setdefault("name", "test")
        return VoiceOutTrunk.from_jsonapi({
            "id": "t1",
            "type": "voice_out_trunks",
            "attributes": attrs,
        })

    def test_list_append_marks_dirty(self):
        trunk = self._voice_out_trunk(allowed_sip_ips=["1.2.3.4"])
        trunk.allowed_sip_ips.append("5.6.7.8")
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["1.2.3.4", "5.6.7.8"]

    def test_list_extend_marks_dirty(self):
        trunk = self._voice_out_trunk(allowed_sip_ips=["1.2.3.4"])
        trunk.allowed_sip_ips.extend(["5.6.7.8", "9.10.11.12"])
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["1.2.3.4", "5.6.7.8", "9.10.11.12"]

    def test_list_remove_marks_dirty(self):
        trunk = self._voice_out_trunk(allowed_sip_ips=["1.2.3.4", "5.6.7.8"])
        trunk.allowed_sip_ips.remove("1.2.3.4")
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["5.6.7.8"]

    def test_list_iadd_marks_dirty(self):
        trunk = self._voice_out_trunk(allowed_sip_ips=["1.2.3.4"])
        trunk.allowed_sip_ips += ["5.6.7.8"]
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["1.2.3.4", "5.6.7.8"]

    def test_list_sort_marks_dirty(self):
        trunk = self._voice_out_trunk(allowed_sip_ips=["5.6.7.8", "1.2.3.4"])
        trunk.allowed_sip_ips.sort()
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["1.2.3.4", "5.6.7.8"]

    def test_list_reverse_marks_dirty(self):
        trunk = self._voice_out_trunk(allowed_sip_ips=["1.2.3.4", "5.6.7.8"])
        trunk.allowed_sip_ips.reverse()
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["5.6.7.8", "1.2.3.4"]

    def test_setdefault_wraps_list_for_mutation_tracking(self):
        """setdefault with a list default must wrap it so in-place mutations are tracked after dirty clear."""
        trunk = self._voice_out_trunk()
        trunk.attributes.setdefault("allowed_sip_ips", ["1.2.3.4"])
        # Clear dirty state to simulate a save/reload cycle
        trunk._clear_dirty_state()
        assert len(trunk._dirty_attrs) == 0
        # Mutate the list in-place — only a wrapped list will re-mark the key dirty
        trunk.allowed_sip_ips.append("5.6.7.8")
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc["attributes"]["allowed_sip_ips"] == ["1.2.3.4", "5.6.7.8"]

