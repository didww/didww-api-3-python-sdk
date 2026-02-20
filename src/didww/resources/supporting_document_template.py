from didww.resources.base import BaseResource, ReadOnlyRepository


class SupportingDocumentTemplate(BaseResource):
    _type = "supporting_document_templates"

    @property
    def name(self):
        return self._attr("name")

    @property
    def permanent(self):
        return self._attr("permanent")

    @property
    def url(self):
        return self._attr("url")


class SupportingDocumentTemplateRepository(ReadOnlyRepository):
    _resource_class = SupportingDocumentTemplate
    _path = "supporting_document_templates"
