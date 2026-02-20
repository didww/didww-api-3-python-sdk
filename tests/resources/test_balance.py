from tests.conftest import my_vcr


class TestBalance:
    @my_vcr.use_cassette("balance/list.yaml")
    def test_find_balance(self, client):
        response = client.balance().find()
        balance = response.data

        assert balance.id == "4c39e0bf-683b-4697-9322-5abaf4011883"
        assert balance.total_balance == "60.00"
        assert balance.credit == "10.00"
        assert balance.balance == "50.00"
