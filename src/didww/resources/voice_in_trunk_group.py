from didww.resources.base import BaseResource, Repository


class VoiceInTrunkGroup(BaseResource):
    _type = "voice_in_trunk_groups"
    _writable_attrs = {"capacity_limit", "name"}

    @property
    def name(self):
        return self._attr("name")

    @name.setter
    def name(self, value):
        self._set_attr("name", value)

    @property
    def capacity_limit(self):
        return self._attr("capacity_limit")

    @capacity_limit.setter
    def capacity_limit(self, value):
        self._set_attr("capacity_limit", value)

    @property
    def created_at(self):
        return self._attr("created_at")

    def set_voice_in_trunks(self, trunks):
        self._set_relationships("voice_in_trunks", trunks)


class VoiceInTrunkGroupRepository(Repository):
    _resource_class = VoiceInTrunkGroup
    _path = "voice_in_trunk_groups"
