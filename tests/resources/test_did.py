from tests.conftest import my_vcr
from didww.enums import AddressVerificationStatus
from didww.query_params import QueryParams


class TestDid:
    @my_vcr.use_cassette("dids/list.yaml")
    def test_list_dids(self, client):
        params = QueryParams().include("order")
        response = client.dids().list(params)
        assert len(response.data) > 0
        first = response.data[0]
        assert first.order is not None
        assert first.order.reference == "TZO-560180"

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
        assert did.billing_cycles_count is None
        assert did.channels_included_count == 0
        assert did.dedicated_channels_count == 0

    @my_vcr.use_cassette("dids/show_with_address_verification_and_did_group.yaml")
    def test_find_did_with_address_verification_and_did_group(self, client):
        params = QueryParams().include("address_verification", "did_group")
        response = client.dids().find("21d0b02c-b556-4d3e-acbf-504b78295dbe", params)
        did = response.data
        assert did.number == "61488943592"
        assert did.blocked is False
        av = did.address_verification
        assert av is not None
        assert av.status == AddressVerificationStatus.APPROVED
        assert av.reference == "AHB-291174"
        dg = did.did_group
        assert dg is not None
        assert dg.prefix == "4"
        assert dg.area_name == "Mobile"
