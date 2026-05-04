from didww.resources.configuration.base import TrunkConfiguration
from didww.enums import (
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
    # Server-generated SIP registration credentials. The API rejects any
    # write attempt with 400 Param not allowed, so they are deserialized
    # from responses (readable via the property) but stripped from
    # POST/PATCH request bodies. (API 2026-04-16)
    _read_only_attrs = frozenset({
        "incoming_auth_username",
        "incoming_auth_password",
    })
    _sensitive_attrs = frozenset({
        "auth_password",
        "incoming_auth_username",
        "incoming_auth_password",
    })

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

    # API 2026-04-16 SIP registration + protocol attributes.
    #
    # Server-side validation rules for `enabled_sip_registration`:
    #   * When True, the trunk's `host` and `port` must be left blank
    #     (server returns 422 otherwise).
    #   * When disabling sip registration on an existing trunk, the same
    #     PATCH must also set `host` to a non-blank value and
    #     `use_did_in_ruri` to False, or the server returns 422.
    enabled_sip_registration = _plain("enabled_sip_registration")
    use_did_in_ruri          = _plain("use_did_in_ruri")
    cnam_lookup              = _plain("cnam_lookup")

    # Read-only: server-generated when SIP registration is enabled.
    # Deserialized from responses but stripped on serialize via
    # `_read_only_attrs` above (API rejects writes with 400 Param not allowed).
    incoming_auth_username = property(lambda self: self._attr("incoming_auth_username"))
    incoming_auth_password = property(lambda self: self._attr("incoming_auth_password"))

    codec_ids                     = _enum_list("codec_ids", Codec)
    rerouting_disconnect_code_ids = _enum_list("rerouting_disconnect_code_ids", ReroutingDisconnectCode)

    transport_protocol_id      = _enum("transport_protocol_id", TransportProtocol)
    rx_dtmf_format_id          = _enum("rx_dtmf_format_id", RxDtmfFormat)
    tx_dtmf_format_id          = _enum("tx_dtmf_format_id", TxDtmfFormat)
    sst_refresh_method_id      = _enum("sst_refresh_method_id", SstRefreshMethod)
    media_encryption_mode      = _enum("media_encryption_mode", MediaEncryptionMode)
    stir_shaken_mode           = _enum("stir_shaken_mode", StirShakenMode)
    diversion_relay_policy     = _enum("diversion_relay_policy", DiversionRelayPolicy)
    diversion_inject_mode      = _enum("diversion_inject_mode", DiversionInjectMode)
    network_protocol_priority  = _enum("network_protocol_priority", NetworkProtocolPriority)


TrunkConfiguration.register("sip_configurations", SipConfiguration)
