from didww.resources.configuration.base import TrunkConfiguration
from didww.enums import (
    Codec,
    MediaEncryptionMode,
    ReroutingDisconnectCode,
    RxDtmfFormat,
    SstRefreshMethod,
    StirShakenMode,
    TransportProtocol,
    TxDtmfFormat,
    enum_value,
    enum_value_list,
    to_enum,
    to_enum_list,
)


def _plain(key):
    return property(lambda self: self._attr(key), lambda self, v: self._set_attr(key, v))


def _enum(key, cls):
    return property(
        lambda self: to_enum(cls, self._attr(key)),
        lambda self, v: self._set_attr(key, enum_value(v)),
    )


def _enum_list(key, cls):
    return property(
        lambda self: to_enum_list(cls, self._attr(key)),
        lambda self, v: self._set_attr(key, enum_value_list(v)),
    )


class SipConfiguration(TrunkConfiguration):
    _type = "sip_configurations"

    username               = _plain("username")
    host                   = _plain("host")
    port                   = _plain("port")
    auth_enabled           = _plain("auth_enabled")
    resolve_ruri           = _plain("resolve_ruri")
    auth_user              = _plain("auth_user")
    auth_password          = _plain("auth_password")
    auth_from_user         = _plain("auth_from_user")
    auth_from_domain       = _plain("auth_from_domain")
    sst_enabled            = _plain("sst_enabled")
    sst_min_timer          = _plain("sst_min_timer")
    sst_max_timer          = _plain("sst_max_timer")
    sst_accept_501         = _plain("sst_accept_501")
    sst_session_expires    = _plain("sst_session_expires")
    sip_timer_b            = _plain("sip_timer_b")
    dns_srv_failover_timer = _plain("dns_srv_failover_timer")
    rtp_ping               = _plain("rtp_ping")
    force_symmetric_rtp    = _plain("force_symmetric_rtp")
    max_transfers          = _plain("max_transfers")
    max_30x_redirects      = _plain("max_30x_redirects")
    allowed_rtp_ips        = _plain("allowed_rtp_ips")

    codec_ids                     = _enum_list("codec_ids", Codec)
    rerouting_disconnect_code_ids = _enum_list("rerouting_disconnect_code_ids", ReroutingDisconnectCode)

    transport_protocol_id = _enum("transport_protocol_id", TransportProtocol)
    rx_dtmf_format_id     = _enum("rx_dtmf_format_id", RxDtmfFormat)
    tx_dtmf_format_id     = _enum("tx_dtmf_format_id", TxDtmfFormat)
    sst_refresh_method_id = _enum("sst_refresh_method_id", SstRefreshMethod)
    media_encryption_mode = _enum("media_encryption_mode", MediaEncryptionMode)
    stir_shaken_mode      = _enum("stir_shaken_mode", StirShakenMode)


TrunkConfiguration.register("sip_configurations", SipConfiguration)
