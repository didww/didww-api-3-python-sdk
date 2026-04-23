import pytest
from tests.conftest import my_vcr
from didww.resources.emergency_requirement_validation import EmergencyRequirementValidation
from didww.resources.emergency_requirement import EmergencyRequirement
from didww.resources.address import Address
from didww.resources.identity import Identity


class TestEmergencyRequirementValidation:
    def test_has_emergency_requirement_relationship(self):
        rv = EmergencyRequirementValidation()
        assert hasattr(rv.__class__, "emergency_requirement")

    def test_has_address_relationship(self):
        rv = EmergencyRequirementValidation()
        assert hasattr(rv.__class__, "address")

    def test_has_identity_relationship(self):
        rv = EmergencyRequirementValidation()
        assert hasattr(rv.__class__, "identity")

    def test_maps_to_correct_type(self):
        assert EmergencyRequirementValidation.Meta.type == "emergency_requirement_validations"

    def test_repository_path(self, client):
        repo = client.emergency_requirement_validations()
        assert repo._path == "emergency_requirement_validations"

    @my_vcr.use_cassette("emergency_requirement_validations/create.yaml")
    def test_create_returns_resource_on_201(self, client):
        rv = EmergencyRequirementValidation()
        rv.emergency_requirement = EmergencyRequirement.build("c1d2e3f4-a5b6-7890-1234-567890abcdef")
        rv.address = Address.build("a1b2c3d4-e5f6-7890-1234-567890abcdef")
        rv.identity = Identity.build("b2c3d4e5-f6a7-8901-2345-67890abcdef1")
        result = client.emergency_requirement_validations().create(rv)
        assert result.data.id == "c1d2e3f4-a5b6-7890-1234-567890abcdef"
        assert result.data.type == "emergency_requirement_validations"
