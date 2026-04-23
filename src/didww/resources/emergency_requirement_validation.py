from didww.resources.base import DidwwApiModel, RelationField, CreateOnlyRepository


class EmergencyRequirementValidation(DidwwApiModel):
    _writable_attrs = set()

    emergency_requirement = RelationField("emergency_requirement")
    address = RelationField("address")
    identity = RelationField("identity")

    class Meta:
        type = "emergency_requirement_validations"


class EmergencyRequirementValidationRepository(CreateOnlyRepository):
    _resource_class = EmergencyRequirementValidation
    _path = "emergency_requirement_validations"
