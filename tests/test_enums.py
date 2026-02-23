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
            "status": "Completed",
            "callback_method": "POST",
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
