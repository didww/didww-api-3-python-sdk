from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestArea:
    @my_vcr.use_cassette("areas/list.yaml")
    def test_list_areas(self, client):
        response = client.areas().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("areas/show.yaml")
    def test_find_area(self, client):
        params = QueryParams().include("country")
        response = client.areas().find("ab2adc18-7c94-42d9-bdde-b28dfc373a22", params)
        area = response.data
        assert area.id == "ab2adc18-7c94-42d9-bdde-b28dfc373a22"
        assert area.name == "Tuscany"
        country = area.country()
        assert country is not None
        assert country.name == "Italy"
        assert country.iso == "IT"
