from tests.conftest import my_vcr
from didww.query_params import QueryParams
from didww.resources.permanent_supporting_document import PermanentSupportingDocument
from didww.resources.identity import Identity
from didww.resources.supporting_document_template import SupportingDocumentTemplate
from didww.resources.encrypted_file import EncryptedFile


class TestPermanentSupportingDocument:
    @my_vcr.use_cassette("permanent_supporting_documents/create.yaml")
    def test_create_permanent_supporting_document(self, client):
        doc = PermanentSupportingDocument()
        doc.identity = Identity.build("5e9df058-50d2-4e34-b0d4-d1746b86f41a")
        doc.template = SupportingDocumentTemplate.build("4199435f-646e-4e9d-a143-8f3b972b10c5")
        doc.files = [EncryptedFile.build("254b3c2d-c40c-4ff7-93b1-a677aee7fa10")]
        create_params = QueryParams().include("template")
        response = client.permanent_supporting_documents().create(doc, create_params)
        created = response.data
        assert created.id == "19510da3-c07e-4fa9-a696-6b9ab89cc172"
        tmpl = created.template
        assert tmpl is not None
        assert tmpl.name == "Germany Special Registration Form"

    @my_vcr.use_cassette("permanent_supporting_documents/delete.yaml")
    def test_delete_permanent_supporting_document(self, client):
        result = client.permanent_supporting_documents().delete("19510da3-c07e-4fa9-a696-6b9ab89cc172")
        assert result is None
