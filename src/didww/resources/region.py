from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class Region(DidwwApiModel):
    name = SafeAttributeField("name")
    iso = SafeAttributeField("iso")

    country = RelationField("country")

    class Meta:
        type = "regions"


class RegionRepository(ReadOnlyRepository):
    _resource_class = Region
    _path = "regions"
