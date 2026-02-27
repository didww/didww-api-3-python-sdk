from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class AvailableDid(DidwwApiModel):
    number = SafeAttributeField("number")

    did_group = RelationField("did_group")
    nanpa_prefix = RelationField("nanpa_prefix")

    class Meta:
        type = "available_dids"

    def nanpa_prefix_id(self):
        return self._relationship_id("nanpa_prefix")


class AvailableDidRepository(ReadOnlyRepository):
    _resource_class = AvailableDid
    _path = "available_dids"
