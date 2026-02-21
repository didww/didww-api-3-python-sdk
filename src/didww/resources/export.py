from didww.resources.base import DidwwApiModel, SafeAttributeField, Repository


class Export(DidwwApiModel):
    _writable_attrs = {"filters", "export_type", "callback_url", "callback_method"}

    status = SafeAttributeField("status")
    created_at = SafeAttributeField("created_at")
    url = SafeAttributeField("url")
    callback_url = SafeAttributeField("callback_url")
    callback_method = SafeAttributeField("callback_method")
    export_type = SafeAttributeField("export_type")
    filters = SafeAttributeField("filters")

    class Meta:
        type = "exports"


class ExportRepository(Repository):
    _resource_class = Export
    _path = "exports"
