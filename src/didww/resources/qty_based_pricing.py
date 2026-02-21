from didww.resources.base import BaseResource, ReadOnlyRepository


class QtyBasedPricing(BaseResource):
    _type = "qty_based_pricings"

    @property
    def qty(self):
        return self._attr("qty")

    @property
    def setup_price(self):
        return self._attr("setup_price")

    @property
    def monthly_price(self):
        return self._attr("monthly_price")


class QtyBasedPricingRepository(ReadOnlyRepository):
    _resource_class = QtyBasedPricing
    _path = "qty_based_pricings"
