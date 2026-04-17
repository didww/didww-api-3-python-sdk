from didww.enums import AddressVerificationStatus, CallbackMethod
from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, EnumAttributeField, RelationField, CreateOnlyRepository


class AddressVerification(DidwwApiModel):
    _writable_attrs = {"service_description", "callback_url", "callback_method", "external_reference_id"}

    status = EnumAttributeField("status", AddressVerificationStatus)
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    service_description = SafeAttributeField("service_description")
    reject_reasons = SafeAttributeField("reject_reasons")
    reject_comment = SafeAttributeField("reject_comment")
    reference = SafeAttributeField("reference")
    external_reference_id = SafeAttributeField("external_reference_id")
    created_at = DatetimeAttributeField("created_at")

    address = RelationField("address")
    dids = RelationField("dids")

    class Meta:
        type = "address_verifications"


class AddressVerificationRepository(CreateOnlyRepository):
    _resource_class = AddressVerification
    _path = "address_verifications"
