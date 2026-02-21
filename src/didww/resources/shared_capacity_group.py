from didww.resources.base import BaseResource, Repository


class SharedCapacityGroup(BaseResource):
    _type = "shared_capacity_groups"
    _writable_attrs = {"name", "shared_channels_count", "metered_channels_count"}

    @property
    def name(self):
        return self._attr("name")

    @name.setter
    def name(self, value):
        self._set_attr("name", value)

    @property
    def shared_channels_count(self):
        return self._attr("shared_channels_count")

    @shared_channels_count.setter
    def shared_channels_count(self, value):
        self._set_attr("shared_channels_count", value)

    @property
    def metered_channels_count(self):
        return self._attr("metered_channels_count")

    @metered_channels_count.setter
    def metered_channels_count(self, value):
        self._set_attr("metered_channels_count", value)

    @property
    def created_at(self):
        return self._attr("created_at")

    def set_capacity_pool(self, capacity_pool_id):
        self._set_relationship("capacity_pool", "capacity_pools", capacity_pool_id)

    def set_dids(self, did_ids):
        self._relationships["dids"] = {
            "data": [{"type": "dids", "id": did_id} for did_id in did_ids]
        }


class SharedCapacityGroupRepository(Repository):
    _resource_class = SharedCapacityGroup
    _path = "shared_capacity_groups"
