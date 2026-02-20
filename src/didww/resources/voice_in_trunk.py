from didww.resources.base import BaseResource, Repository
from didww.resources.configuration.base import TrunkConfiguration

# Import to register types
import didww.resources.configuration.sip  # noqa: F401
import didww.resources.configuration.h323  # noqa: F401
import didww.resources.configuration.iax2  # noqa: F401
import didww.resources.configuration.pstn  # noqa: F401


class VoiceInTrunk(BaseResource):
    _type = "voice_in_trunks"
    _writable_attrs = {"priority", "capacity_limit", "weight", "name", "cli_format",
                       "cli_prefix", "description", "ringing_timeout", "configuration"}

    @property
    def name(self):
        return self._attr("name")

    @name.setter
    def name(self, value):
        self._set_attr("name", value)

    @property
    def priority(self):
        return self._attr("priority")

    @property
    def weight(self):
        return self._attr("weight")

    @property
    def capacity_limit(self):
        return self._attr("capacity_limit")

    @property
    def cli_format(self):
        return self._attr("cli_format")

    @property
    def cli_prefix(self):
        return self._attr("cli_prefix")

    @property
    def description(self):
        return self._attr("description")

    @property
    def ringing_timeout(self):
        return self._attr("ringing_timeout")

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def configuration(self):
        config_data = self._attr("configuration")
        if config_data and isinstance(config_data, dict):
            return TrunkConfiguration.from_jsonapi(config_data)
        return config_data

    @configuration.setter
    def configuration(self, config):
        if isinstance(config, TrunkConfiguration):
            self._set_attr("configuration", config.to_jsonapi())
        else:
            self._set_attr("configuration", config)


class VoiceInTrunkRepository(Repository):
    _resource_class = VoiceInTrunk
    _path = "voice_in_trunks"
