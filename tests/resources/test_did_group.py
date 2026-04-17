from didww.enums import Feature, IdentityType, AreaLevel
from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestDidGroupFeatures:
    def test_new_features_enum_values(self):
        assert Feature.P2P.value == "p2p"
        assert Feature.A2P.value == "a2p"
        assert Feature.EMERGENCY.value == "emergency"
        assert Feature.CNAM_OUT.value == "cnam_out"


class TestDidGroup:
    @my_vcr.use_cassette("did_groups/list.yaml")
    def test_list_did_groups(self, client):
        response = client.did_groups().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("did_groups/show.yaml")
    def test_find_did_group(self, client):
        params = QueryParams().include("country", "region", "city", "did_group_type", "stock_keeping_units")
        response = client.did_groups().find("2187c36d-28fb-436f-8861-5a0f5b5a3ee1", params)
        dg = response.data
        assert dg.id == "2187c36d-28fb-436f-8861-5a0f5b5a3ee1"
        assert dg.prefix == "241"
        assert dg.features == [Feature.VOICE_IN]
        assert dg.is_metered is False
        assert dg.area_name == "Aachen"
        assert dg.allow_additional_channels is True
        assert dg.service_restrictions is None
        country = dg.country
        assert country is not None
        assert country.name == "Germany"
        city = dg.city
        assert city is not None
        assert city.name == "Aachen"
        dgt = dg.did_group_type
        assert dgt is not None
        assert dgt.name == "Local"
        assert dg.region is None
        assert len(dg.stock_keeping_units) == 2

    @my_vcr.use_cassette("did_groups/show_with_address_requirement.yaml")
    def test_find_did_group_with_address_requirement(self, client):
        params = QueryParams().include("address_requirement")
        response = client.did_groups().find("2187c36d-28fb-436f-8861-5a0f5b5a3ee1", params)
        dg = response.data
        assert dg.id == "2187c36d-28fb-436f-8861-5a0f5b5a3ee1"
        assert dg.prefix == "241"
        assert dg.area_name == "Aachen"
        address_requirement = dg.address_requirement
        assert address_requirement is not None
        assert address_requirement.id == "8da1e0b2-047c-4baf-9c57-57143f09b9ce"
        assert address_requirement.identity_type == IdentityType.ANY
        assert address_requirement.personal_area_level == AreaLevel.WORLDWIDE
        assert address_requirement.service_description_required is False
