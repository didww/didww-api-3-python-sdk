from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, Repository


class VoiceInTrunkGroup(DidwwApiModel):
    _writable_attrs = {"capacity_limit", "name", "external_reference_id"}

    name = SafeAttributeField("name")
    capacity_limit = SafeAttributeField("capacity_limit")
    created_at = DatetimeAttributeField("created_at")
    external_reference_id = SafeAttributeField("external_reference_id")

    voice_in_trunks = RelationField("voice_in_trunks")

    class Meta:
        type = "voice_in_trunk_groups"


class VoiceInTrunkGroupRepository(Repository):
    _resource_class = VoiceInTrunkGroup
    _path = "voice_in_trunk_groups"
