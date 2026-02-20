from tests.conftest import my_vcr


class TestRequirement:
    @my_vcr.use_cassette("requirements/list.yaml")
    def test_list_requirements(self, client):
        response = client.requirements().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("requirements/show.yaml")
    def test_find_requirement(self, client):
        response = client.requirements().find("25d12afe-1ec6-4fe3-9621-b250dd1fb959")
        req = response.data
        assert req.id == "25d12afe-1ec6-4fe3-9621-b250dd1fb959"
        assert req.identity_type == "Any"
        assert req.service_description_required is True
