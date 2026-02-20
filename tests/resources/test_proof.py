from tests.conftest import my_vcr
from didww.resources.proof import Proof


class TestProof:
    @my_vcr.use_cassette("proofs/create.yaml")
    def test_create_proof(self, client):
        proof = Proof()
        proof.set_proof_type("19cd7b22-559b-41d4-99c9-7ad7ad63d5d1")
        proof.set_files(["254b3c2d-c40c-4ff7-93b1-a677aee7fa10"])
        response = client.proofs().create(proof)
        created = response.data
        assert created.id == "ed46925b-a830-482d-917d-015858cf7ab9"
