from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, Repository


class Address(DidwwApiModel):
    _writable_attrs = {"city_name", "postal_code", "address", "description", "external_reference_id"}

    city_name = SafeAttributeField("city_name")
    postal_code = SafeAttributeField("postal_code")
    address = SafeAttributeField("address")
    description = SafeAttributeField("description")
    created_at = DatetimeAttributeField("created_at")
    verified = SafeAttributeField("verified")
    external_reference_id = SafeAttributeField("external_reference_id")

    country = RelationField("country")
    identity = RelationField("identity")
    proofs = RelationField("proofs")
    area = RelationField("area")
    city = RelationField("city")

    class Meta:
        type = "addresses"


class AddressRepository(Repository):
    _resource_class = Address
    _path = "addresses"
