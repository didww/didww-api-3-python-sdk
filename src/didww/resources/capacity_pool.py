from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository


class CapacityPool(DidwwApiModel):
    _writable_attrs = {"total_channels_count"}

    name = SafeAttributeField("name")
    renew_date = SafeAttributeField("renew_date")
    total_channels_count = SafeAttributeField("total_channels_count")
    assigned_channels_count = SafeAttributeField("assigned_channels_count")
    minimum_limit = SafeAttributeField("minimum_limit")
    minimum_qty_per_order = SafeAttributeField("minimum_qty_per_order")
    setup_price = SafeAttributeField("setup_price")
    monthly_price = SafeAttributeField("monthly_price")
    metered_rate = SafeAttributeField("metered_rate")

    countries = RelationField("countries")
    shared_capacity_groups = RelationField("shared_capacity_groups")
    qty_based_pricings = RelationField("qty_based_pricings")

    class Meta:
        type = "capacity_pools"


class CapacityPoolRepository(Repository):
    _resource_class = CapacityPool
    _path = "capacity_pools"
