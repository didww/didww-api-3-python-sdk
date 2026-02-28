import pytest
from tests.conftest import my_vcr
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.capacity_pool import CapacityPool
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
        cp = scg.capacity_pool
        assert cp is not None
        assert cp.name == "Standard"
        assert len(scg.dids) >= 16

    @my_vcr.use_cassette("shared_capacity_groups/update.yaml")
    def test_update_shared_capacity_group(self, client):
        scg = SharedCapacityGroup()
        scg.id = "89f987e2-0862-4bf4-a3f4-cdc89af0d875"
        scg.name = "didww1"
        scg.shared_channels_count = 10
        scg.metered_channels_count = 2
        response = client.shared_capacity_groups().update(scg)
        updated = response.data
        assert updated.id == "89f987e2-0862-4bf4-a3f4-cdc89af0d875"
        assert updated.name == "didww1"
        assert updated.shared_channels_count == 10
        assert updated.metered_channels_count == 2

    @my_vcr.use_cassette("shared_capacity_groups/create.yaml")
    def test_create_shared_capacity_group(self, client):
        scg = SharedCapacityGroup()
        scg.name = "python-sdk"
        scg.shared_channels_count = 5
        scg.metered_channels_count = 0
        scg.capacity_pool = CapacityPool.build("f288d07c-e2fc-4ae6-9837-b18fb469c324")
        response = client.shared_capacity_groups().create(scg)
        created = response.data
        assert created.id == "3688a9c3-354f-4e16-b458-1d2df9f02547"
        assert created.name == "python-sdk"
        assert created.shared_channels_count == 5
        assert created.metered_channels_count == 0

    @my_vcr.use_cassette("shared_capacity_groups/create_error.yaml")
    def test_create_shared_capacity_group_error(self, client):
        scg = SharedCapacityGroup()
        scg.name = "python-sdk"
        scg.shared_channels_count = 5
        scg.metered_channels_count = 0
        scg.capacity_pool = CapacityPool.build("f288d07c-e2fc-4ae6-9837-b18fb469c324")
        with pytest.raises(DidwwApiError) as exc_info:
            client.shared_capacity_groups().create(scg)
        assert exc_info.value.status_code == 422
        assert len(exc_info.value.errors) == 1
        assert "capacity_pool" in exc_info.value.errors[0]["detail"]

    @my_vcr.use_cassette("shared_capacity_groups/delete.yaml")
    def test_delete_shared_capacity_group(self, client):
        result = client.shared_capacity_groups().delete("3688a9c3-354f-4e16-b458-1d2df9f02547")
        assert result is None
