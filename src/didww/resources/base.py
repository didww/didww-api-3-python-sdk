import functools
import importlib
from datetime import datetime, timezone
from enum import Enum

from jsonapi_requests.orm.api import OrmApi
from jsonapi_requests.orm.api_model import ApiModel
from jsonapi_requests.orm.fields import AttributeField, RelationField as OrmRelationField
from jsonapi_requests.data import Dictionary, JsonApiResponse
from didww.enums import enum_value, enum_value_list, to_enum, to_enum_list

# Map of JSON:API types to module:class for lazy loading
_TYPE_MAP = {
    "areas": "didww.resources.area:Area",
    "available_dids": "didww.resources.available_did:AvailableDid",
    "capacity_pools": "didww.resources.capacity_pool:CapacityPool",
    "cities": "didww.resources.city:City",
    "countries": "didww.resources.country:Country",
    "did_history": "didww.resources.did_history:DidHistory",
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
    "address_requirements": "didww.resources.address_requirement:AddressRequirement",
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
    "address_requirement_validations": "didww.resources.address_requirement_validation:AddressRequirementValidation",
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

    def __set__(self, instance, value):
        instance.attributes[self.source] = value


class DatetimeAttributeField(SafeAttributeField):
    """AttributeField that parses ISO 8601 datetime strings to datetime objects.

    No custom setter is defined because all current datetime fields are read-only
    (e.g. created_at). The inherited setter stores values as-is. If a writable
    datetime field is added in the future, a setter that converts datetime back
    to an ISO 8601 string should be implemented here.
    """

    def __get__(self, instance, type=None):
        raw = super().__get__(instance, type)
        if instance is None:
            return self
        if raw is None:
            return None
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))  # "Z" not supported by fromisoformat before Python 3.11


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
        else:
            instance.attributes[self.source] = value


class EnumListAttributeField(SafeAttributeField):
    """AttributeField that serializes/deserializes lists of Enum values."""

    def __init__(self, source, enum_cls):
        super().__init__(source)
        self.enum_cls = enum_cls

    def __get__(self, instance, type=None):
        raw = super().__get__(instance, type)
        if instance is None:
            return self
        return to_enum_list(self.enum_cls, raw)

    def __set__(self, instance, value):
        instance.attributes[self.source] = enum_value_list(value)


class RelationField(OrmRelationField):
    """RelationField that tracks dirty relationship writes."""

    def __set__(self, instance, value):
        super().__set__(instance, value)
        instance._mark_relationship_dirty(self.source)


class ExclusiveRelationField(RelationField):
    """RelationField that nullifies another relationship when set."""

    def __init__(self, source, excludes):
        super().__init__(source)
        self.excludes = excludes

    def __set__(self, instance, value):
        super().__set__(instance, value)
        instance._null_relationship(self.excludes)


def _touching(fn):
    """Decorator that calls self._mark_dirty(self._key) after the wrapped list method."""
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        result = fn(self, *args, **kwargs)
        self._mark_dirty(self._key)
        return result
    return wrapper


class _DirtyTrackingList(list):
    """List that marks a parent attribute key dirty on mutation."""

    def __init__(self, initial, key, mark_dirty):
        super().__init__(initial)
        self._key = key
        self._mark_dirty = mark_dirty

    __setitem__ = _touching(list.__setitem__)
    __delitem__ = _touching(list.__delitem__)
    __iadd__    = _touching(list.__iadd__)
    __imul__    = _touching(list.__imul__)
    append  = _touching(list.append)
    extend  = _touching(list.extend)
    insert  = _touching(list.insert)
    remove  = _touching(list.remove)
    pop     = _touching(list.pop)
    clear   = _touching(list.clear)
    sort    = _touching(list.sort)
    reverse = _touching(list.reverse)


