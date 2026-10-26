from didww.resources.base import (
    DidwwApiModel,
    DatetimeAttributeField,
    SafeAttributeField,
    RelationField,
    ReadOnlyRelationField,
    Repository,
)
from didww.resources.sms_trunk_configuration import SmsTrunkConfiguration


class SmsTrunk(DidwwApiModel):
    """SMS trunk resource.

    ``configuration`` is one of the ``SmsTrunkConfiguration`` classes. On
    update its type must match the stored one, and attributes left out keep
    their values. The configuration is a value: after ``find``, edit it and
    assign it back (``trunk.configuration = cfg``).

    ``priority`` (0-32767, default 100) must stay unset on ``http_out``
    trunks. ``outgoing_dids`` replaces the whole list; setting
    ``allow_any_did_as_source`` to True clears a loaded or assigned
    ``outgoing_dids`` list, which must stay empty while the flag is on.
    ``sms_trunk_group = None`` takes the trunk out of its group.
    ``incoming_dids`` and ``sender_id_verifications`` are read-only.

    Filters: ``id``, ``name``, ``external_reference_id``, ``configuration.type``.
    Includes: ``outgoing_dids``, ``incoming_dids``, ``sms_trunk_group``,
    ``sender_id_verifications``.

    Resource-level meta: host (``http_out`` only, also as ``trunk.host``).
    """

    _writable_attrs = {
        "name", "external_reference_id", "blocked", "priority",
        "allow_any_did_as_source", "configuration",
    }

    name = SafeAttributeField("name")
    external_reference_id = SafeAttributeField("external_reference_id")
    blocked = SafeAttributeField("blocked")
    priority = SafeAttributeField("priority")
    allow_in = SafeAttributeField("allow_in")
    allow_out = SafeAttributeField("allow_out")
    created_at = DatetimeAttributeField("created_at")
    updated_at = DatetimeAttributeField("updated_at")

    outgoing_dids = RelationField("outgoing_dids", many=True)
    sms_trunk_group = RelationField("sms_trunk_group")
    incoming_dids = ReadOnlyRelationField("incoming_dids")
    sender_id_verifications = ReadOnlyRelationField("sender_id_verifications")

    class Meta:
        type = "sms_trunks"

    @property
    def allow_any_did_as_source(self):
        return self.attributes.get("allow_any_did_as_source")

    @allow_any_did_as_source.setter
    def allow_any_did_as_source(self, value):
        self.attributes["allow_any_did_as_source"] = value
        if value is True:
            relationship = self.raw_object.relationships.get("outgoing_dids")
            if isinstance(getattr(relationship, "data", None), list):
                self.outgoing_dids = []

    @property
    def configuration(self):
        raw = self.attributes.get("configuration")
        return SmsTrunkConfiguration.from_jsonapi(raw)

    @configuration.setter
    def configuration(self, config):
        if isinstance(config, dict):
            config = SmsTrunkConfiguration.from_jsonapi(config)
        if isinstance(config, SmsTrunkConfiguration):
            config = config.to_jsonapi()
        self.attributes["configuration"] = config

    @property
    def host(self):
        return self.meta.get("host")

    def to_jsonapi(self, include_id=False, dirty_only=False):
        doc = super().to_jsonapi(include_id=include_id, dirty_only=dirty_only)
        raw = doc["attributes"].get("configuration")
        if isinstance(raw, dict):
            doc["attributes"]["configuration"] = SmsTrunkConfiguration.from_jsonapi(raw).to_jsonapi()
        return doc


class SmsTrunkRepository(Repository):
    _resource_class = SmsTrunk
    _path = "sms_trunks"
