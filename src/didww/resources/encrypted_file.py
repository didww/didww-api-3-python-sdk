from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, Repository


class EncryptedFile(DidwwApiModel):
    description = SafeAttributeField("description")
    expires_at = DatetimeAttributeField("expires_at")

    class Meta:
        type = "encrypted_files"


class EncryptedFileRepository(Repository):
    _resource_class = EncryptedFile
    _path = "encrypted_files"
