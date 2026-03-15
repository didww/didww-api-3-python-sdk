from didww.enums import AddressVerificationStatus, CallbackMethod
from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, EnumAttributeField, RelationField, CreateOnlyRepository


class _SplitSemicolonField(SafeAttributeField):
    """Splits a '; '-delimited (semicolon + space) string into a list."""

    def __get__(self, instance, type=None):
        value = super().__get__(instance, type)
        if value is None:
            return None
        return value.split('; ')


class AddressVerification(DidwwApiModel):
    _writable_attrs = {"service_description", "callback_url", "callback_method"}

    status = EnumAttributeField("status", AddressVerificationStatus)
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    service_description = SafeAttributeField("service_description")
    reject_reasons = _SplitSemicolonField("reject_reasons")
    reference = SafeAttributeField("reference")
    created_at = DatetimeAttributeField("created_at")

    address = RelationField("address")
    dids = RelationField("dids")

    class Meta:
        type = "address_verifications"


class AddressVerificationRepository(CreateOnlyRepository):
    _resource_class = AddressVerification
    _path = "address_verifications"
