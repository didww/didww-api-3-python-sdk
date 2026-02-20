from didww.resources.base import BaseResource, ReadOnlyRepository


class Pop(BaseResource):
    _type = "pops"

    @property
    def name(self):
        return self._attr("name")


class PopRepository(ReadOnlyRepository):
    _resource_class = Pop
    _path = "pops"
