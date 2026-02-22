import importlib
from enum import Enum

from jsonapi_requests.orm.api import OrmApi
from jsonapi_requests.orm.api_model import ApiModel
from jsonapi_requests.orm.fields import AttributeField, RelationField
from jsonapi_requests.data import JsonApiResponse
from didww.enums import enum_value, to_enum

# Map of JSON:API types to module:class for lazy loading
_TYPE_MAP = {
    "areas": "didww.resources.area:Area",
    "available_dids": "didww.resources.available_did:AvailableDid",
    "capacity_pools": "didww.resources.capacity_pool:CapacityPool",
    "cities": "didww.resources.city:City",
    "countries": "didww.resources.country:Country",
    "dids": "didww.resources.did:Did",
    "did_groups": "didww.resources.did_group:DidGroup",
    "did_group_types": "didww.resources.did_group_type:DidGroupType",
    "did_reservations": "didww.resources.did_reservation:DidReservation",
    "identities": "didww.resources.identity:Identity",
    "nanpa_prefixes": "didww.resources.nanpa_prefix:NanpaPrefix",
    "orders": "didww.resources.order:Order",
    "pops": "didww.resources.pop:Pop",
    "proofs": "didww.resources.proof:Proof",
    "proof_types": "didww.resources.proof_type:ProofType",
    "regions": "didww.resources.region:Region",
    "requirements": "didww.resources.requirement:Requirement",
    "shared_capacity_groups": "didww.resources.shared_capacity_group:SharedCapacityGroup",
    "supporting_document_templates": "didww.resources.supporting_document_template:SupportingDocumentTemplate",
    "voice_in_trunks": "didww.resources.voice_in_trunk:VoiceInTrunk",
    "voice_in_trunk_groups": "didww.resources.voice_in_trunk_group:VoiceInTrunkGroup",
    "voice_out_trunks": "didww.resources.voice_out_trunk:VoiceOutTrunk",
    "addresses": "didww.resources.address:Address",
    "address_verifications": "didww.resources.address_verification:AddressVerification",
    "permanent_supporting_documents": "didww.resources.permanent_supporting_document:PermanentSupportingDocument",
    "stock_keeping_units": "didww.resources.stock_keeping_unit:StockKeepingUnit",
    "qty_based_pricings": "didww.resources.qty_based_pricing:QtyBasedPricing",
    "balances": "didww.resources.balance:Balance",
    "encrypted_files": "didww.resources.encrypted_file:EncryptedFile",
    "exports": "didww.resources.export:Export",
    "public_keys": "didww.resources.public_key:PublicKey",
    "requirement_validations": "didww.resources.requirement_validation:RequirementValidation",
    "voice_out_trunk_regenerate_credentials": "didww.resources.voice_out_trunk_regenerate_credential:VoiceOutTrunkRegenerateCredential",
}

# Shared ORM API instance (no HTTP — we handle that in client.py)
api = OrmApi(api=None)

# Patch the TypeRegistry to lazy-load resource modules for unknown types.
_original_get_model = api.type_registry.get_model.__func__


def _lazy_get_model(self, type):
    try:
        return _original_get_model(self, type)
    except KeyError:
        entry = _TYPE_MAP.get(type)
        if entry is None:
            raise
        module_path, class_name = entry.rsplit(":", 1)
        importlib.import_module(module_path)
        return _original_get_model(self, type)


import types
api.type_registry.get_model = types.MethodType(_lazy_get_model, api.type_registry)


class SafeAttributeField(AttributeField):
    """Returns None for missing keys instead of KeyError."""

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        return instance.attributes.get(self.source)


class EnumAttributeField(SafeAttributeField):
    """AttributeField that serializes/deserializes Enum values."""

    def __init__(self, source, enum_cls):
        super().__init__(source)
        self.enum_cls = enum_cls

    def __get__(self, instance, type=None):
        raw = super().__get__(instance, type)
        if instance is None:
            return self
        return to_enum(self.enum_cls, raw)

    def __set__(self, instance, value):
        if isinstance(value, Enum):
            instance.attributes[self.source] = enum_value(value)
            return
        instance.attributes[self.source] = value


class ExclusiveRelationField(RelationField):
    """RelationField that nullifies another relationship when set."""

    def __init__(self, source, excludes):
        super().__init__(source)
        self.excludes = excludes

    def __set__(self, instance, value):
        super().__set__(instance, value)
        instance._null_relationship(self.excludes)


