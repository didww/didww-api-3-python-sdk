from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, ReadOnlyRepository


class EmergencyCallingService(DidwwApiModel):
    """Emergency Calling Service subscription resource.

    Attributes:
        name (str): Human-readable name for the calling service subscription.
        reference (str): Server-assigned reference code.
        status (str): One of "active", "canceled", "changes required",
            "in process", "new", "pending update".
        activated_at (datetime): Timestamp when the service became active. None while pending.
        canceled_at (datetime): Timestamp when the service was canceled. None when active.
        created_at (datetime): Timestamp when the resource was created.
        renew_date (datetime): Next renewal date. None when canceled.
    """

    name = SafeAttributeField("name")
    reference = SafeAttributeField("reference")
    status = SafeAttributeField("status")
    activated_at = DatetimeAttributeField("activated_at")
    canceled_at = DatetimeAttributeField("canceled_at")
    created_at = DatetimeAttributeField("created_at")
    renew_date = DatetimeAttributeField("renew_date")

    country = RelationField("country")
    did_group_type = RelationField("did_group_type")
    order = RelationField("order")
    address = RelationField("address")
    emergency_requirement = RelationField("emergency_requirement")
    emergency_verification = RelationField("emergency_verification")
    dids = RelationField("dids")

    class Meta:
        type = "emergency_calling_services"


class EmergencyCallingServiceRepository(ReadOnlyRepository):
    _resource_class = EmergencyCallingService
    _path = "emergency_calling_services"

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
