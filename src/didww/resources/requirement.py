from didww.enums import IdentityType, AreaLevel
from didww.resources.base import DidwwApiModel, SafeAttributeField, EnumAttributeField, RelationField, ReadOnlyRepository


class Requirement(DidwwApiModel):
    identity_type = EnumAttributeField("identity_type", IdentityType)
    personal_area_level = EnumAttributeField("personal_area_level", AreaLevel)
    business_area_level = EnumAttributeField("business_area_level", AreaLevel)
    address_area_level = EnumAttributeField("address_area_level", AreaLevel)
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


class RequirementRepository(ReadOnlyRepository):
    _resource_class = Requirement
    _path = "requirements"
