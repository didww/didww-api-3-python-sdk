from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class City(DidwwApiModel):
    name = SafeAttributeField("name")

    country = RelationField("country")
    region = RelationField("region")
    area = RelationField("area")

    class Meta:
        type = "cities"

    def area_id(self):
        return self._relationship_id("area")


class CityRepository(ReadOnlyRepository):
    _resource_class = City
    _path = "cities"
