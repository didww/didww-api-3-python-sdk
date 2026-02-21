class BaseResource:
    _type = None
    _writable_attrs = None

    def __init__(self, id=None, attributes=None, relationships=None, meta=None):
        self.id = id
        self._attributes = attributes or {}
        self._relationships = relationships or {}
        self._meta = meta or {}

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
        return ApiResponse(
            data=resources,
            meta=body.get("meta", {}),
            included=body.get("included", []),
        )

    def find(self, resource_id, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(f"{self._path}/{resource_id}", params=query)
        resource = self._resource_class.from_jsonapi(body["data"])
        return ApiResponse(
            data=resource,
            meta=body.get("meta", {}),
            included=body.get("included", []),
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
        return ApiResponse(
            data=resource,
            meta=body.get("meta", {}),
            included=body.get("included", []),
        )


class Repository(ReadOnlyRepository):
    def create(self, resource):
        doc = {"data": resource.to_jsonapi()}
        body = self.client.post(self._path, doc)
        created = self._resource_class.from_jsonapi(body["data"])
        return ApiResponse(
            data=created,
            meta=body.get("meta", {}),
            included=body.get("included", []),
        )

    def update(self, resource):
        doc = {"data": resource.to_jsonapi(include_id=True)}
        body = self.client.patch(f"{self._path}/{resource.id}", doc)
        updated = self._resource_class.from_jsonapi(body["data"])
        return ApiResponse(
            data=updated,
            meta=body.get("meta", {}),
            included=body.get("included", []),
        )

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")


class CreateOnlyRepository(ReadOnlyRepository):
    def create(self, resource):
        doc = {"data": resource.to_jsonapi()}
        body = self.client.post(self._path, doc)
        created = self._resource_class.from_jsonapi(body["data"])
        return ApiResponse(
            data=created,
            meta=body.get("meta", {}),
            included=body.get("included", []),
        )

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
