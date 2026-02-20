from tests.conftest import my_vcr


class TestProofType:
    @my_vcr.use_cassette("proof_types/list.yaml")
    def test_list_proof_types(self, client):
        response = client.proof_types().list()
        assert len(response.data) > 0
        first = response.data[0]
        assert first.id == "ab1fb565-ac55-4c73-bc55-64dc61e70169"
        assert first.name == "Utility Bill"
        assert first.entity_type == "Address"
