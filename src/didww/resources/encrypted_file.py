from didww.resources.base import BaseResource, Repository


class EncryptedFile(BaseResource):
    _type = "encrypted_files"

    @property
    def description(self):
        return self._attr("description")

    @property
    def expire_at(self):
        return self._attr("expire_at")


class EncryptedFileRepository(Repository):
    _resource_class = EncryptedFile
    _path = "encrypted_files"
