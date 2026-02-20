from didww.resources.base import BaseResource, ReadOnlyRepository


class PublicKey(BaseResource):
    _type = "public_keys"

    @property
    def key(self):
        return self._attr("key")


class PublicKeyRepository(ReadOnlyRepository):
    _resource_class = PublicKey
    _path = "public_keys"
