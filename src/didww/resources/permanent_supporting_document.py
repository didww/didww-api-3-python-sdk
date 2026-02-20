from didww.resources.base import BaseResource, CreateOnlyRepository


class PermanentSupportingDocument(BaseResource):
    _type = "permanent_supporting_documents"
    _writable_attrs = set()

    @property
    def created_at(self):
        return self._attr("created_at")

    def set_identity(self, identity_id):
        self._set_relationship("identity", "identities", identity_id)

    def set_template(self, template_id):
        self._set_relationship("template", "supporting_document_templates", template_id)

    def set_files(self, file_ids):
        self._relationships["files"] = {
            "data": [{"type": "encrypted_files", "id": fid} for fid in file_ids]
        }


class PermanentSupportingDocumentRepository(CreateOnlyRepository):
    _resource_class = PermanentSupportingDocument
    _path = "permanent_supporting_documents"
