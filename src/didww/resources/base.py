_type_registry = {}

_all_types_registered = False


def _ensure_all_types_registered():
    global _all_types_registered
    if _all_types_registered:
        return
    _all_types_registered = True
    import didww.resources.area  # noqa: F401
    import didww.resources.available_did  # noqa: F401
    import didww.resources.capacity_pool  # noqa: F401
    import didww.resources.city  # noqa: F401
    import didww.resources.country  # noqa: F401
    import didww.resources.did  # noqa: F401
    import didww.resources.did_group  # noqa: F401
    import didww.resources.did_group_type  # noqa: F401
    import didww.resources.did_reservation  # noqa: F401
    import didww.resources.identity  # noqa: F401
    import didww.resources.nanpa_prefix  # noqa: F401
    import didww.resources.order  # noqa: F401
    import didww.resources.pop  # noqa: F401
    import didww.resources.proof  # noqa: F401
    import didww.resources.proof_type  # noqa: F401
    import didww.resources.region  # noqa: F401
    import didww.resources.requirement  # noqa: F401
    import didww.resources.shared_capacity_group  # noqa: F401
    import didww.resources.supporting_document_template  # noqa: F401
    import didww.resources.voice_in_trunk  # noqa: F401
    import didww.resources.voice_in_trunk_group  # noqa: F401
    import didww.resources.voice_out_trunk  # noqa: F401
    import didww.resources.address  # noqa: F401
    import didww.resources.address_verification  # noqa: F401
    import didww.resources.permanent_supporting_document  # noqa: F401
    import didww.resources.stock_keeping_unit  # noqa: F401
    import didww.resources.qty_based_pricing  # noqa: F401
    import didww.resources.balance  # noqa: F401
    import didww.resources.encrypted_file  # noqa: F401
    import didww.resources.export  # noqa: F401
    import didww.resources.public_key  # noqa: F401
    import didww.resources.requirement_validation  # noqa: F401
    import didww.resources.voice_out_trunk_regenerate_credential  # noqa: F401


def _build_included_map(included_list):
    _ensure_all_types_registered()
    included_map = {}
    objects = []
    for item in included_list:
        item_type = item.get("type")
        item_id = item.get("id")
        cls = _type_registry.get(item_type)
        if cls is not None:
            obj = cls.from_jsonapi(item)
            included_map[f"{item_type}:{item_id}"] = obj
            objects.append(obj)
    for obj in objects:
        obj._resolve_includes(included_map)
    return included_map


def _resolve_response(resources, included_list):
    if not included_list:
        return
    included_map = _build_included_map(included_list)
    if isinstance(resources, list):
        for r in resources:
            r._resolve_includes(included_map)
    else:
        resources._resolve_includes(included_map)


