import io
import json

import pytest

from didww.exceptions import DidwwApiError, DidwwClientError
from tests.support.http_stub import Reply, jsonapi_reply, token_reply

FINGERPRINT = "c74684d7863639169c21c4d04747f8d6fa05cfe3:::8a586bd37fa0000501715321b2e6a7b3ca57894c"
CREATED = Reply(201, {"data": {"id": "f6a7b890-1234-5678-9abc-def123456789", "type": "encrypted_files"}})


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


@pytest.fixture
def client(stub, make_client):
    stub.on("POST", "/token", token_reply())
    return make_client()


def test_upload_sends_multipart_with_bearer(stub, client):
    stub.on("POST", "/v3/encrypted_files", CREATED)
    file_id = client.upload_encrypted_file(FINGERPRINT, b"encrypted-bytes", description="passport.pdf")

    assert file_id == "f6a7b890-1234-5678-9abc-def123456789"
    (hit,) = stub.hits("POST", "/v3/encrypted_files")
    assert hit.headers["Authorization"] == "Bearer test-access-token"
    assert "Api-Key" not in hit.headers
    assert hit.headers["Accept"] == "application/json"
    assert hit.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'name="encrypted_files[encryption_fingerprint]"' in hit.body
    assert FINGERPRINT.encode() in hit.body
    assert b'name="encrypted_files[file]"; filename="file.enc"' in hit.body
    assert b"encrypted-bytes" in hit.body
    assert b'name="encrypted_files[description]"' in hit.body


def test_file_object_is_read_once_and_replayed_after_401(stub, make_client):
    stub.on("POST", "/token", token_reply("old-token"), token_reply("new-token"))

    def reply(request):
        if request.headers.get("Authorization") == "Bearer new-token":
            return CREATED
        return jsonapi_reply(401, {"errors": [{"title": "Unauthorized"}]})

    stub.on("POST", "/v3/encrypted_files", reply)
    source = io.BytesIO(b"encrypted-bytes")

    make_client().upload_encrypted_file(FINGERPRINT, source)

    first, second = stub.hits("POST", "/v3/encrypted_files")
    assert b"encrypted-bytes" in first.body
    assert b"encrypted-bytes" in second.body


@pytest.mark.parametrize("data", ["text", 42, None])
def test_data_must_be_bytes_or_binary_file(stub, client, data):
    with pytest.raises(TypeError):
        client.upload_encrypted_file(FINGERPRINT, data)
    assert stub.hits("POST", "/v3/encrypted_files") == []


def test_text_file_object_rejected(stub, client):
    with pytest.raises(TypeError):
        client.upload_encrypted_file(FINGERPRINT, io.StringIO("text"))


def test_api_errors_are_kept(stub, client):
    stub.on("POST", "/v3/encrypted_files", jsonapi_reply(422, {"errors": [
        {"title": "is invalid", "detail": "encryption_fingerprint - is invalid"}]}))
    e = capture(lambda: client.upload_encrypted_file(FINGERPRINT, b"x"))
    assert isinstance(e, DidwwApiError)
    assert e.status_code == 422
    assert e.errors == [{"title": "is invalid", "detail": "encryption_fingerprint - is invalid"}]


def test_error_body_is_limited_in_size(stub, client):
    body = json.dumps({"errors": [{"title": "t"}], "pad": "x" * (2 << 20)}).encode()
    stub.on("POST", "/v3/encrypted_files", Reply(400, body))
    e = capture(lambda: client.upload_encrypted_file(FINGERPRINT, b"x"))
    assert (e.status_code, e.errors) == (400, [{"title": "HTTP 400"}])


def test_redirect_is_an_error_and_not_followed(stub, client):
    stub.on("POST", "/v3/encrypted_files", Reply(307, b"", {"Location": stub.url + "/elsewhere"}))
    e = capture(lambda: client.upload_encrypted_file(FINGERPRINT, b"x"))
    assert isinstance(e, DidwwApiError)
    assert e.status_code == 307
    assert stub.hits(path="/elsewhere") == []


@pytest.mark.parametrize("body", [b'{"unexpected":"response"}', b"not json", b'{"data": []}', b""])
def test_unexpected_response(stub, client, body):
    stub.on("POST", "/v3/encrypted_files", Reply(201, body))
    with pytest.raises(DidwwClientError, match="Unexpected encrypted_files upload response"):
        client.upload_encrypted_file(FINGERPRINT, b"x")
