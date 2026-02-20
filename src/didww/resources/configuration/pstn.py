from didww.resources.configuration.base import TrunkConfiguration


class PstnConfiguration(TrunkConfiguration):
    _type = "pstn_configurations"

    @property
    def dst(self):
        return self._attr("dst")

    @dst.setter
    def dst(self, value):
        self._set_attr("dst", value)


TrunkConfiguration.register("pstn_configurations", PstnConfiguration)
