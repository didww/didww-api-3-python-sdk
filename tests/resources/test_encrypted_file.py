import pytest
from tests.conftest import my_vcr, my_vcr_no_body
from didww.exceptions import DidwwClientError


class TestEncryptedFile:
    @my_vcr.use_cassette("encrypted_files/list.yaml")
    def test_list_encrypted_files(self, client):
        response = client.encrypted_files().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("encrypted_files/show.yaml")
    def test_find_encrypted_file(self, client):
        response = client.encrypted_files().find("6eed102c-66a9-4a9b-a95f-4312d70ec12a")
        ef = response.data
        assert ef.id == "6eed102c-66a9-4a9b-a95f-4312d70ec12a"
        assert ef.description == "some description"

    @my_vcr_no_body.use_cassette("encrypted_files/upload.yaml")
    def test_upload_encrypted_file(self, client):
        file_id = client.upload_encrypted_file(
            fingerprint="c74684d7863639169c21c4d04747f8d6fa05cfe3:::8a586bd37fa0000501715321b2e6a7b3ca57894c",
            data=b"file-content-1",
            description="passport.pdf",
        )
        assert file_id == "f6a7b890-1234-5678-9abc-def123456789"

    @my_vcr_no_body.use_cassette("encrypted_files/upload_error.yaml")
    def test_upload_encrypted_file_unexpected_response(self, client):
        with pytest.raises(DidwwClientError, match="Unexpected encrypted_files upload response"):
            client.upload_encrypted_file(
                fingerprint="fingerprint-123",
                data=b"example",
            )

    @my_vcr.use_cassette("encrypted_files/delete.yaml")
    def test_delete_encrypted_file(self, client):
        result = client.encrypted_files().delete("7f2fbdca-8008-44ce-bcb6-3537ea5efaac")
        assert result is None
