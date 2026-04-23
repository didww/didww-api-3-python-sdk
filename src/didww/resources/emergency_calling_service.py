from didww.enums import EmergencyCallingServiceStatus
from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, EnumAttributeField, RelationField, ReadOnlyRepository


class EmergencyCallingService(DidwwApiModel):
    """Emergency Calling Service subscription resource.

    Attributes:
        name (str): Human-readable name for the calling service subscription.
        reference (str): Server-assigned reference code.
        status (EmergencyCallingServiceStatus): One of active, canceled,
            changes_required, in_process, new, pending_update.
        activated_at (datetime): Timestamp when the service became active. None while pending.
        canceled_at (datetime): Timestamp when the service was canceled. None when active.
        created_at (datetime): Timestamp when the resource was created.
        renew_date (str): Next renewal date as date-only string (e.g. "2026-05-22"). None when canceled.

    Resource-level meta: setup_price, monthly_price
    """

    name = SafeAttributeField("name")
    reference = SafeAttributeField("reference")
    status = EnumAttributeField("status", EmergencyCallingServiceStatus)
    activated_at = DatetimeAttributeField("activated_at")
    canceled_at = DatetimeAttributeField("canceled_at")
    created_at = DatetimeAttributeField("created_at")
    renew_date = SafeAttributeField("renew_date")

    country = RelationField("country")
    did_group_type = RelationField("did_group_type")
    order = RelationField("order")
    address = RelationField("address")
    emergency_requirement = RelationField("emergency_requirement")
    emergency_verification = RelationField("emergency_verification")
    dids = RelationField("dids")

    class Meta:
        type = "emergency_calling_services"

    @property
    def is_active(self):
        return self.status == EmergencyCallingServiceStatus.ACTIVE

    @property
    def is_canceled(self):
        return self.status == EmergencyCallingServiceStatus.CANCELED

    @property
    def is_changes_required(self):
        return self.status == EmergencyCallingServiceStatus.CHANGES_REQUIRED

    @property
    def is_in_process(self):
        return self.status == EmergencyCallingServiceStatus.IN_PROCESS

    @property
    def is_new(self):
        return self.status == EmergencyCallingServiceStatus.NEW

    @property
    def is_pending_update(self):
        return self.status == EmergencyCallingServiceStatus.PENDING_UPDATE


class EmergencyCallingServiceRepository(ReadOnlyRepository):
    _resource_class = EmergencyCallingService
    _path = "emergency_calling_services"

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
