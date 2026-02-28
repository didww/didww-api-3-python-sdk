from tests.conftest import my_vcr
from didww.enums import (
    CliFormat,
    Codec,
    MediaEncryptionMode,
    ReroutingDisconnectCode,
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
        assert first.pop is None
        second = trunks[1]
        assert second.pop is not None
        assert second.pop.name == "DE, FRA"

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
        assert config.rerouting_disconnect_code_ids is None

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

    @my_vcr.use_cassette("voice_in_trunks/create_sip_with_rerouting.yaml")
    def test_create_sip_trunk_with_rerouting_disconnect_codes(self, client):
        config = SipConfiguration()
        config.username = "username"
        config.host = "216.58.215.110"
        config.sst_refresh_method_id = SstRefreshMethod.INVITE
        config.port = 5060
        config.codec_ids = [Codec.PCMU, Codec.PCMA, Codec.G729, Codec.G723, Codec.TELEPHONE_EVENT]
        config.rerouting_disconnect_code_ids = [
            ReroutingDisconnectCode.SIP_400_BAD_REQUEST,
            ReroutingDisconnectCode.SIP_402_PAYMENT_REQUIRED,
            ReroutingDisconnectCode.SIP_403_FORBIDDEN,
            ReroutingDisconnectCode.SIP_404_NOT_FOUND,
            ReroutingDisconnectCode.SIP_408_REQUEST_TIMEOUT,
            ReroutingDisconnectCode.SIP_409_CONFLICT,
            ReroutingDisconnectCode.SIP_410_GONE,
            ReroutingDisconnectCode.SIP_412_CONDITIONAL_REQUEST_FAILED,
            ReroutingDisconnectCode.SIP_413_REQUEST_ENTITY_TOO_LARGE,
            ReroutingDisconnectCode.SIP_414_REQUEST_URI_TOO_LONG,
            ReroutingDisconnectCode.SIP_415_UNSUPPORTED_MEDIA_TYPE,
            ReroutingDisconnectCode.SIP_416_UNSUPPORTED_URI_SCHEME,
            ReroutingDisconnectCode.SIP_417_UNKNOWN_RESOURCE_PRIORITY,
            ReroutingDisconnectCode.SIP_420_BAD_EXTENSION,
            ReroutingDisconnectCode.SIP_421_EXTENSION_REQUIRED,
            ReroutingDisconnectCode.SIP_422_SESSION_INTERVAL_TOO_SMALL,
            ReroutingDisconnectCode.SIP_423_INTERVAL_TOO_BRIEF,
            ReroutingDisconnectCode.SIP_424_BAD_LOCATION_INFORMATION,
            ReroutingDisconnectCode.SIP_428_USE_IDENTITY_HEADER,
            ReroutingDisconnectCode.SIP_429_PROVIDE_REFERRER_IDENTITY,
            ReroutingDisconnectCode.SIP_433_ANONYMITY_DISALLOWED,
            ReroutingDisconnectCode.SIP_436_BAD_IDENTITY_INFO,
            ReroutingDisconnectCode.SIP_437_UNSUPPORTED_CERTIFICATE,
            ReroutingDisconnectCode.SIP_438_INVALID_IDENTITY_HEADER,
            ReroutingDisconnectCode.SIP_480_TEMPORARILY_UNAVAILABLE,
            ReroutingDisconnectCode.SIP_482_LOOP_DETECTED,
            ReroutingDisconnectCode.SIP_483_TOO_MANY_HOPS,
            ReroutingDisconnectCode.SIP_484_ADDRESS_INCOMPLETE,
            ReroutingDisconnectCode.SIP_485_AMBIGUOUS,
            ReroutingDisconnectCode.SIP_486_BUSY_HERE,
            ReroutingDisconnectCode.SIP_487_REQUEST_TERMINATED,
            ReroutingDisconnectCode.SIP_488_NOT_ACCEPTABLE_HERE,
            ReroutingDisconnectCode.SIP_494_SECURITY_AGREEMENT_REQUIRED,
            ReroutingDisconnectCode.SIP_500_SERVER_INTERNAL_ERROR,
            ReroutingDisconnectCode.SIP_501_NOT_IMPLEMENTED,
            ReroutingDisconnectCode.SIP_502_BAD_GATEWAY,
            ReroutingDisconnectCode.SIP_504_SERVER_TIME_OUT,
            ReroutingDisconnectCode.SIP_505_VERSION_NOT_SUPPORTED,
            ReroutingDisconnectCode.SIP_513_MESSAGE_TOO_LARGE,
            ReroutingDisconnectCode.SIP_580_PRECONDITION_FAILURE,
            ReroutingDisconnectCode.SIP_600_BUSY_EVERYWHERE,
            ReroutingDisconnectCode.SIP_603_DECLINE,
            ReroutingDisconnectCode.SIP_604_DOES_NOT_EXIST_ANYWHERE,
            ReroutingDisconnectCode.SIP_606_NOT_ACCEPTABLE,
            ReroutingDisconnectCode.RINGING_TIMEOUT,
        ]
        config.media_encryption_mode = MediaEncryptionMode.ZRTP
        config.stir_shaken_mode = StirShakenMode.PAI
        config.allowed_rtp_ips = ["127.0.0.1"]

        trunk = VoiceInTrunk()
        trunk.name = "hello, test sip trunk"
        trunk.configuration = config

        response = client.voice_in_trunks().create(trunk)
        created = response.data
        sip_config = created.configuration
        assert isinstance(sip_config, SipConfiguration)

        codes = sip_config.rerouting_disconnect_code_ids
        assert len(codes) == 45
        assert all(isinstance(c, ReroutingDisconnectCode) for c in codes)
        assert codes[0] == ReroutingDisconnectCode.SIP_400_BAD_REQUEST
        assert codes[-1] == ReroutingDisconnectCode.RINGING_TIMEOUT
        assert ReroutingDisconnectCode.SIP_480_TEMPORARILY_UNAVAILABLE in codes

    @my_vcr.use_cassette("voice_in_trunks/update_pstn.yaml")
    def test_update_voice_in_trunk_pstn(self, client):
        config = PstnConfiguration()
        config.dst = "558540420025"
        trunk = VoiceInTrunk()
        trunk.id = "41b94706-325e-4704-a433-d65105758836"
        trunk.name = "hello, updated test pstn trunk"
        trunk.configuration = config
        response = client.voice_in_trunks().update(trunk)
        updated = response.data
        assert updated.id == "41b94706-325e-4704-a433-d65105758836"
        assert updated.name == "hello, updated test pstn trunk"
        config_obj = updated.configuration
        assert isinstance(config_obj, PstnConfiguration)
        assert config_obj.dst == "558540420025"

    @my_vcr.use_cassette("voice_in_trunks/update_sip.yaml")
    def test_update_voice_in_trunk_sip(self, client):
        config = SipConfiguration()
        config.username = "new-username"
        config.max_transfers = 5
        trunk = VoiceInTrunk()
        trunk.id = "a80006b6-4183-4865-8b99-7ebbd359a762"
        trunk.name = "hello, updated test sip trunk"
        trunk.description = "just a description"
        trunk.configuration = config
        response = client.voice_in_trunks().update(trunk)
        updated = response.data
        assert updated.id == "a80006b6-4183-4865-8b99-7ebbd359a762"
        assert updated.name == "hello, updated test sip trunk"
        assert updated.description == "just a description"
        sip_config = updated.configuration
        assert isinstance(sip_config, SipConfiguration)
        assert sip_config.username == "new-username"
        assert sip_config.max_transfers == 5

    @my_vcr.use_cassette("voice_in_trunks/delete.yaml")
    def test_delete_voice_in_trunk(self, client):
        result = client.voice_in_trunks().delete("41b94706-325e-4704-a433-d65105758836")
        assert result is None
