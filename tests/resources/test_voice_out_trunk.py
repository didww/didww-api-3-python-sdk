from tests.conftest import my_vcr
from didww.enums import (
    DefaultDstAction,
    MediaEncryptionMode,
    OnCliMismatchAction,
    VoiceOutTrunkStatus,
)
from didww.query_params import QueryParams
from didww.resources.voice_out_trunk import VoiceOutTrunk
from didww.resources.did import Did
from didww.resources.authentication_method import (
    AuthenticationMethod,
    IpOnlyAuthenticationMethod,
    CredentialsAndIpAuthenticationMethod,
    GenericAuthenticationMethod,
)


class TestVoiceOutTrunk:
    @my_vcr.use_cassette("voice_out_trunks/list.yaml")
    def test_list_voice_out_trunks(self, client):
        response = client.voice_out_trunks().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("voice_out_trunks/show.yaml")
    def test_find_voice_out_trunk(self, client):
        params = QueryParams().include("dids", "default_did")
        response = client.voice_out_trunks().find("425ce763-a3a9-49b4-af5b-ada1a65c8864", params)
        trunk = response.data
        assert trunk.id == "425ce763-a3a9-49b4-af5b-ada1a65c8864"
        assert trunk.name == "test"
        assert trunk.status == VoiceOutTrunkStatus.BLOCKED
        assert trunk.capacity_limit == 123
        assert trunk.allow_any_did_as_cli is False
        assert trunk.on_cli_mismatch_action == OnCliMismatchAction.REPLACE_CLI
        assert trunk.media_encryption_mode == MediaEncryptionMode.SRTP_SDES
        assert trunk.default_dst_action == DefaultDstAction.REJECT_ALL
        assert trunk.dst_prefixes == ["370"]
        assert trunk.force_symmetric_rtp is True
        assert trunk.rtp_ping is True
        assert trunk.threshold_reached is False
        assert trunk.threshold_amount == "200.0"
        assert trunk.callback_url is None
        # polymorphic authentication_method
        auth = trunk.authentication_method
        assert isinstance(auth, CredentialsAndIpAuthenticationMethod)
        assert auth.allowed_sip_ips == ["10.11.12.13/32"]
        assert auth.username == "dpjgwbbac9"
        assert auth.password == "z0hshvbcy7"  # NOSONAR
        assert trunk.external_reference_id == "crm-vot-0001"
        assert trunk.emergency_enable_all is False
        assert trunk.rtp_timeout == 30
        assert len(trunk.dids) == 2
        assert trunk.default_did is not None
        assert trunk.default_did.number == "37061498222"

    @my_vcr.use_cassette("voice_out_trunks/create.yaml")
    def test_create_voice_out_trunk(self, client):
        trunk = VoiceOutTrunk()
        trunk.name = "python-test"
        trunk.authentication_method = IpOnlyAuthenticationMethod(
            allowed_sip_ips=["203.0.113.0/24"],
            tech_prefix="",
        )
        trunk.on_cli_mismatch_action = OnCliMismatchAction.REPLACE_CLI
        did = Did.build("7a028c32-e6b6-4c86-bf01-90f901b37012")
        trunk.default_did = did
        trunk.dids = [did]
        response = client.voice_out_trunks().create(trunk)
        created = response.data
        assert created.id == "b60201c1-21f0-4d9a-aafa-0e6d1e12f22e"
        assert created.name == "python-test"
        assert created.status == VoiceOutTrunkStatus.ACTIVE

    @my_vcr.use_cassette("voice_out_trunks/update.yaml")
    def test_update_voice_out_trunk(self, client):
        trunk = VoiceOutTrunk()
        trunk.id = "425ce763-a3a9-49b4-af5b-ada1a65c8864"
        trunk.media_encryption_mode = MediaEncryptionMode.DISABLED
        response = client.voice_out_trunks().update(trunk)
        updated = response.data
        assert updated.id == "425ce763-a3a9-49b4-af5b-ada1a65c8864"
        assert updated.media_encryption_mode == MediaEncryptionMode.DISABLED
        assert updated.name == "test"

    @my_vcr.use_cassette("voice_out_trunks/delete.yaml")
    def test_delete_voice_out_trunk(self, client):
        result = client.voice_out_trunks().delete("425ce763-a3a9-49b4-af5b-ada1a65c8864")
        assert result is None


class TestVoiceOutTrunkStatusHelpers:
    def test_is_active(self):
        trunk = VoiceOutTrunk()
        trunk.status = VoiceOutTrunkStatus.ACTIVE
        assert trunk.is_active is True
        assert trunk.is_blocked is False

    def test_is_blocked(self):
        trunk = VoiceOutTrunk()
        trunk.status = VoiceOutTrunkStatus.BLOCKED
        assert trunk.is_blocked is True
        assert trunk.is_active is False


class TestVoiceOutTrunkRelationships:
    def test_emergency_dids_relationship(self):
        trunk = VoiceOutTrunk()
        assert hasattr(trunk, 'emergency_dids')