class DirtyTrackingDictionary(Dictionary):
    """Dictionary that marks keys as dirty when mutated."""

    def __init__(self, initial=None, mark_dirty=None):
        super().__init__(initial or {})
        self._mark_dirty = mark_dirty

    def set_tracker(self, mark_dirty):
        self._mark_dirty = mark_dirty
        for key, value in list(self.items()):
            wrapped = self._wrap_value(key, value)
            if wrapped is not value:
                super().__setitem__(key, wrapped)

    def _touch(self, key):
        if self._mark_dirty is not None:
            self._mark_dirty(key)

    def _wrap_value(self, key, value):
        if self._mark_dirty is None:
            return value
        if isinstance(value, list) and not isinstance(value, _DirtyTrackingList):
            return _DirtyTrackingList(value, key, self._mark_dirty)
        return value

    def __setitem__(self, key, value):
        value = self._wrap_value(key, value)
        super().__setitem__(key, value)
        self._touch(key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self._touch(key)

    def clear(self):
        dirty_keys = list(self.keys())
        super().clear()
        for key in dirty_keys:
            self._touch(key)

    def pop(self, key, *args):
        result = super().pop(key, *args)
        self._touch(key)
        return result

    def popitem(self):
        key, value = super().popitem()
        self._touch(key)
        return key, value

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def update(self, *args, **kwargs):
        updates = dict(*args, **kwargs)
        for key, value in updates.items():
            self[key] = value


class DidwwApiModel(ApiModel):
    """Base class for all DIDWW resources."""

    _writable_attrs = None

    class Meta:
        api = api

    def __init__(self, raw_object=None):
        super().__init__(raw_object=raw_object)
        self._dirty_attrs = set()
        self._dirty_rels = set()
        self._install_dirty_tracking()
        self._clear_dirty_state()

    def _install_dirty_tracking(self):
        attrs = DirtyTrackingDictionary(self.raw_object.attributes)
        attrs.set_tracker(self._mark_attribute_dirty)
        self.raw_object.attributes = attrs

    def _clear_dirty_state(self):
        self._dirty_attrs.clear()
        self._dirty_rels.clear()

    def _mark_attribute_dirty(self, key):
        self._dirty_attrs.add(key)

    def _mark_relationship_dirty(self, key):
        self._dirty_rels.add(key)

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

    def to_jsonapi(self, include_id=False, dirty_only=False):
        """Serialize for create/update, respecting _writable_attrs."""
        attrs = dict(self.attributes)
        if dirty_only:
            attrs = {k: attrs.get(k) for k in self._dirty_attrs}
        else:
            attrs = {k: v for k, v in attrs.items() if v is not None}
        if self._writable_attrs is not None:
            attrs = {k: v for k, v in attrs.items() if k in self._writable_attrs}
        doc = {"type": self.type, "attributes": attrs}
        if include_id and self.id:
            doc["id"] = self.id
        rels = self.raw_object.relationships.as_data()
        if dirty_only:
            rels = {k: v for k, v in rels.items() if k in self._dirty_rels}
        if rels:
            doc["relationships"] = rels
        return doc

    def _null_relationship(self, key):
        """Write null data into the ORM relationship, like Java's field = null."""
        self.raw_object.relationships[key] = {"data": None}
        self._mark_relationship_dirty(key)



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
        resource._clear_dirty_state()
        response = JsonApiResponse.from_data(body)
        created = self._resource_class.from_response_content(response)
        return ApiResponse(data=created, meta=body.get("meta", {}))

    def update(self, resource, params=None):
        doc = {"data": resource.to_jsonapi(include_id=True, dirty_only=True)}
        query = params.to_dict() if params else None
        body = self.client.patch(f"{self._path}/{resource.id}", doc, params=query)
        resource._clear_dirty_state()
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
        resource._clear_dirty_state()
        response = JsonApiResponse.from_data(body)
        created = self._resource_class.from_response_content(response)
        return ApiResponse(data=created, meta=body.get("meta", {}))

    def delete(self, resource_id):
        self.client.delete(f"{self._path}/{resource_id}")
