from didww.resources.base import BaseResource, Repository


class CapacityPool(BaseResource):
    _type = "capacity_pools"
    _writable_attrs = {"total_channels_count"}

    @property
    def name(self):
        return self._attr("name")

    @property
    def renew_date(self):
        return self._attr("renew_date")

    @property
    def total_channels_count(self):
        return self._attr("total_channels_count")

    @total_channels_count.setter
    def total_channels_count(self, value):
        self._set_attr("total_channels_count", value)

    @property
    def assigned_channels_count(self):
        return self._attr("assigned_channels_count")

    @property
    def minimum_limit(self):
        return self._attr("minimum_limit")

    @property
    def minimum_qty_per_order(self):
        return self._attr("minimum_qty_per_order")

    @property
    def setup_price(self):
        return self._attr("setup_price")

    @property
    def monthly_price(self):
        return self._attr("monthly_price")

    @property
    def metered_rate(self):
        return self._attr("metered_rate")


class CapacityPoolRepository(Repository):
    _resource_class = CapacityPool
    _path = "capacity_pools"
