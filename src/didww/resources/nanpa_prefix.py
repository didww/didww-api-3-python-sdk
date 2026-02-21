from didww.resources.base import DidwwApiModel, SafeAttributeField, RelationField, ReadOnlyRepository


class NanpaPrefix(DidwwApiModel):
    npa = SafeAttributeField("npa")
    nxx = SafeAttributeField("nxx")

    country = RelationField("country")

    class Meta:
        type = "nanpa_prefixes"


class NanpaPrefixRepository(ReadOnlyRepository):
    _resource_class = NanpaPrefix
    _path = "nanpa_prefixes"
