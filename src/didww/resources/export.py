from didww.enums import ExportStatus, ExportType, CallbackMethod
from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, EnumAttributeField, Repository


class Export(DidwwApiModel):
    """CDR or SMS record export.

    ``export_type`` (ExportType) selects the records; ``filters`` narrows them
    (see ``Export.filters`` for the accepted keys).
    """

    _writable_attrs = {"filters", "export_type", "callback_url", "callback_method", "external_reference_id"}

    status = EnumAttributeField("status", ExportStatus)
    created_at = DatetimeAttributeField("created_at")
    url = SafeAttributeField("url")
    callback_url = SafeAttributeField("callback_url")
    callback_method = EnumAttributeField("callback_method", CallbackMethod)
    export_type = EnumAttributeField("export_type", ExportType)
    external_reference_id = SafeAttributeField("external_reference_id")

    class Meta:
        type = "exports"

    @property
    def filters(self):
        """Export filters, a dict sent as is.

        Every export type: ``from`` (inclusive) and ``to`` (exclusive) as
        ``"YYYY-MM-DD HH:MM:SS"`` in UTC.

        - ``cdr_in``: ``did_number``, ``source_number``, ``source_number_out``,
          ``source_country_iso``.
        - ``cdr_out``: ``voice_out_trunk.id``, ``source``, ``cli``, ``destination``.
        - ``sms_in`` and ``sms_out``: ``source_address_eq``,
          ``source_address_cont``, ``destination_address_eq``,
          ``destination_address_cont``, ``status``, ``sms_id``, ``sms_trunk.id``
          (a string or a list).
        - ``sms_in`` only: ``trunk_type`` (ExportTrunkType, a value or a list).
        - ``sms_out`` only: ``service_type`` (``"a2p"`` or ``"p2p"``),
          ``sender_id_verification.id`` (a string or a list).

        The API rejects any other key. ``year``, ``month`` and ``day`` only
        appear on exports created with earlier API versions.
        """
        return self.attributes.get("filters")

    @filters.setter
    def filters(self, value):
        self.attributes["filters"] = value

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
