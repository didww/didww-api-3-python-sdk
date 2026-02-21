from didww.resources.base import BaseResource, ReadOnlyRepository


class Region(BaseResource):
    _type = "regions"

    @property
    def name(self):
        return self._attr("name")

    @property
    def iso(self):
        return self._attr("iso")

    def country(self):
        return self._get_relationship("country")


class RegionRepository(ReadOnlyRepository):
    _resource_class = Region
    _path = "regions"
