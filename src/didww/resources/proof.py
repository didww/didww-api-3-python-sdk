from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, CreateOnlyRepository


class Proof(DidwwApiModel):
    _writable_attrs = set()

    created_at = SafeAttributeField("created_at")
    expires_at = SafeAttributeField("expires_at")

    proof_type = RelationField("proof_type")
    entity = RelationField("entity")
    files = RelationField("files")

    class Meta:
        type = "proofs"


class ProofRepository(CreateOnlyRepository):
    _resource_class = Proof
    _path = "proofs"
