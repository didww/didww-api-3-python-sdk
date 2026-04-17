from didww.resources.base import DidwwApiModel, DatetimeAttributeField, SafeAttributeField, RelationField, CreateOnlyRepository


class PermanentSupportingDocument(DidwwApiModel):
    _writable_attrs = {"external_reference_id"}

    created_at = DatetimeAttributeField("created_at")
    external_reference_id = SafeAttributeField("external_reference_id")

    identity = RelationField("identity")
    template = RelationField("template")
    files = RelationField("files")

    class Meta:
        type = "permanent_supporting_documents"


class PermanentSupportingDocumentRepository(CreateOnlyRepository):
    _resource_class = PermanentSupportingDocument
    _path = "permanent_supporting_documents"
