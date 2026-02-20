from tests.conftest import my_vcr
from didww.resources.address import Address


class TestAddress:
    @my_vcr.use_cassette("addresses/list.yaml")
    def test_list_addresses(self, client):
        response = client.addresses().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("addresses/create.yaml")
    def test_create_address(self, client):
        addr = Address()
        addr.city_name = "New York"
        addr.postal_code = "123"
        addr.address = "some street"
        addr.description = "test address"
        addr.set_country("1f6fc2bd-f081-4202-9b1a-d9cb88d942b9")
        addr.set_identity("5e9df058-50d2-4e34-b0d4-d1746b86f41a")
        response = client.addresses().create(addr)
        created = response.data
        assert created.id == "bf69bc70-e1c2-442c-9f30-335ee299b663"
        assert created.city_name == "New York"
        assert created.verified is False
