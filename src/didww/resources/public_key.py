from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class PublicKey(DidwwApiModel):
    key = SafeAttributeField("key")

    class Meta:
        type = "public_keys"


class PublicKeyRepository(ReadOnlyRepository):
    _resource_class = PublicKey
    _path = "public_keys"
