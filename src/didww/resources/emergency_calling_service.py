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

    STATUS_ACTIVE = "active"
    STATUS_CANCELED = "canceled"
    STATUS_CHANGES_REQUIRED = "changes required"
    STATUS_IN_PROCESS = "in process"
    STATUS_NEW = "new"
    STATUS_PENDING_UPDATE = "pending update"

    class Meta:
        type = "emergency_calling_services"

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def is_canceled(self):
        return self.status == self.STATUS_CANCELED

    @property
    def is_changes_required(self):
        return self.status == self.STATUS_CHANGES_REQUIRED

    @property
    def is_in_process(self):
        return self.status == self.STATUS_IN_PROCESS

    @property
    def is_new(self):
        return self.status == self.STATUS_NEW

    @property
    def is_pending_update(self):
        return self.status == self.STATUS_PENDING_UPDATE


class EmergencyCallingServiceRepository(ReadOnlyRepository):
    _resource_class = EmergencyCallingService
    _path = "emergency_calling_services"

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
