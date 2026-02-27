from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, Repository


class Address(DidwwApiModel):
    _writable_attrs = {"city_name", "postal_code", "address", "description"}

    city_name = SafeAttributeField("city_name")
    postal_code = SafeAttributeField("postal_code")
    address = SafeAttributeField("address")
    description = SafeAttributeField("description")
    created_at = SafeAttributeField("created_at")
    verified = SafeAttributeField("verified")

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