class BaseResource:
    _type = None
    _writable_attrs = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._type is not None:
            _type_registry[cls._type] = cls

    def __init__(self, id=None, attributes=None, relationships=None, meta=None):
        self.id = id
        self._attributes = attributes or {}
        self._relationships = relationships or {}
        self._meta = meta or {}
        self._included_cache = {}

    def _attr(self, key):
        return self._attributes.get(key)

    def _set_attr(self, key, value):
        self._attributes[key] = value

    def _relationship_id(self, key):
        rel = self._relationships.get(key, {})
        data = rel.get("data") if isinstance(rel, dict) else None
        if data and isinstance(data, dict):
            return data.get("id")
        return None

    def _relationship_ids(self, key):
        rel = self._relationships.get(key, {})
        data = rel.get("data") if isinstance(rel, dict) else None
        if data and isinstance(data, list):
            return [item.get("id") for item in data]
        return []

    def _set_relationship(self, key, resource):
        self._relationships[key] = {
            "data": {"type": resource._type, "id": resource.id}
        }

    def _set_relationships(self, key, resources):
        self._relationships[key] = {
            "data": [{"type": r._type, "id": r.id} for r in resources]
        }

    def _resolve_includes(self, included_map):
        for key, rel in self._relationships.items():
            data = rel.get("data") if isinstance(rel, dict) else None
            if data is None:
                continue
            if isinstance(data, dict):
                self._included_cache[key] = included_map.get(f"{data['type']}:{data['id']}")
            elif isinstance(data, list):
                self._included_cache[key] = [
                    included_map[f"{item['type']}:{item['id']}"]
                    for item in data if f"{item['type']}:{item['id']}" in included_map
                ]

    def _get_relationship(self, key):
        return self._included_cache.get(key)

    def _get_relationships(self, key):
        return self._included_cache.get(key, [])

    def to_jsonapi(self, include_id=False):
        attrs = {k: v for k, v in self._attributes.items() if v is not None}
        if self._writable_attrs is not None:
            attrs = {k: v for k, v in attrs.items() if k in self._writable_attrs}
        doc = {"type": self._type, "attributes": attrs}
        if include_id and self.id:
            doc["id"] = self.id
        if self._relationships:
            doc["relationships"] = dict(self._relationships)
        return doc

    @classmethod
    def build(cls, id, **attributes):
        return cls(id=id, attributes=attributes if attributes else {})

    @classmethod
    def from_jsonapi(cls, data):
        return cls(
            id=data.get("id"),
            attributes=data.get("attributes", {}),
            relationships=data.get("relationships", {}),
            meta=data.get("meta", {}),
        )


class ApiResponse:
    def __init__(self, data, meta=None, included=None):
        self.data = data
        self.meta = meta or {}
        self.included = included or []


class ReadOnlyRepository:
    _resource_class = None
    _path = None

    def __init__(self, client):
        self.client = client

    def list(self, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(self._path, params=query)
        data_list = body.get("data", [])
        resources = [self._resource_class.from_jsonapi(d) for d in data_list]
        included = body.get("included", [])
        _resolve_response(resources, included)
        return ApiResponse(
            data=resources,
            meta=body.get("meta", {}),
            included=included,
        )

    def find(self, resource_id, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(f"{self._path}/{resource_id}", params=query)
        resource = self._resource_class.from_jsonapi(body["data"])
        included = body.get("included", [])
        _resolve_response(resource, included)
        return ApiResponse(
            data=resource,
            meta=body.get("meta", {}),
            included=included,
        )


class SingletonRepository:
    _resource_class = None
    _path = None

    def __init__(self, client):
        self.client = client

    def find(self, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(self._path, params=query)
        resource = self._resource_class.from_jsonapi(body["data"])
        included = body.get("included", [])
        _resolve_response(resource, included)
        return ApiResponse(
            data=resource,
            meta=body.get("meta", {}),
            included=included,
        )


class Repository(ReadOnlyRepository):
    def create(self, resource, params=None):
        doc = {"data": resource.to_jsonapi()}
        query = params.to_dict() if params else None
        body = self.client.post(self._path, doc, params=query)
        created = self._resource_class.from_jsonapi(body["data"])
        included = body.get("included", [])
        _resolve_response(created, included)
        return ApiResponse(
            data=created,
            meta=body.get("meta", {}),
            included=included,
        )

    def update(self, resource, params=None):
        doc = {"data": resource.to_jsonapi(include_id=True)}
        query = params.to_dict() if params else None
        body = self.client.patch(f"{self._path}/{resource.id}", doc, params=query)
        updated = self._resource_class.from_jsonapi(body["data"])
        included = body.get("included", [])
        _resolve_response(updated, included)
        return ApiResponse(
            data=updated,
            meta=body.get("meta", {}),
            included=included,
        )

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")


class CreateOnlyRepository(ReadOnlyRepository):
    def create(self, resource, params=None):
        doc = {"data": resource.to_jsonapi()}
        query = params.to_dict() if params else None
        body = self.client.post(self._path, doc, params=query)
        created = self._resource_class.from_jsonapi(body["data"])
        included = body.get("included", [])
        _resolve_response(created, included)
        return ApiResponse(
            data=created,
            meta=body.get("meta", {}),
            included=included,
        )

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
