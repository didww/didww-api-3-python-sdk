from didww.resources.configuration.base import TrunkConfiguration
from didww.enums import Codec, enum_value_list, to_enum_list


class Iax2Configuration(TrunkConfiguration):
    _type = "iax2_configurations"

    @property
    def dst(self):
        return self._attr("dst")

    @dst.setter
    def dst(self, value):
        self._set_attr("dst", value)

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
        return to_enum_list(Codec, self._attr("codec_ids"))

    @codec_ids.setter
    def codec_ids(self, value):
        self._set_attr("codec_ids", enum_value_list(value))

    @property
    def auth_enabled(self):
        return self._attr("auth_enabled")

    @property
    def auth_user(self):
        return self._attr("auth_user")

    @property
    def auth_password(self):
        return self._attr("auth_password")


TrunkConfiguration.register("iax2_configurations", Iax2Configuration)
