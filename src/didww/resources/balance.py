from didww.resources.base import BaseResource, SingletonRepository


class Balance(BaseResource):
    _type = "balances"

    @property
    def total_balance(self):
        return self._attr("total_balance")

    @property
    def credit(self):
        return self._attr("credit")

    @property
    def balance(self):
        return self._attr("balance")


class BalanceRepository(SingletonRepository):
    _resource_class = Balance
    _path = "balance"
