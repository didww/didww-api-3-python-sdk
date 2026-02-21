from didww.resources.base import BaseResource, ReadOnlyRepository


class StockKeepingUnit(BaseResource):
    _type = "stock_keeping_units"

    @property
    def setup_price(self):
        return self._attr("setup_price")

    @property
    def monthly_price(self):
        return self._attr("monthly_price")

    @property
    def channels_included_count(self):
        return self._attr("channels_included_count")


class StockKeepingUnitRepository(ReadOnlyRepository):
    _resource_class = StockKeepingUnit
    _path = "stock_keeping_units"
