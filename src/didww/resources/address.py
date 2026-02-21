from didww.resources.base import BaseResource, Repository


class Address(BaseResource):
    _type = "addresses"
    _writable_attrs = {"city_name", "postal_code", "address", "description"}

    @property
    def city_name(self):
        return self._attr("city_name")

    @city_name.setter
    def city_name(self, value):
        self._set_attr("city_name", value)

    @property
    def postal_code(self):
        return self._attr("postal_code")

    @postal_code.setter
    def postal_code(self, value):
        self._set_attr("postal_code", value)

    @property
    def address(self):
        return self._attr("address")

    @address.setter
    def address(self, value):
        self._set_attr("address", value)

    @property
    def description(self):
        return self._attr("description")

    @description.setter
    def description(self, value):
        self._set_attr("description", value)

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def verified(self):
        return self._attr("verified")

    def set_country(self, country):
        self._set_relationship("country", country)

    def set_identity(self, identity):
        self._set_relationship("identity", identity)

    def country(self):
        return self._get_relationship("country")

    def identity(self):
        return self._get_relationship("identity")

    def area(self):
        return self._get_relationship("area")

    def city(self):
        return self._get_relationship("city")


class AddressRepository(Repository):
    _resource_class = Address
    _path = "addresses"
