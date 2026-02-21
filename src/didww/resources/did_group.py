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

    def country(self):
        return self._get_relationship("country")

    def region(self):
        return self._get_relationship("region")

    def city(self):
        return self._get_relationship("city")

    def did_group_type(self):
        return self._get_relationship("did_group_type")

    def stock_keeping_units(self):
        return self._get_relationships("stock_keeping_units")


class DidGroupRepository(ReadOnlyRepository):
    _resource_class = DidGroup
    _path = "did_groups"
