from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.did_reservation import DidReservation
from didww.resources.available_did import AvailableDid


class TestDidReservation:
    @my_vcr.use_cassette("did_reservations/list.yaml")
    def test_list_did_reservations(self, client):
        response = client.did_reservations().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("did_reservations/show.yaml")
    def test_find_did_reservation(self, client):
        params = QueryParams().include("available_did.did_group.stock_keeping_units")
        response = client.did_reservations().find("fd38d3ff-80cf-4e67-a605-609a2884a5c4", params)
        dr = response.data
        assert dr.id == "fd38d3ff-80cf-4e67-a605-609a2884a5c4"
        assert dr.description == "DIDWW"
        ad = dr.available_did
        assert ad is not None
        assert ad.number == "19492033398"

    @my_vcr.use_cassette("did_reservations/create.yaml")
    def test_create_did_reservation(self, client):
        dr = DidReservation()
        dr.description = "DIDWW"
        dr.available_did = AvailableDid.build("857d1462-5f43-4238-b007-ff05f282e41b")
        response = client.did_reservations().create(dr)
        created = response.data
        assert created.id == "fd38d3ff-80cf-4e67-a605-609a2884a5c4"
        assert created.description == "DIDWW"
