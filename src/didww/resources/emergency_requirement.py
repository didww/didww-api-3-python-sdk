from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class EmergencyRequirement(DidwwApiModel):
    """Emergency requirement resource.

    Resource-level meta: setup_price, monthly_price
    """

    identity_type = SafeAttributeField("identity_type")
    address_area_level = SafeAttributeField("address_area_level")
    personal_area_level = SafeAttributeField("personal_area_level")
    business_area_level = SafeAttributeField("business_area_level")
    address_mandatory_fields = SafeAttributeField("address_mandatory_fields")
    personal_mandatory_fields = SafeAttributeField("personal_mandatory_fields")
    business_mandatory_fields = SafeAttributeField("business_mandatory_fields")
    estimate_setup_time = SafeAttributeField("estimate_setup_time")
    requirement_restriction_message = SafeAttributeField("requirement_restriction_message")

    country = RelationField("country")
    did_group_type = RelationField("did_group_type")

    class Meta:
        type = "emergency_requirements"


class EmergencyRequirementRepository(ReadOnlyRepository):
    _resource_class = EmergencyRequirement
    _path = "emergency_requirements"
