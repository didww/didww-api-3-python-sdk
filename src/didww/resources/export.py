from didww.enums import ExportStatus, ExportType, CallbackMethod
from didww.resources.base import DidwwApiModel, SafeAttributeField, EnumAttributeField, Repository


class Export(DidwwApiModel):
    _writable_attrs = {"filters", "export_type", "callback_url", "callback_method"}

    status = EnumAttributeField("status", ExportStatus)
    created_at = SafeAttributeField("created_at")
    url = SafeAttributeField("url")
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    export_type = EnumAttributeField("export_type", ExportType)
    filters = SafeAttributeField("filters")

    class Meta:
        type = "exports"


class ExportRepository(Repository):
    _resource_class = Export
    _path = "exports"
