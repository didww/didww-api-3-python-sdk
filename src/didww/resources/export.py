from didww.resources.base import BaseResource, Repository


class Export(BaseResource):
    _type = "exports"
    _writable_attrs = {"filters", "export_type", "callback_url", "callback_method"}

    @property
    def status(self):
        return self._attr("status")

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def url(self):
        return self._attr("url")

    @property
    def callback_url(self):
        return self._attr("callback_url")

    @property
    def callback_method(self):
        return self._attr("callback_method")

    @property
    def export_type(self):
        return self._attr("export_type")

    @export_type.setter
    def export_type(self, value):
        self._set_attr("export_type", value)

    @property
    def filters(self):
        return self._attr("filters")

    @filters.setter
    def filters(self, value):
        self._set_attr("filters", value)


class ExportRepository(Repository):
    _resource_class = Export
    _path = "exports"
