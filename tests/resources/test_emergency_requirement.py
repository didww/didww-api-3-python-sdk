from tests.conftest import my_vcr


class TestEmergencyRequirement:
    @my_vcr.use_cassette("emergency_requirements/list.yaml")
    def test_list_emergency_requirements(self, client):
        response = client.emergency_requirements().list()
        assert len(response.data) == 1

    @my_vcr.use_cassette("emergency_requirements/show.yaml")
    def test_find_emergency_requirement(self, client):
        response = client.emergency_requirements().find("er-001")
        er = response.data
        assert er.id == "er-001"
        assert er.identity_type == "personal"
        assert er.address_area_level == "city"
        assert er.estimate_setup_time == 5
        assert er.address_mandatory_fields == ["city_name", "address"]
        assert er.personal_mandatory_fields == ["first_name", "last_name"]
        assert er.requirement_restriction_message is None
