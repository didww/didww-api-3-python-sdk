from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.shared_capacity_group import SharedCapacityGroup


class TestSharedCapacityGroup:
    @my_vcr.use_cassette("shared_capacity_groups/list.yaml")
    def test_list_shared_capacity_groups(self, client):
        response = client.shared_capacity_groups().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("shared_capacity_groups/show.yaml")
    def test_find_shared_capacity_group(self, client):
        params = QueryParams().include("dids", "capacity_pool")
        response = client.shared_capacity_groups().find("89f987e2-0862-4bf4-a3f4-cdc89af0d875", params)
        scg = response.data
        assert scg.id is not None
        assert scg.name is not None
        cp = scg.capacity_pool()
        assert cp is not None
        assert cp.name == "Standard"
        assert len(scg.dids()) >= 16
