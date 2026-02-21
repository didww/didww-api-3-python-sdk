from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.identity import Identity
from didww.resources.country import Country


class TestIdentity:
    @my_vcr.use_cassette("identities/list.yaml")
    def test_list_identities(self, client):
        params = QueryParams().include("country", "addresses", "proofs", "permanent_documents")
        response = client.identities().list(params)
        assert len(response.data) > 0
        first = response.data[0]
        assert first.country() is not None

    @my_vcr.use_cassette("identities/create.yaml")
    def test_create_identity(self, client):
        identity = Identity()
        identity.first_name = "John"
        identity.last_name = "Doe"
        identity.phone_number = "123456789"
        identity.id_number = "ABC1234"
        identity.birth_date = "1970-01-01"
        identity.company_name = "Test Company Limited"
        identity.company_reg_number = "543221"
        identity.vat_id = "GB1234"
        identity.description = "test identity"
        identity.personal_tax_id = "987654321"
        identity.identity_type = "Business"
        identity.external_reference_id = "111"
        identity.set_country(Country.build("1f6fc2bd-f081-4202-9b1a-d9cb88d942b9"))
        create_params = QueryParams().include("country")
        response = client.identities().create(identity, create_params)
        created = response.data
        assert created.id == "e96ae7d1-11d5-42bc-a5c5-211f3c3788ae"
        assert created.first_name == "John"
        assert created.identity_type == "Business"
        assert created.country() is not None
