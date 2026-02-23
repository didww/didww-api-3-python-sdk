from tests.conftest import my_vcr
from didww.enums import (
    CliFormat,
    Codec,
    MediaEncryptionMode,
    RxDtmfFormat,
    SstRefreshMethod,
    StirShakenMode,
    TransportProtocol,
    TxDtmfFormat,
)
from didww.query_params import QueryParams
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.configuration.pstn import PstnConfiguration
from didww.resources.configuration.sip import SipConfiguration


class TestVoiceInTrunk:
    @my_vcr.use_cassette("voice_in_trunks/list.yaml")
    def test_list_voice_in_trunks(self, client):
        params = QueryParams().include("trunk_group", "pop")
        response = client.voice_in_trunks().list(params)
        trunks = response.data
        assert len(trunks) > 0
        first = trunks[0]
        assert first.id == "2b4b1fcf-fe6a-4de9-8a58-7df46820ba13"
        assert first.name == "sample trunk pstn"
        assert first.priority == 1
        assert first.weight == 65535
        assert first.cli_format == CliFormat.E164
        assert first.voice_in_trunk_group is None

    @my_vcr.use_cassette("voice_in_trunks/list.yaml")
    def test_list_sip_configuration_attributes(self, client):
        response = client.voice_in_trunks().list()
        trunks = response.data
        # Find the SIP trunk in the list
        sip_trunk = None
        for t in trunks:
            config = t.configuration
            if isinstance(config, SipConfiguration):
                sip_trunk = t
                break
        assert sip_trunk is not None, "No SIP trunk found in list fixture"
        config = sip_trunk.configuration
        assert config.username == "username"
        assert config.host == "216.58.215.78"
        assert config.port == 8060
        assert config.codec_ids == [Codec.PCMU, Codec.PCMA, Codec.G729]
        assert config.transport_protocol_id == TransportProtocol.UDP
        assert config.auth_enabled is True
        assert config.auth_user == "auth_user"
        assert config.auth_password == "auth_password"
        assert config.auth_from_user == ""
        assert config.auth_from_domain == ""
        assert config.resolve_ruri is True
        assert config.rx_dtmf_format_id == RxDtmfFormat.RFC_2833
        assert config.tx_dtmf_format_id == TxDtmfFormat.DISABLED
        assert config.sst_enabled is False
        assert config.sst_min_timer == 600
        assert config.sst_max_timer == 900
        assert config.sst_accept_501 is True
        assert config.sst_refresh_method_id == SstRefreshMethod.INVITE
        assert config.sip_timer_b == 8000
        assert config.dns_srv_failover_timer == 2000
        assert config.rtp_ping is False
        assert config.force_symmetric_rtp is False
        assert config.max_transfers == 2
        assert config.max_30x_redirects == 5
        assert config.media_encryption_mode == MediaEncryptionMode.DISABLED
        assert config.stir_shaken_mode == StirShakenMode.DISABLED
        assert config.allowed_rtp_ips is None

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
        config.codec_ids = [Codec.PCMU, Codec.PCMA, Codec.G729]
        data = config.to_jsonapi()
        assert data["type"] == "sip_configurations"
        assert data["attributes"]["username"] == "user"
        assert data["attributes"]["host"] == "example.com"
        assert data["attributes"]["codec_ids"] == [9, 10, 8]

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

    @my_vcr.use_cassette("voice_in_trunks/delete.yaml")
    def test_delete_voice_in_trunk(self, client):
        result = client.voice_in_trunks().delete("41b94706-325e-4704-a433-d65105758836")
        assert result is None
