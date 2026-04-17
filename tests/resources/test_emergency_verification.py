from datetime import datetime, timezone

from tests.conftest import my_vcr
from didww.enums import EmergencyVerificationStatus
from didww.resources.emergency_verification import EmergencyVerification
from didww.resources.address import Address
from didww.resources.emergency_calling_service import EmergencyCallingService
from didww.resources.did import Did


class TestEmergencyVerificationStatusHelpers:
    def test_is_pending(self):
        ev = EmergencyVerification()
        ev.status = EmergencyVerificationStatus.PENDING
        assert ev.is_pending is True
        assert ev.is_approved is False
        assert ev.is_rejected is False

    def test_is_approved(self):
        ev = EmergencyVerification()
        ev.status = EmergencyVerificationStatus.APPROVED
        assert ev.is_approved is True
        assert ev.is_pending is False
        assert ev.is_rejected is False

    def test_is_rejected(self):
        ev = EmergencyVerification()
        ev.status = EmergencyVerificationStatus.REJECTED
        assert ev.is_rejected is True
        assert ev.is_pending is False
        assert ev.is_approved is False

    def test_status_enum_from_string(self):
        ev = EmergencyVerification()
        ev.status = "pending"
        assert ev.status == EmergencyVerificationStatus.PENDING


class TestEmergencyVerification:
    @my_vcr.use_cassette("emergency_verifications/list.yaml")
    def test_list_emergency_verifications(self, client):
        response = client.emergency_verifications().list()
        assert len(response.data) == 1
        ev = response.data[0]
        assert ev.reference == "EVR-001"
        assert ev.status == "pending"

    @my_vcr.use_cassette("emergency_verifications/show.yaml")
    def test_find_emergency_verification(self, client):
        response = client.emergency_verifications().find("ev-001")
        ev = response.data
        assert ev.id == "ev-001"
        assert ev.reference == "EVR-001"
        assert ev.status == "pending"
        assert ev.reject_reasons is None
        assert ev.reject_comment is None
        assert ev.external_reference_id is None
        assert ev.created_at == datetime(2026, 4, 10, 10, 0, 0, 0, tzinfo=timezone.utc)

    @my_vcr.use_cassette("emergency_verifications/create.yaml")
    def test_create_emergency_verification(self, client):
        ev = EmergencyVerification()
        ev.callback_url = "https://example.com/callback"
        ev.address = Address.build("addr-001")
        ev.emergency_calling_service = EmergencyCallingService.build("ecs-001")
        ev.dids = [Did.build("did-001")]
        response = client.emergency_verifications().create(ev)
        created = response.data
        assert created.id == "ev-002"
        assert created.status == "pending"
        assert created.callback_url == "https://example.com/callback"

    def test_patch_external_reference_id_request_body(self):
        """PATCH must send exactly the id, type, and only the dirty attribute."""
        ev = EmergencyVerification.build("ev-001")
        ev.external_reference_id = "updated-ev-ref-77"
        doc = ev.to_jsonapi(include_id=True, dirty_only=True)
        assert doc == {
            "id": "ev-001",
            "type": "emergency_verifications",
            "attributes": {"external_reference_id": "updated-ev-ref-77"},
        }

    @my_vcr.use_cassette("emergency_verifications/update.yaml")
    def test_update_emergency_verification_external_reference_id(self, client):
        ev = EmergencyVerification()
        ev.id = "ev-001"
        ev.external_reference_id = "updated-ev-ref-77"
        response = client.emergency_verifications().update(ev)
        updated = response.data
        assert updated.id == "ev-001"
        assert updated.external_reference_id == "updated-ev-ref-77"
