from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, CreateOnlyRepository


class Proof(DidwwApiModel):
    _writable_attrs = {"external_reference_id"}

    created_at = DatetimeAttributeField("created_at")
    expires_at = DatetimeAttributeField("expires_at")
    external_reference_id = SafeAttributeField("external_reference_id")

    proof_type = RelationField("proof_type")
    entity = RelationField("entity")
    files = RelationField("files")

    class Meta:
        type = "proofs"


class ProofRepository(CreateOnlyRepository):
    _resource_class = Proof
    _path = "proofs"
