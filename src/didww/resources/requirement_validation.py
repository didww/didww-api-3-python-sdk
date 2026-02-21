from didww.resources.base import BaseResource, CreateOnlyRepository


class RequirementValidation(BaseResource):
    _type = "requirement_validations"
    _writable_attrs = set()

    def set_requirement(self, requirement):
        self._set_relationship("requirement", requirement)

    def set_identity(self, identity):
        self._set_relationship("identity", identity)

    def set_address(self, address):
        self._set_relationship("address", address)


class RequirementValidationRepository(CreateOnlyRepository):
    _resource_class = RequirementValidation
    _path = "requirement_validations"
