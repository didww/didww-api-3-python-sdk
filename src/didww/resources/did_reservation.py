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
