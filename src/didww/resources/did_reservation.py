from didww.resources.base import BaseResource, Repository


class DidReservation(BaseResource):
    _type = "did_reservations"
    _writable_attrs = {"description"}

    @property
    def expire_at(self):
        return self._attr("expire_at")

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def description(self):
        return self._attr("description")

    @description.setter
    def description(self, value):
        self._set_attr("description", value)

    def set_available_did(self, available_did):
        self._set_relationship("available_did", available_did)


class DidReservationRepository(Repository):
    _resource_class = DidReservation
    _path = "did_reservations"
