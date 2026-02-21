from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class Requirement(DidwwApiModel):
    identity_type = SafeAttributeField("identity_type")
    personal_area_level = SafeAttributeField("personal_area_level")
    business_area_level = SafeAttributeField("business_area_level")
    address_area_level = SafeAttributeField("address_area_level")
    personal_proof_qty = SafeAttributeField("personal_proof_qty")
    business_proof_qty = SafeAttributeField("business_proof_qty")
    address_proof_qty = SafeAttributeField("address_proof_qty")
    personal_mandatory_fields = SafeAttributeField("personal_mandatory_fields")
    business_mandatory_fields = SafeAttributeField("business_mandatory_fields")
    service_description_required = SafeAttributeField("service_description_required")
    restriction_message = SafeAttributeField("restriction_message")

    country = RelationField("country")
    did_group_type = RelationField("did_group_type")
    personal_permanent_document = RelationField("personal_permanent_document")
    business_permanent_document = RelationField("business_permanent_document")
    personal_onetime_document = RelationField("personal_onetime_document")
    business_onetime_document = RelationField("business_onetime_document")
    personal_proof_types = RelationField("personal_proof_types")
    business_proof_types = RelationField("business_proof_types")
    address_proof_types = RelationField("address_proof_types")

    class Meta:
        type = "requirements"

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


class RequirementRepository(ReadOnlyRepository):
    _resource_class = Requirement
    _path = "requirements"
