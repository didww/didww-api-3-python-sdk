from tests.conftest import my_vcr


class TestPop:
    @my_vcr.use_cassette("pops/list.yaml")
    def test_list_pops(self, client):
        response = client.pops().list()
        pops = response.data

        assert len(pops) > 0
        first = pops[0]
        assert first.id is not None
        assert first.name is not None
