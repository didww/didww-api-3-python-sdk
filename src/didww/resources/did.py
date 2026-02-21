from didww.resources.base import BaseResource, Repository


class Did(BaseResource):
    _type = "dids"
    _writable_attrs = {"billing_cycles_count", "capacity_limit", "description", "terminated", "dedicated_channels_count", "pending_removal"}

    @property
    def number(self):
        return self._attr("number")

    @property
    def blocked(self):
        return self._attr("blocked")

    @property
    def capacity_limit(self):
        return self._attr("capacity_limit")

    @capacity_limit.setter
    def capacity_limit(self, value):
        self._set_attr("capacity_limit", value)

    @property
    def description(self):
        return self._attr("description")

    @description.setter
    def description(self, value):
        self._set_attr("description", value)

    @property
    def terminated(self):
        return self._attr("terminated")

    @property
    def awaiting_registration(self):
        return self._attr("awaiting_registration")

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def expires_at(self):
        return self._attr("expires_at")

    @property
    def channels_included_count(self):
        return self._attr("channels_included_count")

    @property
    def billing_cycles_count(self):
        return self._attr("billing_cycles_count")

    @billing_cycles_count.setter
    def billing_cycles_count(self, value):
        self._set_attr("billing_cycles_count", value)

    @property
    def pending_removal(self):
        return self._attr("pending_removal")

    @property
    def dedicated_channels_count(self):
        return self._attr("dedicated_channels_count")

    def set_voice_in_trunk(self, trunk_id):
        self._set_relationship("voice_in_trunk", "voice_in_trunks", trunk_id)

    def set_voice_in_trunk_group(self, group_id):
        self._set_relationship("voice_in_trunk_group", "voice_in_trunk_groups", group_id)

    def set_capacity_pool(self, pool_id):
        self._set_relationship("capacity_pool", "capacity_pools", pool_id)

    def set_shared_capacity_group(self, group_id):
        self._set_relationship("shared_capacity_group", "shared_capacity_groups", group_id)

    def set_address_verification(self, av_id):
        self._set_relationship("address_verification", "address_verifications", av_id)


class DidRepository(Repository):
    _resource_class = Did
    _path = "dids"
