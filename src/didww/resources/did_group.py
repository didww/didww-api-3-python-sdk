from didww.resources.base import BaseResource, ReadOnlyRepository


class DidGroup(BaseResource):
    _type = "did_groups"

    @property
    def prefix(self):
        return self._attr("prefix")

    @property
    def features(self):
        return self._attr("features")

    @property
    def is_metered(self):
        return self._attr("is_metered")

    @property
    def area_name(self):
        return self._attr("area_name")

    @property
    def allow_additional_channels(self):
        return self._attr("allow_additional_channels")

    def requirement_id(self):
        return self._relationship_id("requirement")


class DidGroupRepository(ReadOnlyRepository):
    _resource_class = DidGroup
    _path = "did_groups"
