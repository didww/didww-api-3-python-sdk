from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository

class Did(DidwwApiModel):
    _writable_attrs = {
        "billing_cycles_count", "capacity_limit", "description",
        "terminated", "dedicated_channels_count",
    }

    number = SafeAttributeField("number")
    blocked = SafeAttributeField("blocked")
    capacity_limit = SafeAttributeField("capacity_limit")
    description = SafeAttributeField("description")
    terminated = SafeAttributeField("terminated")
    awaiting_registration = SafeAttributeField("awaiting_registration")
    created_at = SafeAttributeField("created_at")
    expires_at = SafeAttributeField("expires_at")
    channels_included_count = SafeAttributeField("channels_included_count")
    billing_cycles_count = SafeAttributeField("billing_cycles_count")
    dedicated_channels_count = SafeAttributeField("dedicated_channels_count")
    order = RelationField("order")
    did_group = RelationField("did_group")
    voice_in_trunk = RelationField("voice_in_trunk")
    voice_in_trunk_group = RelationField("voice_in_trunk_group")
    capacity_pool = RelationField("capacity_pool")
    shared_capacity_group = RelationField("shared_capacity_group")
    address_verification = RelationField("address_verification")

    class Meta:
        type = "dids"

    def set_voice_in_trunk(self, trunk):
        self.voice_in_trunk = trunk
        self._null_relationship("voice_in_trunk_group")

    def set_voice_in_trunk_group(self, group):
        self.voice_in_trunk_group = group
        self._null_relationship("voice_in_trunk")


class DidRepository(Repository):
    _resource_class = Did
    _path = "dids"
