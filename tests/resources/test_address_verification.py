from tests.conftest import my_vcr
from didww.resources.address_verification import AddressVerification


class TestAddressVerification:
    @my_vcr.use_cassette("address_verifications/list.yaml")
    def test_list_address_verifications(self, client):
        response = client.address_verifications().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("address_verifications/create.yaml")
    def test_create_address_verification(self, client):
        av = AddressVerification()
        av.callback_url = "http://example.com"
        av.callback_method = "GET"
        av.set_address("d3414687-40f4-4346-a267-c2c65117d28c")
        av.set_dids(["a9d64c02-4486-4acb-a9a1-be4c81ff0659"])
        response = client.address_verifications().create(av)
        created = response.data
        assert created.id == "78182ef2-8377-41cd-89e1-26e8266c9c94"
        assert created.status == "Pending"
        assert created.callback_url == "http://example.com"
