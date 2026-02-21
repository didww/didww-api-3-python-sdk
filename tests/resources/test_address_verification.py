from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.address_verification import AddressVerification
from didww.resources.address import Address
from didww.resources.did import Did


class TestAddressVerification:
    @my_vcr.use_cassette("address_verifications/list.yaml")
    def test_list_address_verifications(self, client):
        params = QueryParams().include("address", "dids")
        response = client.address_verifications().list(params)
        assert len(response.data) > 0
        first = response.data[0]
        assert first.address() is not None
        assert first.address().city_name == "Chicago"

    @my_vcr.use_cassette("address_verifications/show.yaml")
    def test_find_address_verification(self, client):
        response = client.address_verifications().find("c8e004b0-87ec-4987-b4fb-ee89db099f0e")
        av = response.data
        assert av.id == "c8e004b0-87ec-4987-b4fb-ee89db099f0e"
        assert av.status == "Approved"
        assert av.reference == "SHB-485120"
        assert av.created_at == "2020-09-15T06:38:12.650Z"

    @my_vcr.use_cassette("address_verifications/create.yaml")
    def test_create_address_verification(self, client):
        av = AddressVerification()
        av.callback_url = "http://example.com"
        av.callback_method = "GET"
        av.set_address(Address.build("d3414687-40f4-4346-a267-c2c65117d28c"))
        av.set_dids([Did.build("a9d64c02-4486-4acb-a9a1-be4c81ff0659")])
        create_params = QueryParams().include("address")
        response = client.address_verifications().create(av, create_params)
        created = response.data
        assert created.id == "78182ef2-8377-41cd-89e1-26e8266c9c94"
        assert created.status == "Pending"
        assert created.callback_url == "http://example.com"
        assert created.address() is not None
        assert created.address().city_name == "Chicago"
