from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, CreateOnlyRepository


class AddressVerification(DidwwApiModel):
    _writable_attrs = {"service_description", "callback_url", "callback_method"}

    status = SafeAttributeField("status")
    callback_url = SafeAttributeField("callback_url")
    callback_method = SafeAttributeField("callback_method")
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
