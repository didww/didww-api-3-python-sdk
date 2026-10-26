from datetime import datetime, timezone

import pytest

from tests.conftest import my_vcr
from didww.enums import SenderIdVerificationStatus, SenderType
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.country import Country
from didww.resources.sender_id_verification import SenderIdVerification
from didww.resources.sms_trunk import SmsTrunk

SIV_ID = "e5a4e2f1-3b26-4a5c-9a0a-2f7c1f3e8d10"
HTTP_OUT_ID = "1a2b3c4d-0003-4a5b-8c6d-7e8f9a0b1c03"

PREDICATES = {
    SenderIdVerificationStatus.ACTIVE: "is_active",
    SenderIdVerificationStatus.CHANGES_REQUIRED: "is_changes_required",
    SenderIdVerificationStatus.CLOSED: "is_closed",
    SenderIdVerificationStatus.CLOSING_IN_PROCESS: "is_closing_in_process",
    SenderIdVerificationStatus.IN_PROCESS: "is_in_process",
    SenderIdVerificationStatus.NEW: "is_new",
}


class TestSenderIdVerificationStatus:
    @pytest.mark.parametrize("status", list(SenderIdVerificationStatus))
    def test_exactly_one_predicate_is_true(self, status):
        verification = SenderIdVerification.from_jsonapi({
            "id": SIV_ID, "type": "sender_id_verifications", "attributes": {"status": status.value},
        })
        assert verification.status == status
        assert {name: getattr(verification, name) for name in PREDICATES.values()} == {
            name: name == PREDICATES[status] for name in PREDICATES.values()
        }

    def test_unknown_values_read_as_raw_strings(self):
        verification = SenderIdVerification.from_jsonapi({
            "id": SIV_ID, "type": "sender_id_verifications",
            "attributes": {"status": "archived", "sender_type": "future_type"},
        })
        assert verification.status == "archived"
        assert verification.sender_type == "future_type"
        assert not any(getattr(verification, name) for name in PREDICATES.values())


class TestSenderIdVerification:
    @my_vcr.use_cassette("sender_id_verifications/list.yaml")
    def test_list(self, client):
        response = client.sender_id_verifications().list()
        active, changes_required = response.data
        assert response.meta["total_records"] == 2
        assert active.name == "ACME alerts"
        assert active.status == SenderIdVerificationStatus.ACTIVE
        assert active.is_active is True
        assert active.sender_type == SenderType.LONG_CODE
        assert active.sender_ids == ["12125550100", "12125550101"]
        assert active.reference == "SID-1234"
        assert active.renew_date == "2026-11-22"
        assert active.created_at == datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        assert active.activated_at == datetime(2026, 10, 3, 12, 30, tzinfo=timezone.utc)
        assert active.closed_at is None
        assert active.reject_reasons is None
        assert active.meta == {"setup_price": "10.0", "monthly_price": "15.0"}
        assert changes_required.is_changes_required is True
        assert changes_required.sender_type == SenderType.ALPHANUMERIC
        assert changes_required.reject_reasons == ["Company documents are missing"]
        assert changes_required.renew_date is None

    @my_vcr.use_cassette("sender_id_verifications/show_with_sms_trunk.yaml")
    def test_find_with_sms_trunk(self, client):
        verification = client.sender_id_verifications().find(SIV_ID, QueryParams().include("sms_trunk")).data
        assert isinstance(verification.sms_trunk, SmsTrunk)
        assert verification.sms_trunk.id == HTTP_OUT_ID
        assert verification.sms_trunk.name == "Outbound HTTP"
        assert verification.sms_trunk.host == "https://sms-out.example.com/outbound_messages"

    @my_vcr.use_cassette("sender_id_verifications/update_name.yaml")
    def test_update_name(self, client):
        verification = SenderIdVerification.build(SIV_ID)
        verification.name = "ACME notifications"
        updated = client.sender_id_verifications().update(verification).data
        assert updated.name == "ACME notifications"
        assert updated.meta == {"setup_price": "10.0", "monthly_price": "15.0"}

    @my_vcr.use_cassette("sender_id_verifications/assign_sms_trunk.yaml")
    def test_assign_sms_trunk(self, client):
        verification = SenderIdVerification.build(SIV_ID)
        verification.sms_trunk = SmsTrunk.build(HTTP_OUT_ID)
        updated = client.sender_id_verifications().update(verification).data
        assert updated.sms_trunk.id == HTTP_OUT_ID

    @my_vcr.use_cassette("sender_id_verifications/unassign_sms_trunk.yaml")
    def test_unassign_sms_trunk(self, client):
        verification = SenderIdVerification.build(SIV_ID)
        verification.sms_trunk = None
        assert verification.sms_trunk is None
        updated = client.sender_id_verifications().update(verification).data
        assert updated.sms_trunk is None

    @my_vcr.use_cassette("sender_id_verifications/update_closed_error.yaml")
    def test_update_closed_verification_fails(self, client):
        verification = SenderIdVerification.build(SIV_ID)
        verification.name = "ACME notifications"
        with pytest.raises(DidwwApiError) as exc_info:
            client.sender_id_verifications().update(verification)
        assert exc_info.value.status_code == 422
        assert "closed" in exc_info.value.errors[0]["detail"]

    @my_vcr.use_cassette("sender_id_verifications/update_name_with_read_only_relationships.yaml")
    def test_included_read_only_relationships_are_not_sent_back(self, client):
        params = QueryParams().include("countries", "dids", "order", "identity", "address")
        verification = client.sender_id_verifications().find(SIV_ID, params).data
        assert [c.iso for c in verification.countries] == ["US"]
        assert [d.number for d in verification.dids] == ["12125550100"]
        assert verification.order.reference == "SPT-474057"
        assert verification.identity.first_name == "Jake"
        assert verification.address.city_name == "Chicago"
        verification.name = "ACME notifications"
        assert client.sender_id_verifications().update(verification).data.name == "ACME notifications"

    @pytest.mark.parametrize("field", ["countries", "dids", "order", "identity", "address"])
    def test_read_only_relationships_cannot_be_assigned(self, field):
        verification = SenderIdVerification.build(SIV_ID)
        with pytest.raises(AttributeError):
            setattr(verification, field, [Country.build("c1")] if field == "countries" else None)
        assert "relationships" not in verification.to_jsonapi(include_id=True, dirty_only=True)

    def test_only_name_is_writable(self):
        verification = SenderIdVerification.from_jsonapi({
            "id": SIV_ID, "type": "sender_id_verifications",
            "attributes": {"name": "n", "status": "active", "renew_date": "2026-11-22"},
        })
        verification.attributes["status"] = "closed"
        verification.name = "renamed"
        assert verification.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {"name": "renamed"}

    def test_repository_has_no_create_or_delete(self, client):
        repository = client.sender_id_verifications()
        assert not hasattr(repository, "create")
        assert not hasattr(repository, "delete")
