from tests.conftest import my_vcr


class TestCapacityPool:
    @my_vcr.use_cassette("capacity_pools/list.yaml")
    def test_list_capacity_pools(self, client):
        response = client.capacity_pools().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("capacity_pools/show.yaml")
    def test_find_capacity_pool(self, client):
        response = client.capacity_pools().find("f288d07c-e2fc-4ae6-9837-b18fb469c324")
        cp = response.data
        assert cp.id == "f288d07c-e2fc-4ae6-9837-b18fb469c324"
