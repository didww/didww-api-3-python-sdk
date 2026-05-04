class TrunkConfiguration:
    _type = None
    _type_map = {}
    # Set of attribute keys that are deserialized from server responses
    # but MUST NOT be sent in POST/PATCH request bodies. Subclasses should
    # extend this set to mark server-generated read-only fields. The server
    # rejects writes to these keys with 400 Param not allowed.
    _read_only_attrs = frozenset()
    # Set of attribute keys whose values are credentials/secrets. The wire
    # format is unchanged — to_jsonapi still emits the real values — but
    # __repr__ redacts them so default logging / error reports / REPL
    # echoes never leak credentials downstream. Subclasses extend this set.
    _sensitive_attrs = frozenset()

    def __init__(self, attributes=None):
        self._attributes = attributes or {}

    def _attr(self, key):
        return self._attributes.get(key)

    def _set_attr(self, key, value):
        self._attributes[key] = value

    def to_jsonapi(self):
        attrs = {
            k: v
            for k, v in self._attributes.items()
            if k not in self._read_only_attrs
        }
        return {
            "type": self._type,
            "attributes": attrs,
        }

    def __repr__(self):
        parts = []
        for key, value in self._attributes.items():
            if key in self._sensitive_attrs and value is not None:
                value = "[FILTERED]"
            parts.append(f"{key}={value!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"

    @classmethod
    def from_jsonapi(cls, data):
        config_type = data.get("type")
        config_cls = cls._type_map.get(config_type, cls)
        return config_cls(attributes=data.get("attributes", {}))

    @classmethod
    def register(cls, type_name, config_class):
        cls._type_map[type_name] = config_class
