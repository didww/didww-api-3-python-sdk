from didww.resources.configuration.base import TrunkConfiguration
from didww.enums import Codec, enum_value_list, to_enum_list


class H323Configuration(TrunkConfiguration):
    _type = "h323_configurations"

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


TrunkConfiguration.register("h323_configurations", H323Configuration)
