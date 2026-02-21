from didww.resources.base import BaseResource, CreateOnlyRepository


class VoiceOutTrunkRegenerateCredential(BaseResource):
    _type = "voice_out_trunk_regenerate_credentials"
    _writable_attrs = set()

    def set_voice_out_trunk(self, trunk):
        self._set_relationship("voice_out_trunk", trunk)


class VoiceOutTrunkRegenerateCredentialRepository(CreateOnlyRepository):
    _resource_class = VoiceOutTrunkRegenerateCredential
    _path = "voice_out_trunk_regenerate_credentials"
