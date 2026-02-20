from tests.conftest import my_vcr


class TestDidGroupType:
    @my_vcr.use_cassette("did_group_types/list.yaml")
    def test_list_did_group_types(self, client):
        response = client.did_group_types().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("did_group_types/show.yaml")
    def test_find_did_group_type(self, client):
        response = client.did_group_types().find("d6530a8c-924c-469a-98c0-9525602e6192")
        dgt = response.data
        assert dgt.id == "d6530a8c-924c-469a-98c0-9525602e6192"
        assert dgt.name == "Global"
