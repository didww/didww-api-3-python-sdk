from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class Area(DidwwApiModel):
    name = SafeAttributeField("name")

    country = RelationField("country")

    class Meta:
        type = "areas"


class AreaRepository(ReadOnlyRepository):
    _resource_class = Area
    _path = "areas"
