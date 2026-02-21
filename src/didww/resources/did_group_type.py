from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class DidGroupType(DidwwApiModel):
    name = SafeAttributeField("name")

    class Meta:
        type = "did_group_types"


class DidGroupTypeRepository(ReadOnlyRepository):
    _resource_class = DidGroupType
    _path = "did_group_types"
