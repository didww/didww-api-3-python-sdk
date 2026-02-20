from didww.resources.base import BaseResource, CreateOnlyRepository


class RequirementValidation(BaseResource):
    _type = "requirement_validations"
    _writable_attrs = set()

    def set_requirement(self, requirement_id):
        self._set_relationship("requirement", "requirements", requirement_id)

    def set_identity(self, identity_id):
        self._set_relationship("identity", "identities", identity_id)

    def set_address(self, address_id):
        self._set_relationship("address", "addresses", address_id)


class RequirementValidationRepository(CreateOnlyRepository):
    _resource_class = RequirementValidation
    _path = "requirement_validations"
