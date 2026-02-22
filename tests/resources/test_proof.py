from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.proof import Proof
from didww.resources.proof_type import ProofType
from didww.resources.encrypted_file import EncryptedFile


class TestProof:
    @my_vcr.use_cassette("proofs/create.yaml")
    def test_create_proof(self, client):
        proof = Proof()
        proof.proof_type = ProofType.build("19cd7b22-559b-41d4-99c9-7ad7ad63d5d1")
        proof.files = [EncryptedFile.build("254b3c2d-c40c-4ff7-93b1-a677aee7fa10")]
        create_params = QueryParams().include("proof_type")
        response = client.proofs().create(proof, create_params)
        created = response.data
        assert created.id == "ed46925b-a830-482d-917d-015858cf7ab9"
        pt = created.proof_type
        assert pt is not None
        assert pt.name == "Drivers License"

    @my_vcr.use_cassette("proofs/delete.yaml")
    def test_delete_proof(self, client):
        result = client.proofs().delete("ed46925b-a830-482d-917d-015858cf7ab9")
        assert result is None
