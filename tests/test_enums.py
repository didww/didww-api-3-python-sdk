from didww.enums import (
    CallbackMethod,
    CliFormat,
    Codec,
    ExportType,
    Feature,
    IdentityType,
    OrderStatus,
    ReroutingDisconnectCode,
    TransportProtocol,
    enum_value,
)
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.did_group import DidGroup
from didww.resources.identity import Identity
from didww.resources.order import Order
from didww.resources.voice_in_trunk import VoiceInTrunk


def test_identity_enum_setter_and_getter():
    identity = Identity()
    identity.identity_type = IdentityType.BUSINESS
    assert identity.identity_type == IdentityType.BUSINESS
    assert identity.to_jsonapi()["attributes"]["identity_type"] == enum_value(IdentityType.BUSINESS)


def test_order_enums_from_response():
    order = Order.from_jsonapi({
        "id": "1",
        "type": "orders",
        "attributes": {
            "status": "completed",
            "callback_method": "post",
        },
    })
    assert order.status == OrderStatus.COMPLETED
    assert order.callback_method == CallbackMethod.POST


def test_voice_in_trunk_and_sip_enums():
    trunk = VoiceInTrunk()
    trunk.cli_format = CliFormat.E164
    assert trunk.cli_format == CliFormat.E164
    assert trunk.to_jsonapi()["attributes"]["cli_format"] == enum_value(CliFormat.E164)

    sip = SipConfiguration()
    sip.codecs = [Codec.PCMU, Codec.PCMA]
    sip.transport_protocol_id = TransportProtocol.UDP
    data = sip.to_jsonapi()
    assert data["attributes"]["codecs"] == ["pcmu", "pcma"]
    assert data["attributes"]["transport_protocol_id"] == 1


def test_codec_ids_are_gone():
    assert not hasattr(SipConfiguration, "codec_ids")
    assert all(isinstance(codec.value, str) for codec in Codec)
    assert not issubclass(Codec, int)


def test_codec_and_mode_values_match_the_api_document():
    from didww.enums import IceMode, RtcpFeedbackMode, RtcpMuxMode, VoiceOutCodec

    assert [c.value for c in Codec] == [
        "telephone_event", "g723", "g729", "pcmu", "pcma", "speex", "gsm", "g726_32", "g721",
        "g726_24", "g726_40", "g726_16", "l16", "amr", "amr_wb"]
    assert [c.value for c in VoiceOutCodec] == [
        "telephone_event", "g723", "g729", "pcmu", "pcma", "gsm", "g722", "opus", "amr", "amr_wb"]
    for mode in (IceMode, RtcpMuxMode, RtcpFeedbackMode):
        assert [m.value for m in mode] == ["disabled", "accept", "initiate"]


def test_rerouting_disconnect_code_enum_serialization():
    sip = SipConfiguration()
    sip.rerouting_disconnect_code_ids = [
        ReroutingDisconnectCode.SIP_480_TEMPORARILY_UNAVAILABLE,
        ReroutingDisconnectCode.RINGING_TIMEOUT,
    ]
    data = sip.to_jsonapi()
    assert data["attributes"]["rerouting_disconnect_code_ids"] == [84, 1505]


def test_did_group_features_enum_round_trip():
    group = DidGroup()
    group.features = [Feature.VOICE_IN, Feature.SMS_IN]
    assert group.features == [Feature.VOICE_IN, Feature.SMS_IN]
    assert group.to_jsonapi()["attributes"]["features"] == ["voice_in", "sms_in"]


def test_copies_of_did_group_features_are_plain_lists():
    import copy
    import pickle

    group = DidGroup.from_jsonapi({"id": "1", "type": "did_groups", "attributes": {"features": ["voice_in", "t38"]}})
    for clone in (copy.deepcopy(group.features), pickle.loads(pickle.dumps(group.features))):
        assert type(clone) is list
        assert clone == [Feature.VOICE_IN, Feature.T38]
        assert all(type(feature) is Feature for feature in clone)


def test_did_group_features_accepts_strings_for_backward_compatibility():
    group = DidGroup()
    group.features = ["voice_in", "t38"]
    assert group.features == [Feature.VOICE_IN, Feature.T38]


def test_export_type_accepts_string_for_backward_compatibility():
    from didww.resources.export import Export

    export = Export()
    export.export_type = "cdr_in"
    assert export.export_type == ExportType.CDR_IN


def test_new_enum_values():
    import didww
    from didww.enums import (
        ExportServiceType,
        ExportTrunkType,
        NumberType,
        Pop,
        SenderIdVerificationStatus,
        SenderType,
        SmsBodyType,
        SmsHttpMethod,
        SmsServerLocation,
    )

    assert [e.value for e in NumberType] == ["local", "national", "mobile", "toll_free", "shared_cost", "global"]
    assert [e.value for e in Pop] == ["nyc", "fra", "lac", "mia", "sg", "hk", "ams"]
    assert didww.Pop is Pop
    assert ExportType.SMS_IN.value == "sms_in"
    assert ExportType.SMS_OUT.value == "sms_out"
    assert [e.value for e in ExportTrunkType] == ["smpp_smsc", "smpp_esme", "sms_to_email", "http_in"]
    assert [e.value for e in ExportServiceType] == ["a2p", "p2p"]
    assert [e.name for e in ExportTrunkType] == ["SMPP_SMSC", "SMPP_ESME", "SMS_TO_EMAIL", "HTTP_IN"]
    assert [e.name for e in ExportServiceType] == ["A2P", "P2P"]
    assert [e.value for e in SenderIdVerificationStatus] == [
        "active", "changes_required", "closed", "closing_in_process", "in_process", "new"]
    assert [e.value for e in SenderType] == ["alphanumeric", "carrier", "long_code", "short_code", "toll_free"]
    assert [e.value for e in SmsHttpMethod] == ["get", "post", "put"]
    assert [e.value for e in SmsBodyType] == ["json", "html_multipart", "html_url_encoded", "raw"]
    assert [e.value for e in SmsServerLocation] == ["nyc", "ams"]


def test_number_type_and_pop_round_trip():
    from didww.enums import NumberType, Pop

    group = DidGroup.from_jsonapi({"id": "1", "type": "did_groups", "attributes": {"number_type": "toll_free"}})
    assert group.number_type == NumberType.TOLL_FREE
    future = DidGroup.from_jsonapi({"id": "1", "type": "did_groups", "attributes": {"number_type": "future"}})
    assert future.number_type == "future"

    trunk = VoiceInTrunk()
    trunk.pop = Pop.AMS
    assert trunk.to_jsonapi()["attributes"]["pop"] == "ams"
    trunk.pop = "fra"
    assert trunk.pop is Pop.FRA
    unknown = VoiceInTrunk.from_jsonapi({"id": "1", "type": "voice_in_trunks", "attributes": {"pop": "XYZ"}})
    assert unknown.pop == "XYZ"
