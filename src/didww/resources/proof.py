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

    def set_proof_type(self, proof_type):
        self._set_relationship("proof_type", proof_type)

    def set_entity(self, entity):
        self._set_relationship("entity", entity)

    def set_files(self, files):
        self._set_relationships("files", files)

    def proof_type(self):
        return self._get_relationship("proof_type")

    def entity(self):
        return self._get_relationship("entity")


class ProofRepository(CreateOnlyRepository):
    _resource_class = Proof
    _path = "proofs"
