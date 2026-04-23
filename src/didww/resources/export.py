from didww.enums import ExportStatus, ExportType, CallbackMethod
from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, EnumAttributeField, Repository


class Export(DidwwApiModel):
    _writable_attrs = {"filters", "export_type", "callback_url", "callback_method", "external_reference_id"}

    status = EnumAttributeField("status", ExportStatus)
    created_at = DatetimeAttributeField("created_at")
    url = SafeAttributeField("url")
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    export_type = EnumAttributeField("export_type", ExportType)
    filters = SafeAttributeField("filters")
    external_reference_id = SafeAttributeField("external_reference_id")

    class Meta:
        type = "exports"

    @property
    def is_pending(self):
        return self.status == ExportStatus.PENDING

    @property
    def is_processing(self):
        return self.status == ExportStatus.PROCESSING

    @property
    def is_completed(self):
        return self.status == ExportStatus.COMPLETED


class ExportRepository(Repository):
    _resource_class = Export
    _path = "exports"
