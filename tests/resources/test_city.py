from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestCity:
    @my_vcr.use_cassette("cities/list.yaml")
    def test_list_cities(self, client):
        response = client.cities().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("cities/show.yaml")
    def test_find_city(self, client):
        params = QueryParams().include("country", "region", "area")
        response = client.cities().find("368bf92f-c36e-473f-96fc-d53ed1b4028b", params)
        city = response.data
        assert city.id == "368bf92f-c36e-473f-96fc-d53ed1b4028b"
        assert city.name == "New York"
        country = city.country
        assert country is not None
        assert country.name == "United States"
        region = city.region
        assert region is not None
        assert region.name == "New York"
