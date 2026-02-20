from didww.resources.base import BaseResource, ReadOnlyRepository


class DidGroupType(BaseResource):
    _type = "did_group_types"

    @property
    def name(self):
        return self._attr("name")


class DidGroupTypeRepository(ReadOnlyRepository):
    _resource_class = DidGroupType
    _path = "did_group_types"
