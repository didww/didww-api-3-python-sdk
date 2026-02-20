from didww.resources.base import BaseResource, ReadOnlyRepository


class ProofType(BaseResource):
    _type = "proof_types"

    @property
    def name(self):
        return self._attr("name")

    @property
    def entity_type(self):
        return self._attr("entity_type")


class ProofTypeRepository(ReadOnlyRepository):
    _resource_class = ProofType
    _path = "proof_types"
