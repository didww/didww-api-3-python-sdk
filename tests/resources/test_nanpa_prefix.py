from tests.conftest import my_vcr


class TestNanpaPrefix:
    @my_vcr.use_cassette("nanpa_prefixes/list.yaml")
    def test_list_nanpa_prefixes(self, client):
        response = client.nanpa_prefixes().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("nanpa_prefixes/show.yaml")
    def test_find_nanpa_prefix(self, client):
        response = client.nanpa_prefixes().find("6c16d51d-d376-4395-91c4-012321317e48")
        np = response.data
        assert np.id == "6c16d51d-d376-4395-91c4-012321317e48"
        assert np.npa == "864"
        assert np.nxx == "920"
