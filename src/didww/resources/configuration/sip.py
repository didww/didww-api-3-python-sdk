from didww.resources.configuration.base import TrunkConfiguration


class SipConfiguration(TrunkConfiguration):
    _type = "sip_configurations"

    @property
    def username(self):
        return self._attr("username")

    @username.setter
    def username(self, value):
        self._set_attr("username", value)

    @property
    def host(self):
        return self._attr("host")

    @host.setter
    def host(self, value):
        self._set_attr("host", value)

    @property
    def port(self):
        return self._attr("port")

    @port.setter
    def port(self, value):
        self._set_attr("port", value)

    @property
    def codec_ids(self):
        return self._attr("codec_ids")

    @codec_ids.setter
    def codec_ids(self, value):
        self._set_attr("codec_ids", value)

    @property
    def transport_protocol_id(self):
        return self._attr("transport_protocol_id")

    @transport_protocol_id.setter
    def transport_protocol_id(self, value):
        self._set_attr("transport_protocol_id", value)

    @property
    def auth_enabled(self):
        return self._attr("auth_enabled")

    @auth_enabled.setter
    def auth_enabled(self, value):
        self._set_attr("auth_enabled", value)

    @property
    def resolve_ruri(self):
        return self._attr("resolve_ruri")

    @resolve_ruri.setter
    def resolve_ruri(self, value):
        self._set_attr("resolve_ruri", value)

    @property
    def auth_user(self):
        return self._attr("auth_user")

    @auth_user.setter
    def auth_user(self, value):
        self._set_attr("auth_user", value)

    @property
    def auth_password(self):
        return self._attr("auth_password")

    @auth_password.setter
    def auth_password(self, value):
        self._set_attr("auth_password", value)

    @property
    def auth_from_user(self):
        return self._attr("auth_from_user")

    @auth_from_user.setter
    def auth_from_user(self, value):
        self._set_attr("auth_from_user", value)

    @property
    def auth_from_domain(self):
        return self._attr("auth_from_domain")

    @auth_from_domain.setter
    def auth_from_domain(self, value):
        self._set_attr("auth_from_domain", value)

    @property
    def rx_dtmf_format_id(self):
        return self._attr("rx_dtmf_format_id")

    @rx_dtmf_format_id.setter
    def rx_dtmf_format_id(self, value):
        self._set_attr("rx_dtmf_format_id", value)

    @property
    def tx_dtmf_format_id(self):
        return self._attr("tx_dtmf_format_id")

    @tx_dtmf_format_id.setter
    def tx_dtmf_format_id(self, value):
        self._set_attr("tx_dtmf_format_id", value)

    @property
    def sst_enabled(self):
        return self._attr("sst_enabled")

    @sst_enabled.setter
    def sst_enabled(self, value):
        self._set_attr("sst_enabled", value)

    @property
    def sst_min_timer(self):
        return self._attr("sst_min_timer")

    @sst_min_timer.setter
    def sst_min_timer(self, value):
        self._set_attr("sst_min_timer", value)

    @property
    def sst_max_timer(self):
        return self._attr("sst_max_timer")

    @sst_max_timer.setter
    def sst_max_timer(self, value):
        self._set_attr("sst_max_timer", value)

    @property
    def sst_accept_501(self):
        return self._attr("sst_accept_501")

    @sst_accept_501.setter
    def sst_accept_501(self, value):
        self._set_attr("sst_accept_501", value)

    @property
    def sst_session_expires(self):
        return self._attr("sst_session_expires")

    @sst_session_expires.setter
    def sst_session_expires(self, value):
        self._set_attr("sst_session_expires", value)

    @property
    def sst_refresh_method_id(self):
        return self._attr("sst_refresh_method_id")

    @sst_refresh_method_id.setter
    def sst_refresh_method_id(self, value):
        self._set_attr("sst_refresh_method_id", value)

    @property
    def sip_timer_b(self):
        return self._attr("sip_timer_b")

    @sip_timer_b.setter
    def sip_timer_b(self, value):
        self._set_attr("sip_timer_b", value)

    @property
    def dns_srv_failover_timer(self):
        return self._attr("dns_srv_failover_timer")

    @dns_srv_failover_timer.setter
    def dns_srv_failover_timer(self, value):
        self._set_attr("dns_srv_failover_timer", value)

    @property
    def rtp_ping(self):
        return self._attr("rtp_ping")

    @rtp_ping.setter
    def rtp_ping(self, value):
        self._set_attr("rtp_ping", value)

    @property
    def force_symmetric_rtp(self):
        return self._attr("force_symmetric_rtp")

    @force_symmetric_rtp.setter
    def force_symmetric_rtp(self, value):
        self._set_attr("force_symmetric_rtp", value)

    @property
    def rerouting_disconnect_code_ids(self):
        return self._attr("rerouting_disconnect_code_ids")

    @rerouting_disconnect_code_ids.setter
    def rerouting_disconnect_code_ids(self, value):
        self._set_attr("rerouting_disconnect_code_ids", value)

    @property
    def max_transfers(self):
        return self._attr("max_transfers")

    @max_transfers.setter
    def max_transfers(self, value):
        self._set_attr("max_transfers", value)

    @property
    def max_30x_redirects(self):
        return self._attr("max_30x_redirects")

    @max_30x_redirects.setter
    def max_30x_redirects(self, value):
        self._set_attr("max_30x_redirects", value)

    @property
    def media_encryption_mode(self):
        return self._attr("media_encryption_mode")

    @media_encryption_mode.setter
    def media_encryption_mode(self, value):
        self._set_attr("media_encryption_mode", value)

    @property
    def stir_shaken_mode(self):
        return self._attr("stir_shaken_mode")

    @stir_shaken_mode.setter
    def stir_shaken_mode(self, value):
        self._set_attr("stir_shaken_mode", value)

    @property
    def allowed_rtp_ips(self):
        return self._attr("allowed_rtp_ips")

    @allowed_rtp_ips.setter
    def allowed_rtp_ips(self, value):
        self._set_attr("allowed_rtp_ips", value)


TrunkConfiguration.register("sip_configurations", SipConfiguration)
