from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository


class SharedCapacityGroup(DidwwApiModel):
    _writable_attrs = {"name", "shared_channels_count", "metered_channels_count"}

    name = SafeAttributeField("name")
    shared_channels_count = SafeAttributeField("shared_channels_count")
    metered_channels_count = SafeAttributeField("metered_channels_count")
    created_at = SafeAttributeField("created_at")

    capacity_pool = RelationField("capacity_pool")
    dids = RelationField("dids")

    class Meta:
        type = "shared_capacity_groups"


class SharedCapacityGroupRepository(Repository):
    _resource_class = SharedCapacityGroup
    _path = "shared_capacity_groups"
