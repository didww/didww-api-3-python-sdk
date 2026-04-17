from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, ReadOnlyRepository


class DidHistory(DidwwApiModel):
    did_number = SafeAttributeField("did_number")
    action = SafeAttributeField("action")
    method = SafeAttributeField("method")
    created_at = DatetimeAttributeField("created_at")

    class Meta:
        type = "did_history"


class DidHistoryRepository(ReadOnlyRepository):
    _resource_class = DidHistory
    _path = "did_history"
