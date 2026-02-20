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

    @property
    def auth_enabled(self):
        return self._attr("auth_enabled")

    @property
    def resolve_ruri(self):
        return self._attr("resolve_ruri")


TrunkConfiguration.register("sip_configurations", SipConfiguration)
