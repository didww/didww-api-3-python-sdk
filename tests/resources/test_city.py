from tests.conftest import my_vcr


class TestCity:
    @my_vcr.use_cassette("cities/list.yaml")
    def test_list_cities(self, client):
        response = client.cities().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("cities/show.yaml")
    def test_find_city(self, client):
        response = client.cities().find("368bf92f-c36e-473f-96fc-d53ed1b4028b")
        city = response.data
        assert city.id == "368bf92f-c36e-473f-96fc-d53ed1b4028b"
        assert city.name == "New York"
