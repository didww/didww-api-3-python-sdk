from didww.resources.base import BaseResource, ReadOnlyRepository


class AvailableDid(BaseResource):
    _type = "available_dids"

    @property
    def number(self):
        return self._attr("number")

    def nanpa_prefix_id(self):
        return self._relationship_id("nanpa_prefix")


class AvailableDidRepository(ReadOnlyRepository):
    _resource_class = AvailableDid
    _path = "available_dids"
