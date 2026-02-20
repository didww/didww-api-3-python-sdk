from tests.conftest import my_vcr
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.configuration.pstn import PstnConfiguration
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.configuration.h323 import H323Configuration
from didww.resources.configuration.iax2 import Iax2Configuration


class TestVoiceInTrunk:
    @my_vcr.use_cassette("voice_in_trunks/list.yaml")
    def test_list_voice_in_trunks(self, client):
        response = client.voice_in_trunks().list()
        trunks = response.data
        assert len(trunks) > 0
        first = trunks[0]
        assert first.id == "9cbadd6f-0665-46bc-b3aa-687d22157808"
        assert first.name == "iax2 trunk sample"
        assert first.priority == 1
        assert first.weight == 65535
        assert first.cli_format == "e164"

    @my_vcr.use_cassette("voice_in_trunks/create.yaml")
    def test_create_voice_in_trunk_with_pstn(self, client):
        config = PstnConfiguration()
        config.dst = "558540420024"

        trunk = VoiceInTrunk()
        trunk.name = "hello, test pstn trunk"
        trunk.configuration = config

        response = client.voice_in_trunks().create(trunk)
        created = response.data
        assert created.id == "41b94706-325e-4704-a433-d65105758836"
        assert created.name == "hello, test pstn trunk"
        config_obj = created.configuration
        assert isinstance(config_obj, PstnConfiguration)
        assert config_obj.dst == "558540420024"

    def test_pstn_configuration_serialization(self):
        config = PstnConfiguration()
        config.dst = "558540420024"
        data = config.to_jsonapi()
        assert data == {
            "type": "pstn_configurations",
            "attributes": {"dst": "558540420024"},
        }

    def test_sip_configuration_serialization(self):
        config = SipConfiguration()
        config.username = "user"
        config.host = "example.com"
        config.port = 5060
        config.codec_ids = [9, 10, 8]
        data = config.to_jsonapi()
        assert data["type"] == "sip_configurations"
        assert data["attributes"]["username"] == "user"
        assert data["attributes"]["host"] == "example.com"

    def test_h323_configuration_serialization(self):
        config = H323Configuration()
        config.dst = "{CALL_DID}"
        config.host = "127.0.0.1"
        data = config.to_jsonapi()
        assert data["type"] == "h323_configurations"
        assert data["attributes"]["dst"] == "{CALL_DID}"

    def test_iax2_configuration_serialization(self):
        config = Iax2Configuration()
        config.dst = "test"
        config.host = "127.0.0.1"
        data = config.to_jsonapi()
        assert data["type"] == "iax2_configurations"
        assert data["attributes"]["dst"] == "test"

    def test_configuration_deserialization(self):
        from didww.resources.configuration.base import TrunkConfiguration

        data = {"type": "pstn_configurations", "attributes": {"dst": "12345"}}
        config = TrunkConfiguration.from_jsonapi(data)
        assert isinstance(config, PstnConfiguration)
        assert config.dst == "12345"

        data = {"type": "sip_configurations", "attributes": {"username": "user"}}
        config = TrunkConfiguration.from_jsonapi(data)
        assert isinstance(config, SipConfiguration)
        assert config.username == "user"
