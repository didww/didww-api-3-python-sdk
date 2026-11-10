import copy
import pickle

import pytest

from tests.conftest import my_vcr
from didww.enums import (
    DefaultDstAction,
    IceMode,
    MediaEncryptionMode,
    OnCliMismatchAction,
    RtcpFeedbackMode,
    RtcpMuxMode,
    VoiceOutCodec,
    VoiceOutTrunkStatus,
)
from didww.query_params import QueryParams
from didww.resources.voice_out_trunk import VoiceOutTrunk
from didww.resources.did import Did
from didww.resources.authentication_method import (
    AuthenticationMethod,
    IpOnlyAuthenticationMethod,
    CredentialsAndIpAuthenticationMethod,
    TwilioAuthenticationMethod,
    GenericAuthenticationMethod,
)
from tests.support.http_stub import jsonapi_reply, token_reply

TRUNK_ID = "425ce763-a3a9-49b4-af5b-ada1a65c8864"
TRUNK_REPLY = jsonapi_reply(200, {"data": {"id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {}}})


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
        assert auth.allowed_sip_ips == ["203.0.113.1/32"]
        assert auth.username == "dpjgwbbac9"
        assert auth.password == "z0hshvbcy7"  # NOSONAR
        assert trunk.external_reference_id == "crm-vot-0001"
        assert trunk.emergency_enable_all is False
        assert trunk.rtp_timeout == 30
        assert trunk.codecs == [VoiceOutCodec.OPUS, VoiceOutCodec.PCMA, VoiceOutCodec.TELEPHONE_EVENT]
        assert all(type(codec) is VoiceOutCodec for codec in trunk.codecs)
        assert trunk.ice_mode is IceMode.INITIATE
        assert trunk.rtcp_mux_mode is RtcpMuxMode.ACCEPT
        assert trunk.rtcp_feedback_mode is RtcpFeedbackMode.DISABLED
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

    def test_create_with_codecs_and_modes_request_body(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("POST", "/v3/voice_out_trunks", TRUNK_REPLY)
        trunk = VoiceOutTrunk()
        trunk.name = "out"
        trunk.codecs = [VoiceOutCodec.G722, "opus", VoiceOutCodec.PCMU]
        trunk.ice_mode = IceMode.ACCEPT
        trunk.rtcp_mux_mode = RtcpMuxMode.DISABLED
        trunk.rtcp_feedback_mode = RtcpFeedbackMode.INITIATE

        make_client().voice_out_trunks().create(trunk)

        (hit,) = stub.hits("POST", "/v3/voice_out_trunks")
        assert hit.json() == {"data": {"type": "voice_out_trunks", "attributes": {
            "name": "out",
            "codecs": ["g722", "opus", "pcmu"],
            "ice_mode": "accept",
            "rtcp_mux_mode": "disabled",
            "rtcp_feedback_mode": "initiate",
        }}}

    def test_update_codecs_and_modes_request_body(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.build(TRUNK_ID)
        trunk.codecs = [VoiceOutCodec.AMR, VoiceOutCodec.AMR_WB]
        trunk.ice_mode = "initiate"
        trunk.rtcp_mux_mode = RtcpMuxMode.ACCEPT
        trunk.rtcp_feedback_mode = RtcpFeedbackMode.DISABLED

        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json() == {"data": {"type": "voice_out_trunks", "id": TRUNK_ID, "attributes": {
            "codecs": ["amr", "amr_wb"],
            "ice_mode": "initiate",
            "rtcp_mux_mode": "accept",
            "rtcp_feedback_mode": "disabled",
        }}}

    def test_codecs_changed_in_place_on_a_fetched_trunk_are_sent_on_update(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("GET", f"/v3/voice_out_trunks/{TRUNK_ID}", jsonapi_reply(200, {"data": {
            "id": TRUNK_ID, "type": "voice_out_trunks",
            "attributes": {"name": "out", "codecs": ["pcma", "pcmu"], "ice_mode": "accept"},
        }}))
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        client = make_client()
        trunk = client.voice_out_trunks().find(TRUNK_ID).data

        trunk.codecs.insert(0, VoiceOutCodec.OPUS)
        trunk.codecs.append("telephone_event")
        trunk.codecs.remove(VoiceOutCodec.PCMU)
        client.voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json() == {"data": {"type": "voice_out_trunks", "id": TRUNK_ID, "attributes": {
            "codecs": ["opus", "pcma", "telephone_event"],
        }}}

    @pytest.mark.parametrize("change_a, expected", [
        (lambda trunk: trunk.codecs.append(VoiceOutCodec.OPUS), ["pcma", "pcmu", "opus", "g722"]),
        (lambda trunk: setattr(trunk, "codecs", [VoiceOutCodec.AMR]), ["amr"]),
    ], ids=["in_place_change", "assignment"])
    def test_list_read_earlier_does_not_undo_a_later_change(self, stub, make_client, change_a, expected):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma", "pcmu"]},
        })
        earlier = trunk.codecs

        change_a(trunk)
        earlier.append(VoiceOutCodec.G722)
        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json()["data"]["attributes"] == {"codecs": expected}

    def test_read_after_assigning_another_list_shows_and_tracks_it(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma", "pcmu"]},
        })
        assert trunk.codecs == [VoiceOutCodec.PCMA, VoiceOutCodec.PCMU]

        trunk.codecs = [VoiceOutCodec.AMR]
        later = trunk.codecs
        assert later == [VoiceOutCodec.AMR]
        later.append(VoiceOutCodec.OPUS)
        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json()["data"]["attributes"] == {"codecs": ["amr", "opus"]}

    def test_direct_change_of_the_stored_list_is_kept(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma", "pcmu"]},
        })
        assert trunk.codecs == [VoiceOutCodec.PCMA, VoiceOutCodec.PCMU]

        trunk.attributes["codecs"].append("opus")
        assert trunk.codecs[2] is VoiceOutCodec.OPUS
        trunk.codecs.append("g722")
        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json()["data"]["attributes"] == {"codecs": ["pcma", "pcmu", "opus", "g722"]}

    def test_list_read_earlier_keeps_a_direct_change_of_the_stored_list(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma", "pcmu"]},
        })
        earlier = trunk.codecs

        trunk.attributes["codecs"].append("opus")
        earlier.append(VoiceOutCodec.G722)
        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json()["data"]["attributes"] == {"codecs": ["pcma", "pcmu", "opus", "g722"]}

    def test_list_replaced_by_an_assignment_keeps_its_own_items(self):
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma"]},
        })
        earlier = trunk.codecs
        trunk.codecs = [VoiceOutCodec.AMR]

        earlier.append(VoiceOutCodec.G722)
        earlier.append(VoiceOutCodec.OPUS)

        assert earlier == [VoiceOutCodec.PCMA, VoiceOutCodec.G722, VoiceOutCodec.OPUS]
        assert trunk.codecs == [VoiceOutCodec.AMR]

    def test_assigning_the_list_read_to_itself_keeps_it_live(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma", "pcmu"]},
        })
        earlier = trunk.codecs

        trunk.codecs = trunk.codecs  # NOSONAR python:S1656 -- the self-assignment under test
        earlier.append(VoiceOutCodec.G722)
        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json()["data"]["attributes"] == {"codecs": ["pcma", "pcmu", "g722"]}

    def test_augmented_assignment_keeps_the_list_read_live(self, stub, make_client):
        stub.on("POST", "/token", token_reply())
        stub.on("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}", TRUNK_REPLY)
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma", "pcmu"]},
        })
        earlier = trunk.codecs

        trunk.codecs += [VoiceOutCodec.OPUS]
        earlier.append(VoiceOutCodec.G722)
        make_client().voice_out_trunks().update(trunk)

        (hit,) = stub.hits("PATCH", f"/v3/voice_out_trunks/{TRUNK_ID}")
        assert hit.json()["data"]["attributes"] == {"codecs": ["pcma", "pcmu", "opus", "g722"]}

    def test_codecs_set_to_none_read_as_none(self):
        trunk = VoiceOutTrunk()
        trunk.codecs = None
        assert trunk.codecs is None

    def test_known_codec_added_as_a_string_reads_back_as_a_member(self):
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["pcma"]},
        })
        codecs = trunk.codecs
        codecs.append("opus")
        assert codecs[1] is VoiceOutCodec.OPUS
        codecs.append("future_codec")
        assert type(codecs[2]) is str

    def test_copies_of_the_codec_list_are_plain_lists(self):
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks", "attributes": {"codecs": ["opus", "pcma"]},
        })
        for clone in (copy.copy(trunk.codecs), copy.deepcopy(trunk.codecs), pickle.loads(pickle.dumps(trunk.codecs))):
            assert type(clone) is list
            assert clone == [VoiceOutCodec.OPUS, VoiceOutCodec.PCMA]
            assert all(type(codec) is VoiceOutCodec for codec in clone)
        assert trunk.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {}

    def test_unknown_codec_and_mode_read_as_raw_strings(self):
        trunk = VoiceOutTrunk.from_jsonapi({
            "id": TRUNK_ID, "type": "voice_out_trunks",
            "attributes": {"codecs": ["opus", "future_codec"], "rtcp_mux_mode": "future_mode"},
        })
        assert trunk.codecs[0] is VoiceOutCodec.OPUS
        assert type(trunk.codecs[1]) is str
        assert type(trunk.rtcp_mux_mode) is str

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