class TestVoiceOutTrunkEmergencyPatch:
    @my_vcr.use_cassette("voice_out_trunks/update_emergency_enable_all.yaml")
    def test_toggle_emergency_enable_all(self, client):
        trunk = VoiceOutTrunk.build("01234567-89ab-cdef-0123-456789abcdef")
        trunk.emergency_enable_all = True
        response = client.voice_out_trunks().update(trunk)
        updated = response.data
        assert updated.id == "01234567-89ab-cdef-0123-456789abcdef"
        assert updated.emergency_enable_all is True

    def test_replace_emergency_dids_request_body(self):
        """PATCH must send emergency_dids as a has-many relationship."""
        trunk = VoiceOutTrunk.build("01234567-89ab-cdef-0123-456789abcdef")
        trunk.emergency_dids = [
            Did.build("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            Did.build("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        ]
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc == {
            "id": "01234567-89ab-cdef-0123-456789abcdef",
            "type": "voice_out_trunks",
            "attributes": {},
            "relationships": {
                "emergency_dids": {
                    "data": [
                        {"type": "dids", "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
                        {"type": "dids", "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"},
                    ]
                }
            },
        }

    @my_vcr.use_cassette("voice_out_trunks/update_emergency_dids.yaml")
    def test_replace_emergency_dids(self, client):
        trunk = VoiceOutTrunk.build("01234567-89ab-cdef-0123-456789abcdef")
        trunk.emergency_dids = [
            Did.build("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            Did.build("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        ]
        response = client.voice_out_trunks().update(trunk)
        updated = response.data
        assert updated.id == "01234567-89ab-cdef-0123-456789abcdef"

    def test_clear_emergency_dids_request_body(self):
        """PATCH with empty list must send emergency_dids data as []."""
        trunk = VoiceOutTrunk.build("01234567-89ab-cdef-0123-456789abcdef")
        trunk.emergency_dids = []
        doc = trunk.to_jsonapi(include_id=True, dirty_only=True)
        assert doc == {
            "id": "01234567-89ab-cdef-0123-456789abcdef",
            "type": "voice_out_trunks",
            "attributes": {},
            "relationships": {
                "emergency_dids": {"data": []}
            },
        }

    @my_vcr.use_cassette("voice_out_trunks/update_clear_emergency_dids.yaml")
    def test_clear_emergency_dids(self, client):
        trunk = VoiceOutTrunk.build("01234567-89ab-cdef-0123-456789abcdef")
        trunk.emergency_dids = []
        response = client.voice_out_trunks().update(trunk)
        updated = response.data
        assert updated.id == "01234567-89ab-cdef-0123-456789abcdef"


class TestAuthenticationMethodPolymorphism:
    def test_from_jsonapi_ip_only(self):
        data = {"type": "ip_only", "attributes": {"allowed_sip_ips": ["1.2.3.4/32"], "tech_prefix": "123"}}
        auth = AuthenticationMethod.from_jsonapi(data)
        assert isinstance(auth, IpOnlyAuthenticationMethod)
        assert auth.allowed_sip_ips == ["1.2.3.4/32"]
        assert auth.tech_prefix == "123"

    def test_from_jsonapi_credentials_and_ip(self):
        data = {"type": "credentials_and_ip", "attributes": {"allowed_sip_ips": ["1.2.3.4/32"], "tech_prefix": "", "username": "user", "password": "pass"}}  # NOSONAR
        auth = AuthenticationMethod.from_jsonapi(data)
        assert isinstance(auth, CredentialsAndIpAuthenticationMethod)
        assert auth.username == "user"
        assert auth.password == "pass"  # NOSONAR

    def test_from_jsonapi_unknown_type_returns_generic(self):
        data = {"type": "future_auth", "attributes": {"some_field": "val"}}
        auth = AuthenticationMethod.from_jsonapi(data)
        assert isinstance(auth, GenericAuthenticationMethod)
        assert auth._type == "future_auth"
        assert auth._attr("some_field") == "val"

    def test_to_jsonapi_roundtrip(self):
        auth = IpOnlyAuthenticationMethod(allowed_sip_ips=["10.0.0.0/8"], tech_prefix="")
        serialized = auth.to_jsonapi()
        assert serialized == {"type": "ip_only", "attributes": {"allowed_sip_ips": ["10.0.0.0/8"], "tech_prefix": ""}}

    def test_type_property_on_known_subclass(self):
        auth = IpOnlyAuthenticationMethod(allowed_sip_ips=["203.0.113.0/24"])
        assert auth.type == "ip_only"

    def test_type_property_on_credentials_and_ip(self):
        auth = CredentialsAndIpAuthenticationMethod(
            allowed_sip_ips=["203.0.113.0/24"], username="u", password="p",  # NOSONAR
        )
        assert auth.type == "credentials_and_ip"

    def test_type_property_on_generic(self):
        data = {"type": "future_auth", "attributes": {"key": "val"}}
        auth = AuthenticationMethod.from_jsonapi(data)
        assert auth.type == "future_auth"
