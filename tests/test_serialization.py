"""Tests that to_jsonapi() only serializes writable attributes.

When a resource is fetched from the API it contains read-only fields
(created_at, status, etc). These must NOT be included when the resource
is serialized for create/update requests.
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
                "pending_removal": False,
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
        assert attrs["pending_removal"] is False


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
        assert attrs["callback_method"] == "POST"
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
        assert attrs["export_type"] == "cdr_in"
        assert attrs["filters"] == {"year": "2021"}
        assert attrs["callback_url"] == "http://example.com"
        assert attrs["callback_method"] == "POST"


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
        assert attrs["identity_type"] == "Personal"
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
        assert attrs["callback_method"] == "GET"


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
