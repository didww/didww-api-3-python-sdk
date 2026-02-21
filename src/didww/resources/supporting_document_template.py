from didww.resources.base import DidwwApiModel, SafeAttributeField, ReadOnlyRepository


class SupportingDocumentTemplate(DidwwApiModel):
    name = SafeAttributeField("name")
    permanent = SafeAttributeField("permanent")
    url = SafeAttributeField("url")

    class Meta:
        type = "supporting_document_templates"


class SupportingDocumentTemplateRepository(ReadOnlyRepository):
    _resource_class = SupportingDocumentTemplate
    _path = "supporting_document_templates"
