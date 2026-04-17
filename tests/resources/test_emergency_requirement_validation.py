from didww.resources.emergency_requirement_validation import EmergencyRequirementValidation


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
