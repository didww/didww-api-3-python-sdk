from didww.resources.base import DidwwApiModel, RelationField, CreateOnlyRepository


class VoiceOutTrunkRegenerateCredential(DidwwApiModel):
    _writable_attrs = set()

    voice_out_trunk = RelationField("voice_out_trunk")

    class Meta:
        type = "voice_out_trunk_regenerate_credentials"


class VoiceOutTrunkRegenerateCredentialRepository(CreateOnlyRepository):
    _resource_class = VoiceOutTrunkRegenerateCredential
    _path = "voice_out_trunk_regenerate_credentials"
