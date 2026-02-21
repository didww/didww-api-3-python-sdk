from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.address import Address
from didww.resources.country import Country
from didww.resources.identity import Identity


class TestAddress:
    @my_vcr.use_cassette("addresses/list.yaml")
    def test_list_addresses(self, client):
        params = QueryParams().include("country", "identity", "proofs", "area", "city")
        response = client.addresses().list(params)
        assert len(response.data) > 0

    @my_vcr.use_cassette("addresses/create.yaml")
    def test_create_address(self, client):
        addr = Address()
        addr.city_name = "New York"
        addr.postal_code = "123"
        addr.address = "some street"
        addr.description = "test address"
        addr.set_country(Country.build("1f6fc2bd-f081-4202-9b1a-d9cb88d942b9"))
        addr.set_identity(Identity.build("5e9df058-50d2-4e34-b0d4-d1746b86f41a"))
        create_params = QueryParams().include("country")
        response = client.addresses().create(addr, create_params)
        created = response.data
        assert created.id == "bf69bc70-e1c2-442c-9f30-335ee299b663"
        assert created.city_name == "New York"
        assert created.verified is False
