from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestRegion:
    @my_vcr.use_cassette("regions/list.yaml")
    def test_list_regions(self, client):
        response = client.regions().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("regions/show.yaml")
    def test_find_region(self, client):
        params = QueryParams().include("country")
        response = client.regions().find("c11b1f34-16cf-4ba6-8497-f305b53d5b01", params)
        region = response.data
        assert region.id == "c11b1f34-16cf-4ba6-8497-f305b53d5b01"
        assert region.name == "California"
