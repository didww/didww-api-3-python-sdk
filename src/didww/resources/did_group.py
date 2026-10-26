from didww.enums import Feature, NumberType
from didww.resources.base import DidwwApiModel, EnumAttributeField, EnumListAttributeField, SafeAttributeField, RelationField, ReadOnlyRepository


class DidGroup(DidwwApiModel):
    prefix = SafeAttributeField("prefix")
    features = EnumListAttributeField("features", Feature)
    is_metered = SafeAttributeField("is_metered")
    is_demo = SafeAttributeField("is_demo")
    area_name = SafeAttributeField("area_name")
    allow_additional_channels = SafeAttributeField("allow_additional_channels")
    service_restrictions = SafeAttributeField("service_restrictions")
    number_type = EnumAttributeField("number_type", NumberType)

    country = RelationField("country")
    region = RelationField("region")
    city = RelationField("city")
    stock_keeping_units = RelationField("stock_keeping_units")
    address_requirement = RelationField("address_requirement")

    class Meta:
        type = "did_groups"


class DidGroupRepository(ReadOnlyRepository):
    _resource_class = DidGroup
    _path = "did_groups"
