from tests.conftest import my_vcr


class TestCountry:
    @my_vcr.use_cassette("countries/list.yaml")
    def test_list_countries(self, client):
        response = client.countries().list()
        countries = response.data

        assert len(countries) > 0

        first = countries[0]
        assert first.id == "6c7727b3-6e17-4b8b-a4b3-4c5142e31a63"
        assert first.name == "Afghanistan"
        assert first.prefix == "93"
        assert first.iso == "AF"

    @my_vcr.use_cassette("countries/show.yaml")
    def test_find_country(self, client):
        response = client.countries().find("7eda11bb-0e66-4146-98e7-57a5281f56c8")
        country = response.data

        assert country.name == "United Kingdom"
        assert country.prefix == "44"
        assert country.iso == "GB"
