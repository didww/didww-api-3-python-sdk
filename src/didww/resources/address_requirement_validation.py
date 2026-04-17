from didww.resources.base import DidwwApiModel, RelationField, CreateOnlyRepository


class AddressRequirementValidation(DidwwApiModel):
    _writable_attrs = set()

    address_requirement = RelationField("address_requirement")
    identity = RelationField("identity")
    address = RelationField("address")

    class Meta:
        type = "address_requirement_validations"


class AddressRequirementValidationRepository(CreateOnlyRepository):
    _resource_class = AddressRequirementValidation
    _path = "address_requirement_validations"
