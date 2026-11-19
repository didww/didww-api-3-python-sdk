from didww.resources.base import DidwwApiModel, RelationField, CreateOnlyRepository


class SmsTrunkRegenerateCredential(DidwwApiModel):
    """Regenerates the credentials of an ``smpp_esme`` or ``http_out`` SMS trunk.

    The response carries no credentials; read them from the trunk afterwards.
    """

    _writable_attrs = set()

    sms_trunk = RelationField("sms_trunk")

    class Meta:
        type = "sms_trunk_regenerate_credentials"


class SmsTrunkRegenerateCredentialRepository(CreateOnlyRepository):
    _resource_class = SmsTrunkRegenerateCredential
    _path = "sms_trunk_regenerate_credentials"
