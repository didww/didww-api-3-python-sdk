from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, Repository


class SharedCapacityGroup(DidwwApiModel):
    _writable_attrs = {"name", "shared_channels_count", "metered_channels_count", "external_reference_id"}

    name = SafeAttributeField("name")
    shared_channels_count = SafeAttributeField("shared_channels_count")
    metered_channels_count = SafeAttributeField("metered_channels_count")
    created_at = DatetimeAttributeField("created_at")
    external_reference_id = SafeAttributeField("external_reference_id")

    capacity_pool = RelationField("capacity_pool")
    dids = RelationField("dids")

    class Meta:
        type = "shared_capacity_groups"


class SharedCapacityGroupRepository(Repository):
    _resource_class = SharedCapacityGroup
    _path = "shared_capacity_groups"
