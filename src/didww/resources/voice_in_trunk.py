from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository
from didww.resources.configuration.base import TrunkConfiguration

# Import to register types
import didww.resources.configuration.sip  # noqa: F401
import didww.resources.configuration.h323  # noqa: F401
import didww.resources.configuration.iax2  # noqa: F401
import didww.resources.configuration.pstn  # noqa: F401


class VoiceInTrunk(DidwwApiModel):
    _writable_attrs = {
        "priority", "capacity_limit", "weight", "name", "cli_format",
        "cli_prefix", "description", "ringing_timeout", "configuration",
    }

    name = SafeAttributeField("name")
    priority = SafeAttributeField("priority")
    weight = SafeAttributeField("weight")
    capacity_limit = SafeAttributeField("capacity_limit")
    cli_format = SafeAttributeField("cli_format")
    cli_prefix = SafeAttributeField("cli_prefix")
    description = SafeAttributeField("description")
    ringing_timeout = SafeAttributeField("ringing_timeout")
    created_at = SafeAttributeField("created_at")

    pop = RelationField("pop")
    voice_in_trunk_group = RelationField("voice_in_trunk_group")

    class Meta:
        type = "voice_in_trunks"

    @property
    def configuration(self):
        config_data = self.attributes.get("configuration")
        if config_data and isinstance(config_data, dict):
            return TrunkConfiguration.from_jsonapi(config_data)
        return config_data

    @configuration.setter
    def configuration(self, config):
        if isinstance(config, TrunkConfiguration):
            self.attributes["configuration"] = config.to_jsonapi()
        else:
            self.attributes["configuration"] = config


class VoiceInTrunkRepository(Repository):
    _resource_class = VoiceInTrunk
    _path = "voice_in_trunks"
