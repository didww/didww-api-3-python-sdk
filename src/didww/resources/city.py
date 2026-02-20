from didww.resources.base import BaseResource, ReadOnlyRepository


class City(BaseResource):
    _type = "cities"

    @property
    def name(self):
        return self._attr("name")

    def area_id(self):
        return self._relationship_id("area")


class CityRepository(ReadOnlyRepository):
    _resource_class = City
    _path = "cities"
