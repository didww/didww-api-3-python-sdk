from didww.enums import Feature
from didww.resources.base import DidwwApiModel, EnumListAttributeField, SafeAttributeField, RelationField, ReadOnlyRepository


class DidGroup(DidwwApiModel):
    prefix = SafeAttributeField("prefix")
    features = EnumListAttributeField("features", Feature)
    is_metered = SafeAttributeField("is_metered")
    area_name = SafeAttributeField("area_name")
    allow_additional_channels = SafeAttributeField("allow_additional_channels")

    country = RelationField("country")
    region = RelationField("region")
    city = RelationField("city")
    did_group_type = RelationField("did_group_type")
    stock_keeping_units = RelationField("stock_keeping_units")

    class Meta:
        type = "did_groups"

    def requirement_id(self):
        return self._relationship_id("requirement")


class DidGroupRepository(ReadOnlyRepository):
    _resource_class = DidGroup
    _path = "did_groups"
