from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestDidGroup:
    @my_vcr.use_cassette("did_groups/list.yaml")
    def test_list_did_groups(self, client):
        response = client.did_groups().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("did_groups/show.yaml")
    def test_find_did_group(self, client):
        params = QueryParams().include("country", "region", "city", "did_group_type", "stock_keeping_units")
        response = client.did_groups().find("2187c36d-28fb-436f-8861-5a0f5b5a3ee1", params)
        dg = response.data
        assert dg.id == "2187c36d-28fb-436f-8861-5a0f5b5a3ee1"
        assert dg.prefix == "241"
        assert dg.features == ["voice"]
        assert dg.is_metered is False
        assert dg.area_name == "Aachen"
        assert dg.allow_additional_channels is True
