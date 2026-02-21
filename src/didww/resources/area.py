from didww.resources.base import BaseResource, ReadOnlyRepository


class Area(BaseResource):
    _type = "areas"

    @property
    def name(self):
        return self._attr("name")

    def country(self):
        return self._get_relationship("country")


class AreaRepository(ReadOnlyRepository):
    _resource_class = Area
    _path = "areas"
