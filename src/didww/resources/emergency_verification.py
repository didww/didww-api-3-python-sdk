from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, Repository


class EmergencyVerification(DidwwApiModel):
    _writable_attrs = {"callback_url", "callback_method", "external_reference_id"}

    reference = SafeAttributeField("reference")
    status = SafeAttributeField("status")
    reject_reasons = SafeAttributeField("reject_reasons")
    reject_comment = SafeAttributeField("reject_comment")
    callback_url = SafeAttributeField("callback_url")
    callback_method = SafeAttributeField("callback_method")
    external_reference_id = SafeAttributeField("external_reference_id")
    created_at = DatetimeAttributeField("created_at")

    address = RelationField("address")
    emergency_calling_service = RelationField("emergency_calling_service")
    dids = RelationField("dids")

    class Meta:
        type = "emergency_verifications"


class EmergencyVerificationRepository(Repository):
    _resource_class = EmergencyVerification
    _path = "emergency_verifications"
