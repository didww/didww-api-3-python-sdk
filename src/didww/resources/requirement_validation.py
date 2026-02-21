from didww.resources.base import DidwwApiModel, RelationField, CreateOnlyRepository


class RequirementValidation(DidwwApiModel):
    _writable_attrs = set()

    requirement = RelationField("requirement")
    identity = RelationField("identity")
    address = RelationField("address")

    class Meta:
        type = "requirement_validations"


class RequirementValidationRepository(CreateOnlyRepository):
    _resource_class = RequirementValidation
    _path = "requirement_validations"
