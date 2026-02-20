from didww.resources.base import BaseResource, CreateOnlyRepository


class VoiceOutTrunkRegenerateCredential(BaseResource):
    _type = "voice_out_trunk_regenerate_credentials"
    _writable_attrs = set()


class VoiceOutTrunkRegenerateCredentialRepository(CreateOnlyRepository):
    _resource_class = VoiceOutTrunkRegenerateCredential
    _path = "voice_out_trunk_regenerate_credentials"
