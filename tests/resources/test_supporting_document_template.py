from tests.conftest import my_vcr


class TestSupportingDocumentTemplate:
    @my_vcr.use_cassette("supporting_document_templates/list.yaml")
    def test_list_supporting_document_templates(self, client):
        response = client.supporting_document_templates().list()
        assert len(response.data) > 0
        first = response.data[0]
        assert first.id == "206ccec2-1166-461f-9f58-3a56823db548"
        assert first.name == "Generic LOI"
        assert first.permanent is False
