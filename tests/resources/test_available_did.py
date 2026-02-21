from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestAvailableDid:
    @my_vcr.use_cassette("available_dids/list.yaml")
    def test_list_available_dids(self, client):
        response = client.available_dids().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("available_dids/show.yaml")
    def test_find_available_did(self, client):
        params = QueryParams().include("did_group.stock_keeping_units")
        response = client.available_dids().find("0b76223b-9625-412f-b0f3-330551473e7e", params)
        ad = response.data
        assert ad.id == "0b76223b-9625-412f-b0f3-330551473e7e"
        assert ad.number == "16169886810"
        dg = ad.did_group()
        assert dg is not None
        assert dg.prefix == "616"
        assert len(dg.stock_keeping_units()) == 2
