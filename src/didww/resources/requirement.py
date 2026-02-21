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
    def personal_mandatory_fields(self):
        return self._attr("personal_mandatory_fields")

    @property
    def business_mandatory_fields(self):
        return self._attr("business_mandatory_fields")

    @property
    def service_description_required(self):
        return self._attr("service_description_required")

    @property
    def restriction_message(self):
        return self._attr("restriction_message")

    def country_id(self):
        return self._relationship_id("country")

    def did_group_type_id(self):
        return self._relationship_id("did_group_type")

    def personal_permanent_document_id(self):
        return self._relationship_id("personal_permanent_document")

    def business_permanent_document_id(self):
        return self._relationship_id("business_permanent_document")

    def personal_onetime_document_id(self):
        return self._relationship_id("personal_onetime_document")

    def business_onetime_document_id(self):
        return self._relationship_id("business_onetime_document")

    def personal_proof_type_ids(self):
        return self._relationship_ids("personal_proof_types")

    def business_proof_type_ids(self):
        return self._relationship_ids("business_proof_types")

    def address_proof_type_ids(self):
        return self._relationship_ids("address_proof_types")

    def country(self):
        return self._get_relationship("country")

    def did_group_type(self):
        return self._get_relationship("did_group_type")

    def personal_permanent_document(self):
        return self._get_relationship("personal_permanent_document")

    def business_permanent_document(self):
        return self._get_relationship("business_permanent_document")

    def personal_onetime_document(self):
        return self._get_relationship("personal_onetime_document")

    def business_onetime_document(self):
        return self._get_relationship("business_onetime_document")

    def personal_proof_types(self):
        return self._get_relationships("personal_proof_types")

    def business_proof_types(self):
        return self._get_relationships("business_proof_types")

    def address_proof_types(self):
        return self._get_relationships("address_proof_types")


class RequirementRepository(ReadOnlyRepository):
    _resource_class = Requirement
    _path = "requirements"
