import pytest

from tests.conftest import my_vcr
from didww.enums import NumberType
from didww.resources.emergency_requirement import EmergencyRequirement


class TestEmergencyRequirement:
    @pytest.mark.parametrize("attributes", [
        {},
        {"address_mandatory_fields": None, "personal_mandatory_fields": None, "business_mandatory_fields": None},
    ], ids=["missing", "null"])
    def test_mandatory_fields_are_lists_when_missing_or_null(self, attributes):
        requirement = EmergencyRequirement.from_jsonapi(
            {"id": "1", "type": "emergency_requirements", "attributes": attributes})
        assert requirement.address_mandatory_fields == []
        assert requirement.personal_mandatory_fields == []
        assert requirement.business_mandatory_fields == []

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
        assert er.personal_area_level == "country"
        # A country that accepts personal identities only leaves the business level unset.
        assert er.business_area_level is None
        assert er.estimate_setup_time == "7-14 days"
        assert er.address_mandatory_fields == ["area"]
        assert er.personal_mandatory_fields == ["birth_date", "country", "id_number"]
        assert er.business_mandatory_fields == []
        assert er.requirement_restriction_message is None
        assert er.number_type == NumberType.LOCAL
        assert er.meta["setup_price"] == "0.0"
        assert er.meta["monthly_price"] == "1.5"
