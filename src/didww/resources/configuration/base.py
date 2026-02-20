class TrunkConfiguration:
    _type = None
    _type_map = {}

    def __init__(self, attributes=None):
        self._attributes = attributes or {}

    def _attr(self, key):
        return self._attributes.get(key)

    def _set_attr(self, key, value):
        self._attributes[key] = value

    def to_jsonapi(self):
        return {
            "type": self._type,
            "attributes": dict(self._attributes),
        }

    @classmethod
    def from_jsonapi(cls, data):
        config_type = data.get("type")
        config_cls = cls._type_map.get(config_type, cls)
        return config_cls(attributes=data.get("attributes", {}))

    @classmethod
    def register(cls, type_name, config_class):
        cls._type_map[type_name] = config_class
