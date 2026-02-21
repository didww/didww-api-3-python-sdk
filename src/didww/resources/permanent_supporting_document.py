from didww.resources.base import BaseResource, CreateOnlyRepository


class PermanentSupportingDocument(BaseResource):
    _type = "permanent_supporting_documents"
    _writable_attrs = set()

    @property
    def created_at(self):
        return self._attr("created_at")

    def set_identity(self, identity):
        self._set_relationship("identity", identity)

    def set_template(self, template):
        self._set_relationship("template", template)

    def set_files(self, files):
        self._set_relationships("files", files)


class PermanentSupportingDocumentRepository(CreateOnlyRepository):
    _resource_class = PermanentSupportingDocument
    _path = "permanent_supporting_documents"
