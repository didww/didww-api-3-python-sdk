from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, ExclusiveRelationField, Repository

class Did(DidwwApiModel):
    """DID (phone number) resource.

    ``voice_in_trunk`` / ``voice_in_trunk_group`` and ``sms_trunk`` /
    ``sms_trunk_group`` are exclusive pairs: assigning one unassigns the
    other, and assigning ``None`` unassigns only that relationship.
    """

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
    created_at = DatetimeAttributeField("created_at")
    expires_at = DatetimeAttributeField("expires_at")
    channels_included_count = SafeAttributeField("channels_included_count")
    billing_cycles_count = SafeAttributeField("billing_cycles_count")
    dedicated_channels_count = SafeAttributeField("dedicated_channels_count")
    emergency_enabled = SafeAttributeField("emergency_enabled")
    order = RelationField("order")
    did_group = RelationField("did_group")
    voice_in_trunk = ExclusiveRelationField("voice_in_trunk", excludes="voice_in_trunk_group")
    voice_in_trunk_group = ExclusiveRelationField("voice_in_trunk_group", excludes="voice_in_trunk")
    sms_trunk = ExclusiveRelationField("sms_trunk", excludes="sms_trunk_group")
    sms_trunk_group = ExclusiveRelationField("sms_trunk_group", excludes="sms_trunk")
    capacity_pool = RelationField("capacity_pool")
    shared_capacity_group = RelationField("shared_capacity_group")
    address_verification = RelationField("address_verification")
    emergency_calling_service = RelationField("emergency_calling_service")
    emergency_verification = RelationField("emergency_verification")
    identity = RelationField("identity")

    class Meta:
        type = "dids"


class DidRepository(Repository):
    _resource_class = Did
    _path = "dids"
