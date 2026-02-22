from didww.exceptions import DidwwApiError
from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository


class DidReservation(DidwwApiModel):
    _writable_attrs = {"description"}

    expire_at = SafeAttributeField("expire_at")
    created_at = SafeAttributeField("created_at")
    description = SafeAttributeField("description")

    available_did = RelationField("available_did")

    class Meta:
        type = "did_reservations"


class DidReservationRepository(Repository):
    _resource_class = DidReservation
    _path = "did_reservations"

    def delete(self, resource_id):
        try:
            self.client.delete(f"{self._path}/{resource_id}")
        except DidwwApiError as e:
            if e.status_code != 404:
                raise
