from didww.resources.base import BaseResource, ReadOnlyRepository


class NanpaPrefix(BaseResource):
    _type = "nanpa_prefixes"

    @property
    def npa(self):
        return self._attr("npa")

    @property
    def nxx(self):
        return self._attr("nxx")


class NanpaPrefixRepository(ReadOnlyRepository):
    _resource_class = NanpaPrefix
    _path = "nanpa_prefixes"