class TestVoiceOutTrunkTwilioAuth:
    @my_vcr.use_cassette("voice_out_trunks/show_twilio.yaml")
    def test_find_voice_out_trunk_with_twilio_auth(self, client):
        response = client.voice_out_trunks().find("b5e701f4-ea15-4f9d-8f35-6a0bdce04385")
        trunk = response.data
        assert trunk.id == "b5e701f4-ea15-4f9d-8f35-6a0bdce04385"
        assert trunk.name == "SDK Test twilio"
        assert trunk.status == VoiceOutTrunkStatus.ACTIVE
        # authentication_method must be Twilio
        auth = trunk.authentication_method
        assert isinstance(auth, TwilioAuthenticationMethod)
        assert auth.type == "twilio"
        assert auth.twilio_account_sid == "AC22222222222222222222222222222222"

    @my_vcr.use_cassette("voice_out_trunks/create_twilio.yaml")
    def test_create_voice_out_trunk_with_twilio_auth(self, client):
        trunk = VoiceOutTrunk()
        trunk.name = "SDK Test twilio create"
        trunk.authentication_method = TwilioAuthenticationMethod(
            twilio_account_sid="AC33333333333333333333333333333333",
        )
        trunk.on_cli_mismatch_action = OnCliMismatchAction.REJECT_CALL
        response = client.voice_out_trunks().create(trunk)
        created = response.data
        assert created.id == "507fa5a2-fd58-4c4d-a231-efba27f67c3a"
        assert created.name == "SDK Test twilio create"
        assert created.status == VoiceOutTrunkStatus.ACTIVE
        auth = created.authentication_method
        assert isinstance(auth, TwilioAuthenticationMethod)
        assert auth.twilio_account_sid == "AC33333333333333333333333333333333"


