from didww.enums import NumberType
from didww.resources.base import DidwwApiModel, SafeAttributeField, EnumAttributeField, RelationField, ReadOnlyRepository


class EmergencyRequirement(DidwwApiModel):
    """Emergency requirement resource.

    personal_area_level and business_area_level are None when the country does not
    accept that kind of identity for emergency calling.

    Resource-level meta: setup_price, monthly_price (decimal strings)
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
    number_type = EnumAttributeField("number_type", NumberType)

    country = RelationField("country")

    class Meta:
        type = "emergency_requirements"


class EmergencyRequirementRepository(ReadOnlyRepository):
    _resource_class = EmergencyRequirement
    _path = "emergency_requirements"
