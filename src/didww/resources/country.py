from didww.resources.base import BaseResource, ReadOnlyRepository


class Country(BaseResource):
    _type = "countries"

    @property
    def name(self):
        return self._attr("name")

    @property
    def prefix(self):
        return self._attr("prefix")

    @property
    def iso(self):
        return self._attr("iso")


class CountryRepository(ReadOnlyRepository):
    _resource_class = Country
    _path = "countries"