class DidwwApiModel(ApiModel):
    """Base class for all DIDWW resources."""

    _writable_attrs = None

    class Meta:
        api = api

    @classmethod
    def build(cls, id, **attributes):
        obj = cls()
        obj.id = id
        for k, v in attributes.items():
            obj.attributes[k] = v
        return obj

    @classmethod
    def from_jsonapi(cls, data):
        """Backward-compatible factory from a JSON:API resource dict."""
        response = JsonApiResponse.from_data({"data": data})
        return cls.from_response_content(response)

    def to_jsonapi(self, include_id=False):
        """Serialize for create/update, respecting _writable_attrs."""
        attrs = dict(self.attributes)
        attrs = {k: v for k, v in attrs.items() if v is not None}
        if self._writable_attrs is not None:
            attrs = {k: v for k, v in attrs.items() if k in self._writable_attrs}
        doc = {"type": self.type, "attributes": attrs}
        if include_id and self.id:
            doc["id"] = self.id
        rels = self.raw_object.relationships.as_data()
        null_rels = getattr(self, "_null_rels", None)
        if null_rels:
            for key in null_rels:
                rels[key] = {"data": None}
        if rels:
            doc["relationships"] = rels
        return doc

    def _null_relationship(self, key):
        """Mark a relationship as explicitly null for serialization."""
        if not hasattr(self, "_null_rels"):
            self._null_rels = set()
        self._null_rels.add(key)

    def _relationship_id(self, key):
        """Get the ID from a to-one relationship without resolving it."""
        try:
            rel = self.relationships[key]
            if rel.data and rel.data.id is not None:
                return rel.data.id
        except (KeyError, AttributeError):
            pass
        return None

    def _relationship_ids(self, key):
        """Get IDs from a to-many relationship without resolving them."""
        try:
            rel = self.relationships[key]
            return [item.id for item in rel.data if item.id is not None]
        except (KeyError, AttributeError, TypeError):
            return []


class ApiResponse:
    def __init__(self, data, meta=None):
        self.data = data
        self.meta = meta or {}


class ReadOnlyRepository:
    _resource_class = None
    _path = None

    def __init__(self, client):
        self.client = client

    def list(self, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(self._path, params=query)
        response = JsonApiResponse.from_data(body)
        resources = self._resource_class.from_response_content(response)
        if not isinstance(resources, list):
            resources = [resources]
        return ApiResponse(data=resources, meta=body.get("meta", {}))

    def find(self, resource_id, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(f"{self._path}/{resource_id}", params=query)
        response = JsonApiResponse.from_data(body)
        resource = self._resource_class.from_response_content(response)
        return ApiResponse(data=resource, meta=body.get("meta", {}))


class SingletonRepository:
    _resource_class = None
    _path = None

    def __init__(self, client):
        self.client = client

    def find(self, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(self._path, params=query)
        response = JsonApiResponse.from_data(body)
        resource = self._resource_class.from_response_content(response)
        return ApiResponse(data=resource, meta=body.get("meta", {}))


class Repository(ReadOnlyRepository):
    def create(self, resource, params=None):
        doc = {"data": resource.to_jsonapi()}
        query = params.to_dict() if params else None
        body = self.client.post(self._path, doc, params=query)
        response = JsonApiResponse.from_data(body)
        created = self._resource_class.from_response_content(response)
        return ApiResponse(data=created, meta=body.get("meta", {}))

    def update(self, resource, params=None):
        doc = {"data": resource.to_jsonapi(include_id=True)}
        query = params.to_dict() if params else None
        body = self.client.patch(f"{self._path}/{resource.id}", doc, params=query)
        response = JsonApiResponse.from_data(body)
        updated = self._resource_class.from_response_content(response)
        return ApiResponse(data=updated, meta=body.get("meta", {}))

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")


class CreateOnlyRepository(ReadOnlyRepository):
    def create(self, resource, params=None):
        doc = {"data": resource.to_jsonapi()}
        query = params.to_dict() if params else None
        body = self.client.post(self._path, doc, params=query)
        response = JsonApiResponse.from_data(body)
        created = self._resource_class.from_response_content(response)
        return ApiResponse(data=created, meta=body.get("meta", {}))

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
