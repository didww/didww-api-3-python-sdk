from datetime import datetime, timezone

from tests.conftest import my_vcr


class TestEmergencyCallingService:
    @my_vcr.use_cassette("emergency_calling_services/list.yaml")
    def test_list_emergency_calling_services(self, client):
        response = client.emergency_calling_services().list()
        assert len(response.data) == 1
        ecs = response.data[0]
        assert ecs.name == "US Emergency"
        assert ecs.status == "active"

    @my_vcr.use_cassette("emergency_calling_services/show.yaml")
    def test_find_emergency_calling_service(self, client):
        response = client.emergency_calling_services().find("ecs-001")
        ecs = response.data
        assert ecs.id == "ecs-001"
        assert ecs.name == "US Emergency"
        assert ecs.reference == "ECS-123"
        assert ecs.status == "active"
        assert ecs.activated_at == datetime(2026, 4, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
        assert ecs.canceled_at is None
        assert ecs.created_at == datetime(2026, 3, 15, 10, 0, 0, 0, tzinfo=timezone.utc)

    @my_vcr.use_cassette("emergency_calling_services/show_with_includes.yaml")
    def test_find_emergency_calling_service_with_includes(self, client):
        from didww.query_params import QueryParams
        params = QueryParams().include("emergency_requirement", "emergency_verification")
        response = client.emergency_calling_services().find("ecs-001", params)
        ecs = response.data
        assert ecs.id == "ecs-001"
        assert ecs.name == "US Emergency"
        assert ecs.emergency_requirement is not None
        assert ecs.emergency_requirement.id == "er-001"
        assert ecs.emergency_verification is not None
        assert ecs.emergency_verification.id == "ev-001"
        assert ecs.emergency_verification.reference == "EVR-001"

    @my_vcr.use_cassette("emergency_calling_services/delete.yaml")
    def test_delete_emergency_calling_service(self, client):
        result = client.emergency_calling_services().delete("ecs-001")
        assert result is None
