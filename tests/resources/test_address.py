from tests.conftest import my_vcr
from didww.enums import IdentityType
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
        first = response.data[0]
        assert first.country is not None
        assert first.country.name == "Ukraine"
        assert first.country.iso == "UA"
        assert first.identity is not None
        assert first.identity.first_name == "John"
        assert first.identity.last_name == "Doe"
        assert len(first.proofs) == 1
        assert first.proofs[0].id == "dd2f5f37-0d08-415d-9530-6488e6eb797b"
        assert first.area is None
        assert first.city is None

    @my_vcr.use_cassette("addresses/create.yaml")
    def test_create_address(self, client):
        addr = Address()
        addr.city_name = "New York"
        addr.postal_code = "123"
        addr.address = "some street"
        addr.description = "test address"
        addr.country = Country.build("1f6fc2bd-f081-4202-9b1a-d9cb88d942b9")
        addr.identity = Identity.build("5e9df058-50d2-4e34-b0d4-d1746b86f41a")
        create_params = QueryParams().include("country")
        response = client.addresses().create(addr, create_params)
        created = response.data
        assert created.id == "bf69bc70-e1c2-442c-9f30-335ee299b663"
        assert created.city_name == "New York"
        assert created.verified is False
        assert created.country is not None
        assert created.country.name == "United States"
        assert created.country.iso == "US"

    @my_vcr.use_cassette("addresses/show_with_includes.yaml")
    def test_find_address_with_includes(self, client):
        params = QueryParams().include(
            "identity.proofs",
            "identity.permanent_documents",
            "identity.addresses",
            "identity.country",
            "proofs",
            "country",
            "area",
            "city",
        )
        response = client.addresses().find("fafaca6b-40e5-4a9c-9a30-f2fac3ee8957", params)
        addr = response.data
        assert addr.id == "fafaca6b-40e5-4a9c-9a30-f2fac3ee8957"
        assert addr.city_name == "Algiers"
        assert addr.postal_code == "16000"
        assert addr.verified is True
        # proofs
        assert len(addr.proofs) == 1
        assert addr.proofs[0].id == "5cd00239-f9b5-4f08-9783-fb710eea9189"
        # country
        assert addr.country is not None
        assert addr.country.name == "Algeria"
        assert addr.country.iso == "DZ"
        # area and city
        assert addr.area is None
        assert addr.city is None
        # identity
        identity = addr.identity
        assert identity is not None
        assert identity.first_name == "John"
        assert identity.last_name == "Doe"
        assert identity.identity_type == IdentityType.BUSINESS
        assert len(identity.proofs) == 1
        assert identity.proofs[0].id == "9f8e2f56-bb2a-4c2e-9330-5dc4c204fc27"
        assert len(identity.addresses) == 1
        assert len(identity.permanent_documents) == 0
        assert identity.country is not None
        assert identity.country.name == "Algeria"

    @my_vcr.use_cassette("addresses/delete.yaml")
    def test_delete_address(self, client):
        result = client.addresses().delete("bf69bc70-e1c2-442c-9f30-335ee299b663")
        assert result is None
