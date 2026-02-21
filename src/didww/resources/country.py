from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class Country(DidwwApiModel):
    name = SafeAttributeField("name")
    prefix = SafeAttributeField("prefix")
    iso = SafeAttributeField("iso")

    class Meta:
        type = "countries"


class CountryRepository(ReadOnlyRepository):
    _resource_class = Country
    _path = "countries"
