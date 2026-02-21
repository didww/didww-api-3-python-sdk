from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class Pop(DidwwApiModel):
    name = SafeAttributeField("name")

    class Meta:
        type = "pops"


class PopRepository(ReadOnlyRepository):
    _resource_class = Pop
    _path = "pops"
