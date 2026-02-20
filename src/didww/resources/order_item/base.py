class OrderItem:
    _type = None
    _type_map = {}

    def __init__(self, attributes=None):
        self._attributes = attributes or {}

    def _attr(self, key):
        return self._attributes.get(key)

    def _set_attr(self, key, value):
        self._attributes[key] = value

    def to_jsonapi(self):
        attrs = {k: v for k, v in self._attributes.items() if v is not None}
        return {
            "type": self._type,
            "attributes": attrs,
        }

    @classmethod
    def from_jsonapi(cls, data):
        item_type = data.get("type")
        item_cls = cls._type_map.get(item_type, cls)
        instance = item_cls(attributes=data.get("attributes", {}))
        if instance._type is None:
            instance._type = item_type
        return instance

    @classmethod
    def register(cls, type_name, item_class):
        cls._type_map[type_name] = item_class
