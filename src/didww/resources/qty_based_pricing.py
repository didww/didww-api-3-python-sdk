from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class QtyBasedPricing(DidwwApiModel):
    qty = SafeAttributeField("qty")
    setup_price = SafeAttributeField("setup_price")
    monthly_price = SafeAttributeField("monthly_price")

    class Meta:
        type = "qty_based_pricings"


class QtyBasedPricingRepository(ReadOnlyRepository):
    _resource_class = QtyBasedPricing
    _path = "qty_based_pricings"
