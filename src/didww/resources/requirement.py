from didww.resources.base import BaseResource, ReadOnlyRepository


class Requirement(BaseResource):
    _type = "requirements"

    @property
    def identity_type(self):
        return self._attr("identity_type")

    @property
    def personal_area_level(self):
        return self._attr("personal_area_level")

    @property
    def business_area_level(self):
        return self._attr("business_area_level")

    @property
    def address_area_level(self):
        return self._attr("address_area_level")

    @property
    def personal_proof_qty(self):
        return self._attr("personal_proof_qty")

    @property
    def business_proof_qty(self):
        return self._attr("business_proof_qty")

    @property
    def address_proof_qty(self):
        return self._attr("address_proof_qty")

    @property
    def service_description_required(self):
        return self._attr("service_description_required")

    @property
    def restriction_message(self):
        return self._attr("restriction_message")


class RequirementRepository(ReadOnlyRepository):
    _resource_class = Requirement
    _path = "requirements"
