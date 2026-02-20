from tests.conftest import my_vcr
from didww.resources.voice_out_trunk_regenerate_credential import VoiceOutTrunkRegenerateCredential


class TestVoiceOutTrunkRegenerateCredential:
    @my_vcr.use_cassette("voice_out_trunk_regenerate_credentials/create.yaml")
    def test_create(self, client):
        resource = VoiceOutTrunkRegenerateCredential()
        response = client.voice_out_trunk_regenerate_credentials().create(resource)
        created = response.data
        assert created.id == "5fc59e7e-79eb-498a-8779-800416b5c68a"
