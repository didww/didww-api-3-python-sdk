from tests.conftest import my_vcr
from didww.enums import (
    CliFormat,
    Codec,
    DiversionInjectMode,
    DiversionRelayPolicy,
    MediaEncryptionMode,
    NetworkProtocolPriority,
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
    @my_vcr.use_cassette("voice_in_trunks/show.yaml")
    def test_find_voice_in_trunk(self, client):
        response = client.voice_in_trunks().find("2b4b1fcf-fe6a-4de9-8a58-7df46820ba13")
        trunk = response.data
        assert trunk.id == "2b4b1fcf-fe6a-4de9-8a58-7df46820ba13"
        assert trunk.name == "sample trunk pstn"
        assert trunk.external_reference_id == "crm-vit-0001"

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
        assert config.host == "203.0.113.78"
        assert config.port == 8060
        assert config.codec_ids == [Codec.PCMU, Codec.PCMA, Codec.G729]
        assert config.transport_protocol_id == TransportProtocol.UDP
        assert config.auth_enabled is True
        assert config.auth_user == "auth_user"
        assert config.auth_password == "auth_password"  # NOSONAR
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
        config.host = "203.0.113.110"
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
        config.allowed_rtp_ips = ["203.0.113.1"]
        # API 2026-04-16 writable attributes
        config.diversion_relay_policy = DiversionRelayPolicy.AS_IS
        config.diversion_inject_mode = DiversionInjectMode.DID_NUMBER
        config.network_protocol_priority = NetworkProtocolPriority.FORCE_IPV4
        config.cnam_lookup = True
        # use_did_in_ruri must stay false unless enabled_sip_registration is
        # also True (server returns 422 otherwise).  Setting it here is
        # redundant against the default but documents the field.
        config.use_did_in_ruri = False

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

    @my_vcr.use_cassette("voice_in_trunks/create_with_sip_registration.yaml")
    def test_create_voice_in_trunk_with_sip_registration_returns_populated_credentials(self, client):
        """End-to-end: when the SDK sends ``enabled_sip_registration: True`` the
        server returns 201 with server-generated ``incoming_auth_username`` and
        ``incoming_auth_password``. The SDK must surface those populated values
        to the caller, not None."""
        config = SipConfiguration()
        config.enabled_sip_registration = True
        config.use_did_in_ruri = True
        config.cnam_lookup = True
        config.diversion_relay_policy = DiversionRelayPolicy.AS_IS
        config.diversion_inject_mode = DiversionInjectMode.DID_NUMBER
        config.network_protocol_priority = NetworkProtocolPriority.PREFER_IPV4

        trunk = VoiceInTrunk()
        trunk.name = "sip-registration"
        trunk.priority = 1
        trunk.weight = 100
        trunk.cli_format = CliFormat.E164
        trunk.ringing_timeout = 30
        trunk.configuration = config

        response = client.voice_in_trunks().create(trunk)
        created = response.data
        sip_config = created.configuration
        assert isinstance(sip_config, SipConfiguration)
        assert sip_config.enabled_sip_registration is True
        # Server-generated credentials are populated, not None.
        assert sip_config.incoming_auth_username
        assert sip_config.incoming_auth_password

    @my_vcr.use_cassette("voice_in_trunks/disable_sip_registration.yaml")
    def test_disable_sip_registration_patch_serializes_all_three_fields(self, client):
        """Disabling SIP registration is a multi-field PATCH because the
        server's V3 form rejects (422) any request that flips
        ``enabled_sip_registration`` to false without simultaneously
        providing a non-blank ``host`` (model-level presence) and
        ``use_did_in_ruri: false`` (form-level). Lock those three fields in
        the same request body — the cassette matches on body, so a future
        regression that drops one of them fails the request match."""
        config = SipConfiguration()
        config.enabled_sip_registration = False
        config.use_did_in_ruri = False
        config.host = "203.0.113.10"

        trunk = VoiceInTrunk()
        trunk.id = "57a939dd-1600-41a6-80b1-f624e22a1f4c"
        trunk.configuration = config

        response = client.voice_in_trunks().update(trunk)
        sip_config = response.data.configuration
        assert isinstance(sip_config, SipConfiguration)
        assert sip_config.enabled_sip_registration is False
        assert sip_config.use_did_in_ruri is False
        assert sip_config.host == "203.0.113.10"
        assert sip_config.incoming_auth_username is None
        assert sip_config.incoming_auth_password is None

    @my_vcr.use_cassette("voice_in_trunks/delete.yaml")
    def test_delete_voice_in_trunk(self, client):
        result = client.voice_in_trunks().delete("41b94706-325e-4704-a433-d65105758836")
        assert result is None

    # 2026-04-16 SIP-registration attributes (API 2026-04-16).
    #
    # Real wire shape captured from sandbox: when sip_registration is
    # enabled, host/port/username come back as null and the API rejects
    # any attempt to set them, so the test fixtures below intentionally
    # omit them.
    def test_sip_configuration_v35_writable_attributes_serialize(self):
        from didww.enums import DiversionInjectMode, NetworkProtocolPriority

        config = SipConfiguration(
            attributes={
                "enabled_sip_registration": True,
                "use_did_in_ruri": True,
                "cnam_lookup": True,
                "diversion_inject_mode": "did_number",
                "network_protocol_priority": "prefer_ipv4",
            }
        )
        assert config.enabled_sip_registration is True
        assert config.use_did_in_ruri is True
        assert config.cnam_lookup is True
        assert config.diversion_inject_mode == DiversionInjectMode.DID_NUMBER
        assert config.network_protocol_priority == NetworkProtocolPriority.PREFER_IPV4

        payload = config.to_jsonapi()
        assert payload["type"] == "sip_configurations"
        assert payload["attributes"]["enabled_sip_registration"] is True
        assert payload["attributes"]["use_did_in_ruri"] is True
        assert payload["attributes"]["cnam_lookup"] is True
        assert payload["attributes"]["diversion_inject_mode"] == "did_number"
        assert payload["attributes"]["network_protocol_priority"] == "prefer_ipv4"

    def test_sip_configuration_exposes_read_only_incoming_auth_credentials(self):
        # Test fixture values; not a real credential. NOSONAR-suppressed below.
        fake_user = "sipreg-user-1"
        fake_pass = "s3cret-Pa55"  # NOSONAR python:S2068 -- test fixture
        config = SipConfiguration(
            attributes={
                "host": None,
                "port": None,
                "username": None,
                "enabled_sip_registration": True,
                "incoming_auth_username": fake_user,
                "incoming_auth_password": fake_pass,
            }
        )
        assert config.incoming_auth_username == fake_user
        assert config.incoming_auth_password == fake_pass

    def test_sip_configuration_strips_read_only_credentials_from_write_payload(self):
        # Simulate a caller who loaded a SIP configuration from the server
        # (with incoming_auth_* populated) and submits it back. The server
        # returns 400 Param not allowed if these are echoed in the request,
        # so the SDK MUST strip them from the JSON:API payload.
        fake_user = "sipreg-user-1"
        fake_pass = "s3cret-Pa55"  # NOSONAR python:S2068 -- test fixture
        config = SipConfiguration(
            attributes={
                "enabled_sip_registration": True,
                "use_did_in_ruri": True,
                "incoming_auth_username": fake_user,
                "incoming_auth_password": fake_pass,
            }
        )
        payload = config.to_jsonapi()
        assert payload["attributes"]["enabled_sip_registration"] is True
        assert payload["attributes"]["use_did_in_ruri"] is True
        assert "incoming_auth_username" not in payload["attributes"]
        assert "incoming_auth_password" not in payload["attributes"]

    def test_sip_configuration_repr_redacts_credentials(self):
        # Default __repr__ output is what shows up in default print() /
        # logging / unhandled exception traces — none of those contexts
        # should ever expose SIP credentials in plaintext.
        secret_pass = "s3cret-Pa55"  # NOSONAR python:S2068 -- test fixture
        secret_inc_pass = "srv-pass-xyz"  # NOSONAR python:S2068
        config = SipConfiguration(
            attributes={
                "username": "alice",
                "host": "sip.example.com",
                "auth_password": secret_pass,
                "enabled_sip_registration": True,
                "incoming_auth_username": "srv-user-xyz",
                "incoming_auth_password": secret_inc_pass,
            }
        )
        output = repr(config)
        assert "alice" in output
        assert "sip.example.com" in output
        assert secret_pass not in output
        assert "srv-user-xyz" not in output
        assert secret_inc_pass not in output
        assert "[FILTERED]" in output
