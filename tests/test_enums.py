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
    sip.codec_ids = [Codec.PCMU, Codec.PCMA]
    sip.transport_protocol_id = TransportProtocol.UDP
    data = sip.to_jsonapi()
    assert data["attributes"]["codec_ids"] == [9, 10]
    assert data["attributes"]["transport_protocol_id"] == 1


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
    assert [e.value for e in Pop] == ["NYC", "FRA", "LAC", "MIA", "SG", "HK", "AMS"]
    assert didww.Pop is Pop
    assert ExportType.SMS_IN.value == "sms_in"
    assert ExportType.SMS_OUT.value == "sms_out"
    assert [e.value for e in ExportTrunkType] == ["SMPP SMSC", "SMPP ESME", "Email", "HTTP IN"]
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
    assert trunk.to_jsonapi()["attributes"]["pop"] == "AMS"
    trunk.pop = "FRA"
    assert trunk.pop == Pop.FRA
    unknown = VoiceInTrunk.from_jsonapi({"id": "1", "type": "voice_in_trunks", "attributes": {"pop": "XYZ"}})
    assert unknown.pop == "XYZ"
