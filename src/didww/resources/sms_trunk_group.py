from didww.resources.base import (
    DidwwApiModel,
    DatetimeAttributeField,
    SafeAttributeField,
    RelationField,
    ReadOnlyRelationField,
    Repository,
)


class SmsTrunkGroup(DidwwApiModel):
    """SMS trunk group resource.

    ``sms_trunks`` replaces the whole membership; an empty list (or None)
    removes every trunk. ``http_out`` trunks cannot join a group. Deleting a
    group also deletes its trunks. ``incoming_dids`` is read-only.

    Resource-level meta: sms_trunks_count (also as ``group.sms_trunks_count``).
    """

    _writable_attrs = {"name", "external_reference_id"}

    name = SafeAttributeField("name")
    external_reference_id = SafeAttributeField("external_reference_id")
    created_at = DatetimeAttributeField("created_at")
    updated_at = DatetimeAttributeField("updated_at")

    sms_trunks = RelationField("sms_trunks", many=True)
    incoming_dids = ReadOnlyRelationField("incoming_dids")

    class Meta:
        type = "sms_trunk_groups"

    @property
    def sms_trunks_count(self):
        return self.meta.get("sms_trunks_count")


class SmsTrunkGroupRepository(Repository):
    _resource_class = SmsTrunkGroup
    _path = "sms_trunk_groups"
