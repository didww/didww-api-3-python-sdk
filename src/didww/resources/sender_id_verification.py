from didww.enums import SenderIdVerificationStatus, SenderType
from didww.resources.base import (
    DidwwApiModel,
    DatetimeAttributeField,
    SafeAttributeField,
    EnumAttributeField,
    RelationField,
    ReadOnlyRelationField,
    ReadOnlyRepository,
    Repository,
)


class SenderIdVerification(DidwwApiModel):
    """Sender ID verification resource.

    Only ``name`` and the ``sms_trunk`` relationship can be updated
    (``None`` unassigns the trunk; ``http_out``, ``smpp_smsc`` and
    ``smpp_esme`` trunks are accepted). A closed verification cannot be
    updated.

    Attributes:
        status (SenderIdVerificationStatus): active, changes_required, closed,
            closing_in_process, in_process or new.
        sender_type (SenderType): alphanumeric, carrier, long_code, short_code
            or toll_free.
        renew_date (str): Next renewal date as a date-only string
            (e.g. "2026-11-22"). None once closed.

    Relationships ``countries``, ``dids``, ``order``, ``identity`` and
    ``address`` are read-only.

    Resource-level meta: setup_price, monthly_price (decimal strings)
    """

    _writable_attrs = {"name"}

    name = SafeAttributeField("name")
    status = EnumAttributeField("status", SenderIdVerificationStatus)
    sender_type = EnumAttributeField("sender_type", SenderType)
    sender_ids = SafeAttributeField("sender_ids")
    reference = SafeAttributeField("reference")
    reject_reasons = SafeAttributeField("reject_reasons")
    reject_comment = SafeAttributeField("reject_comment")
    renew_date = SafeAttributeField("renew_date")
    created_at = DatetimeAttributeField("created_at")
    activated_at = DatetimeAttributeField("activated_at")
    closed_at = DatetimeAttributeField("closed_at")

    sms_trunk = RelationField("sms_trunk")
    countries = ReadOnlyRelationField("countries")
    dids = ReadOnlyRelationField("dids")
    order = ReadOnlyRelationField("order")
    identity = ReadOnlyRelationField("identity")
    address = ReadOnlyRelationField("address")

    class Meta:
        type = "sender_id_verifications"

    @property
    def is_active(self):
        return self.status == SenderIdVerificationStatus.ACTIVE

    @property
    def is_changes_required(self):
        return self.status == SenderIdVerificationStatus.CHANGES_REQUIRED

    @property
    def is_closed(self):
        return self.status == SenderIdVerificationStatus.CLOSED

    @property
    def is_closing_in_process(self):
        return self.status == SenderIdVerificationStatus.CLOSING_IN_PROCESS

    @property
    def is_in_process(self):
        return self.status == SenderIdVerificationStatus.IN_PROCESS

    @property
    def is_new(self):
        return self.status == SenderIdVerificationStatus.NEW


class SenderIdVerificationRepository(ReadOnlyRepository):
    _resource_class = SenderIdVerification
    _path = "sender_id_verifications"

    update = Repository.update
