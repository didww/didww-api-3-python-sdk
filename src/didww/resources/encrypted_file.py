from didww.resources.base import DidwwApiModel, SafeAttributeField, Repository


class EncryptedFile(DidwwApiModel):
    description = SafeAttributeField("description")
    expire_at = SafeAttributeField("expire_at")

    class Meta:
        type = "encrypted_files"


class EncryptedFileRepository(Repository):
    _resource_class = EncryptedFile
    _path = "encrypted_files"
