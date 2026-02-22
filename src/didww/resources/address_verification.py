from didww.enums import AddressVerificationStatus, CallbackMethod
from didww.resources.base import DidwwApiModel, SafeAttributeField, EnumAttributeField, RelationField, CreateOnlyRepository


class AddressVerification(DidwwApiModel):
    _writable_attrs = {"service_description", "callback_url", "callback_method"}

    status = EnumAttributeField("status", AddressVerificationStatus)
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    service_description = SafeAttributeField("service_description")
    reject_reasons = SafeAttributeField("reject_reasons")
    reference = SafeAttributeField("reference")
    created_at = SafeAttributeField("created_at")

    address = RelationField("address")
    dids = RelationField("dids")

    class Meta:
        type = "address_verifications"


class AddressVerificationRepository(CreateOnlyRepository):
    _resource_class = AddressVerification
    _path = "address_verifications"
