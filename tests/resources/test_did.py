from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestDid:
    @my_vcr.use_cassette("dids/list.yaml")
    def test_list_dids(self, client):
        params = QueryParams().include("order")
        response = client.dids().list(params)
        assert len(response.data) > 0
        first = response.data[0]
        assert first.order() is not None
        assert first.order().reference == "TZO-560180"

    @my_vcr.use_cassette("dids/show.yaml")
    def test_find_did(self, client):
        response = client.dids().find("9df99644-f1a5-4a3c-99a4-559d758eb96b")
        did = response.data
        assert did.number == "16091609123456797"
        assert did.blocked is False
        assert did.capacity_limit == 2
        assert did.description == "something"
        assert did.terminated is False
        assert did.awaiting_registration is False
        assert did.pending_removal is False
        assert did.channels_included_count == 0
        assert did.dedicated_channels_count == 0
