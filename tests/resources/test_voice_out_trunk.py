from tests.conftest import my_vcr
from didww.resources.voice_out_trunk import VoiceOutTrunk


class TestVoiceOutTrunk:
    @my_vcr.use_cassette("voice_out_trunks/list.yaml")
    def test_list_voice_out_trunks(self, client):
        response = client.voice_out_trunks().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("voice_out_trunks/show.yaml")
    def test_find_voice_out_trunk(self, client):
        response = client.voice_out_trunks().find("425ce763-a3a9-49b4-af5b-ada1a65c8864")
        trunk = response.data
        assert trunk.id == "425ce763-a3a9-49b4-af5b-ada1a65c8864"
        assert trunk.name == "test"
        assert trunk.status == "blocked"
        assert trunk.allowed_sip_ips == ["10.11.12.13/32"]

    @my_vcr.use_cassette("voice_out_trunks/create.yaml")
    def test_create_voice_out_trunk(self, client):
        trunk = VoiceOutTrunk()
        trunk.name = "php-test"
        trunk.allowed_sip_ips = ["0.0.0.0/0"]
        trunk.on_cli_mismatch_action = "replace_cli"
        trunk.set_default_did("7a028c32-e6b6-4c86-bf01-90f901b37012")
        trunk.set_dids(["7a028c32-e6b6-4c86-bf01-90f901b37012"])
        response = client.voice_out_trunks().create(trunk)
        created = response.data
        assert created.id == "b60201c1-21f0-4d9a-aafa-0e6d1e12f22e"
        assert created.name == "php-test"
        assert created.status == "active"
