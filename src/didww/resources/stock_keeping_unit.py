from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class StockKeepingUnit(DidwwApiModel):
    setup_price = SafeAttributeField("setup_price")
    monthly_price = SafeAttributeField("monthly_price")
    channels_included_count = SafeAttributeField("channels_included_count")

    class Meta:
        type = "stock_keeping_units"


class StockKeepingUnitRepository(ReadOnlyRepository):
    _resource_class = StockKeepingUnit
    _path = "stock_keeping_units"
