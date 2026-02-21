from tests.conftest import my_vcr
from didww.query_params import QueryParams


class TestRequirement:
    @my_vcr.use_cassette("requirements/list.yaml")
    def test_list_requirements(self, client):
        response = client.requirements().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("requirements/show.yaml")
    def test_find_requirement(self, client):
        params = QueryParams().include(
            "country", "did_group_type",
            "personal_permanent_document", "business_permanent_document",
            "personal_onetime_document", "business_onetime_document",
            "personal_proof_types", "business_proof_types", "address_proof_types",
        )
        response = client.requirements().find("25d12afe-1ec6-4fe3-9621-b250dd1fb959", params)
        req = response.data
        assert req.id == "25d12afe-1ec6-4fe3-9621-b250dd1fb959"
        assert req.identity_type == "Any"
        assert req.service_description_required is True
        assert req.personal_area_level == "WorldWide"
        assert req.business_area_level == "WorldWide"
        assert req.address_area_level == "WorldWide"
        assert req.personal_proof_qty == 1
        assert req.business_proof_qty == 1
        assert req.address_proof_qty == 1
        assert req.restriction_message == "End User Registration is Required"
        assert isinstance(req.personal_mandatory_fields, list)
        assert "Birth Date" in req.personal_mandatory_fields
        assert isinstance(req.business_mandatory_fields, list)
        assert "Company ID" in req.business_mandatory_fields
        # relationship ID accessors
        assert req.country_id() == "5b156dc2-327e-4665-bdc5-35cd8729b885"
        assert req.did_group_type_id() == "994ea201-4a4d-4b27-ac4b-b5916ac969a3"
        assert req.personal_permanent_document_id() == "fd38c86d-b69b-4ca8-b73c-286a3b93d107"
        assert req.business_permanent_document_id() == "fd38c86d-b69b-4ca8-b73c-286a3b93d107"
        assert req.personal_onetime_document_id() == "206ccec2-1166-461f-9f58-3a56823db548"
        assert req.business_onetime_document_id() == "206ccec2-1166-461f-9f58-3a56823db548"
        assert len(req.personal_proof_type_ids()) == 1
        assert len(req.business_proof_type_ids()) == 7
        assert len(req.address_proof_type_ids()) == 1
