from jsonapi_requests.data import JsonApiResponse

from didww.resources.base import ApiResponse, DidwwApiModel, SafeAttributeField


class Balance(DidwwApiModel):
    total_balance = SafeAttributeField("total_balance")
    credit = SafeAttributeField("credit")
    balance = SafeAttributeField("balance")

    class Meta:
        type = "balances"


class BalanceRepository:
    _resource_class = Balance
    _path = "balance"

    def __init__(self, client):
        self.client = client

    def find(self, params=None):
        query = params.to_dict() if params else None
        body = self.client.get(self._path, params=query)
        response = JsonApiResponse.from_data(body)
        resource = self._resource_class.from_response_content(response)
        return ApiResponse(data=resource, meta=body.get("meta", {}))
