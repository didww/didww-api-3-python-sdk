from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, ReadOnlyRepository


class DidHistory(DidwwApiModel):
    """DID History event resource.

    Attributes:
        did_number (str): The DID number this history event relates to.
        action (str): The action that occurred (e.g. "billing_cycles_count_changed").
        method (str): The method used for the action.
        created_at (datetime): When the event occurred.

    Meta fields (present in the JSON:API ``meta`` hash on the response,
    not as resource attributes):

        meta["from"] / meta["to"] (str):
            Only present when action is "billing_cycles_count_changed".
            The previous (from) and new (to) billing_cycles_count values.
            Absent for every other action.
    """

    did_number = SafeAttributeField("did_number")
    action = SafeAttributeField("action")
    method = SafeAttributeField("method")
    created_at = DatetimeAttributeField("created_at")

    class Meta:
        type = "did_history"


class DidHistoryRepository(ReadOnlyRepository):
    _resource_class = DidHistory
    _path = "did_history"
