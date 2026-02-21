from didww.resources.base import BaseResource, CreateOnlyRepository


class AddressVerification(BaseResource):
    _type = "address_verifications"
    _writable_attrs = {"service_description", "callback_url", "callback_method"}

    @property
    def status(self):
        return self._attr("status")

    @property
    def callback_url(self):
        return self._attr("callback_url")

    @callback_url.setter
    def callback_url(self, value):
        self._set_attr("callback_url", value)

    @property
    def callback_method(self):
        return self._attr("callback_method")

    @callback_method.setter
    def callback_method(self, value):
        self._set_attr("callback_method", value)

    @property
    def service_description(self):
        return self._attr("service_description")

    @property
    def reject_reasons(self):
        return self._attr("reject_reasons")

    @property
    def reference(self):
        return self._attr("reference")

    @property
    def created_at(self):
        return self._attr("created_at")

    def set_address(self, address):
        self._set_relationship("address", address)

    def set_dids(self, dids):
        self._set_relationships("dids", dids)

    def address(self):
        return self._get_relationship("address")

    def dids(self):
        return self._get_relationships("dids")


class AddressVerificationRepository(CreateOnlyRepository):
    _resource_class = AddressVerification
    _path = "address_verifications"
