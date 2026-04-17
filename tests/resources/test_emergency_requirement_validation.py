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
    def test_create_returns_none_on_204(self, client):
        rv = EmergencyRequirementValidation()
        rv.emergency_requirement = EmergencyRequirement.build("er-001")
        rv.address = Address.build("addr-001")
        rv.identity = Identity.build("id-001")
        result = client.emergency_requirement_validations().create(rv)
        assert result is None
