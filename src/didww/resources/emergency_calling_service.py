from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, ReadOnlyRepository


class EmergencyCallingService(DidwwApiModel):
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
