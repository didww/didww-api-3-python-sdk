from didww.resources.base import BaseResource, CreateOnlyRepository


class Proof(BaseResource):
    _type = "proofs"
    _writable_attrs = set()

    @property
    def created_at(self):
        return self._attr("created_at")

    @property
    def expires_at(self):
        return self._attr("expires_at")

    def set_proof_type(self, proof_type_id):
        self._set_relationship("proof_type", "proof_types", proof_type_id)

    def set_entity(self, entity_type, entity_id):
        self._set_relationship("entity", entity_type, entity_id)

    def set_files(self, file_ids):
        self._relationships["files"] = {
            "data": [{"type": "encrypted_files", "id": fid} for fid in file_ids]
        }


class ProofRepository(CreateOnlyRepository):
    _resource_class = Proof
    _path = "proofs"