class TestVoiceOutTrunkIpOnlyAuth:
    @my_vcr.use_cassette("voice_out_trunks/show_ip_only.yaml")
    def test_find_voice_out_trunk_with_ip_only_auth(self, client):
        response = client.voice_out_trunks().find("23fd58f9-9094-406c-bfd9-f4d25bda13c6")
        trunk = response.data
        assert trunk.id == "23fd58f9-9094-406c-bfd9-f4d25bda13c6"
        assert trunk.name == "SDK Test credentials_and_ip"
        assert trunk.status == VoiceOutTrunkStatus.ACTIVE
        # authentication_method must be IpOnly, not CredentialsAndIp
        auth = trunk.authentication_method
        assert isinstance(auth, IpOnlyAuthenticationMethod)
        assert not isinstance(auth, CredentialsAndIpAuthenticationMethod)
        assert auth.type == "ip_only"
        assert auth.allowed_sip_ips == ["203.0.113.1/32"]
        assert not hasattr(auth, "username")
        assert not hasattr(auth, "password")


class TestAuthenticationMethodPolymorphism:
    def test_from_jsonapi_ip_only(self):
        data = {"type": "ip_only", "attributes": {"allowed_sip_ips": ["203.0.113.4/32"], "tech_prefix": "123"}}
        auth = AuthenticationMethod.from_jsonapi(data)
        assert isinstance(auth, IpOnlyAuthenticationMethod)
        assert auth.allowed_sip_ips == ["203.0.113.4/32"]
        assert auth.tech_prefix == "123"

    def test_from_jsonapi_credentials_and_ip(self):
        data = {"type": "credentials_and_ip", "attributes": {"allowed_sip_ips": ["203.0.113.4/32"], "tech_prefix": "", "username": "user", "password": "pass"}}  # NOSONAR
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
        auth = IpOnlyAuthenticationMethod(allowed_sip_ips=["203.0.113.0/24"], tech_prefix="")
        serialized = auth.to_jsonapi()
        assert serialized == {"type": "ip_only", "attributes": {"allowed_sip_ips": ["203.0.113.0/24"], "tech_prefix": ""}}

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
