from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class ProofType(DidwwApiModel):
    """Proof type resource; ``entity_type`` is ``address``, ``business`` or ``personal``."""

    name = SafeAttributeField("name")
    entity_type = SafeAttributeField("entity_type")

    class Meta:
        type = "proof_types"


class ProofTypeRepository(ReadOnlyRepository):
    _resource_class = ProofType
    _path = "proof_types"
