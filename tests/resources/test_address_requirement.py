import pytest

from tests.conftest import my_vcr
from didww.enums import AreaLevel, IdentityType, NumberType
from didww.query_params import QueryParams
from didww.resources.address_requirement import AddressRequirement


class TestAddressRequirement:
    @my_vcr.use_cassette("address_requirements/list.yaml")
    def test_list_address_requirements(self, client):
        response = client.address_requirements().list()
        assert len(response.data) > 0
        assert response.data[0].business_mandatory_fields == []

    @pytest.mark.parametrize("attributes", [
        {},
        {"personal_mandatory_fields": None, "business_mandatory_fields": None},
    ], ids=["missing", "null"])
    def test_mandatory_fields_are_lists_when_missing_or_null(self, attributes):
        requirement = AddressRequirement.from_jsonapi(
            {"id": "1", "type": "address_requirements", "attributes": attributes})
        assert requirement.personal_mandatory_fields == []
        assert requirement.business_mandatory_fields == []

    @my_vcr.use_cassette("address_requirements/show.yaml")
    def test_find_address_requirement(self, client):
        params = QueryParams().include(
            "country",
            "personal_permanent_document", "business_permanent_document",
            "personal_onetime_document", "business_onetime_document",
            "personal_proof_types", "business_proof_types", "address_proof_types",
        )
        response = client.address_requirements().find("25d12afe-1ec6-4fe3-9621-b250dd1fb959", params)
        req = response.data
        assert req.id == "25d12afe-1ec6-4fe3-9621-b250dd1fb959"
        assert req.identity_type == IdentityType.ANY
        assert req.service_description_required is True
        assert req.personal_area_level == AreaLevel.WORLDWIDE
        assert req.business_area_level == AreaLevel.WORLDWIDE
        assert req.address_area_level == AreaLevel.WORLDWIDE
        assert req.personal_proof_qty == 1
        assert req.business_proof_qty == 1
        assert req.address_proof_qty == 1
        assert req.restriction_message == "End User Registration is Required"
        assert req.number_type == NumberType.LOCAL
        assert req.personal_mandatory_fields == ["birth_date", "country", "personal_tax_id"]
        assert req.business_mandatory_fields == ["id_number", "tax_id", "country", "company_reg_number",
                                                 "personal_tax_id"]
        # included relationships
        assert req.country.id == "5b156dc2-327e-4665-bdc5-35cd8729b885"
        assert req.personal_permanent_document.id == "fd38c86d-b69b-4ca8-b73c-286a3b93d107"
        assert req.business_permanent_document.id == "fd38c86d-b69b-4ca8-b73c-286a3b93d107"
        assert req.personal_onetime_document.id == "206ccec2-1166-461f-9f58-3a56823db548"
        assert req.business_onetime_document.id == "206ccec2-1166-461f-9f58-3a56823db548"
        assert len(req.personal_proof_types) == 1
        assert req.personal_proof_types[0].entity_type == "personal"
        assert req.address_proof_types[0].entity_type == "address"
        assert len(req.business_proof_types) == 7
        assert len(req.address_proof_types) == 1
