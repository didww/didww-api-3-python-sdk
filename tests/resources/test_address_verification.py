from tests.conftest import my_vcr
from didww.enums import AddressVerificationStatus, CallbackMethod, IdentityType
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
        assert first.address is not None
        assert first.address.city_name == "Chicago"
        assert len(first.dids) == 1
        assert first.dids[0].number == "13472013835"

    @my_vcr.use_cassette("address_verifications/show.yaml")
    def test_find_address_verification(self, client):
        response = client.address_verifications().find("c8e004b0-87ec-4987-b4fb-ee89db099f0e")
        av = response.data
        assert av.id == "c8e004b0-87ec-4987-b4fb-ee89db099f0e"
        assert av.status == AddressVerificationStatus.APPROVED
        assert av.reference == "SHB-485120"
        assert av.created_at == "2020-09-15T06:38:12.650Z"

    @my_vcr.use_cassette("address_verifications/show_with_includes.yaml")
    def test_find_address_verification_with_includes(self, client):
        params = QueryParams().include(
            "address.identity.proofs",
            "address.identity.permanent_documents",
            "address.identity.addresses",
            "address.identity.country",
            "address.proofs",
            "address.country",
            "dids",
        )
        response = client.address_verifications().find("75dc8d39-5e17-4470-a6f3-df42642c975f", params)
        av = response.data
        assert av.id == "75dc8d39-5e17-4470-a6f3-df42642c975f"
        assert av.status == AddressVerificationStatus.APPROVED
        assert av.reference == "AHB-291174"
        assert av.callback_method == CallbackMethod.POST
        # dids
        assert len(av.dids) == 1
        assert av.dids[0].number == "61488943592"
        # address
        addr = av.address
        assert addr is not None
        assert addr.city_name == "Algiers"
        assert addr.postal_code == "16000"
        assert addr.verified is True
        assert len(addr.proofs) == 1
        assert addr.proofs[0].id == "5cd00239-f9b5-4f08-9783-fb710eea9189"
        assert addr.country is not None
        assert addr.country.name == "Algeria"
        assert addr.country.iso == "DZ"
        # address.identity
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

    @my_vcr.use_cassette("address_verifications/create.yaml")
    def test_create_address_verification(self, client):
        av = AddressVerification()
        av.callback_url = "http://example.com"
        av.callback_method = CallbackMethod.GET
        av.address = Address.build("d3414687-40f4-4346-a267-c2c65117d28c")
        av.dids = [Did.build("a9d64c02-4486-4acb-a9a1-be4c81ff0659")]
        create_params = QueryParams().include("address")
        response = client.address_verifications().create(av, create_params)
        created = response.data
        assert created.id == "78182ef2-8377-41cd-89e1-26e8266c9c94"
        assert created.status == AddressVerificationStatus.PENDING
        assert created.callback_url == "http://example.com"
        assert created.address is not None
        assert created.address.city_name == "Chicago"
