from didww.resources.base import DidwwApiModel, SafeAttributeField, SingletonRepository


class Balance(DidwwApiModel):
    total_balance = SafeAttributeField("total_balance")
    credit = SafeAttributeField("credit")
    balance = SafeAttributeField("balance")

    class Meta:
        type = "balances"


class BalanceRepository(SingletonRepository):
    _resource_class = Balance
    _path = "balance"
