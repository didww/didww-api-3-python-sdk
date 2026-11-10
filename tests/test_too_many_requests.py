import io
from types import SimpleNamespace

import pytest

from didww.exceptions import DidwwApiError
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup
from tests.support.http_stub import Reply, jsonapi_reply, token_reply

GROUP_ID = "8bf3f1f0-1e5b-4cf3-9e1e-6c6a0d6f1f3a"
GROUP_PATH = f"/v3/voice_in_trunk_groups/{GROUP_ID}"
EXPORT_PATH = "/v3/exports/02bf6df4-3af9-416c-96be-16e5b7eeb651.csv.gz"
TOO_MANY = {"errors": [{"title": "Too many requests", "code": "too_many_requests", "status": "429"}]}


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


@pytest.fixture
def ctx(stub, client, tmp_path):
    return SimpleNamespace(client=client, export_url=stub.url + EXPORT_PATH, tmp_path=tmp_path)


def _group():
    group = VoiceInTrunkGroup()
    group.name = "Primary"
    return group


def _renamed_group():
    group = VoiceInTrunkGroup.build(GROUP_ID)
    group.name = "Renamed"
    return group


# (method, path, call) of every path a 429 can reach: JSON:API reads and writes,
# the export downloads and the encrypted file upload.
CALLS = [
    ("GET", "/v3/voice_in_trunk_groups", lambda ctx: ctx.client.voice_in_trunk_groups().list()),
    ("POST", "/v3/voice_in_trunk_groups", lambda ctx: ctx.client.voice_in_trunk_groups().create(_group())),
    ("PATCH", GROUP_PATH, lambda ctx: ctx.client.voice_in_trunk_groups().update(_renamed_group())),
    ("DELETE", GROUP_PATH, lambda ctx: ctx.client.voice_in_trunk_groups().delete(GROUP_ID)),
    ("GET", EXPORT_PATH, lambda ctx: ctx.client.download_export(ctx.export_url, io.BytesIO())),
    ("GET", EXPORT_PATH, lambda ctx: ctx.client.download_export(ctx.export_url, ctx.tmp_path / "e.csv.gz")),
    ("GET", EXPORT_PATH,
     lambda ctx: ctx.client.download_and_decompress_export(ctx.export_url, ctx.tmp_path / "e.csv")),
    ("POST", "/v3/encrypted_files", lambda ctx: ctx.client.upload_encrypted_file("fingerprint", b"x")),
]
IDS = ["read", "create", "update", "delete", "export", "export_to_path", "export_decompressed", "upload"]


@pytest.mark.parametrize("method, path, call", CALLS, ids=IDS)
def test_429_carries_retry_after_and_is_not_retried(stub, ctx, tmp_path, method, path, call):
    stub.on(method, path, jsonapi_reply(429, TOO_MANY, {"Retry-After": "17"}))

    e = capture(lambda: call(ctx))

    assert type(e) is DidwwApiError
    assert (e.status_code, e.retry_after) == (429, 17)
    assert e.errors == TOO_MANY["errors"]
    assert len(stub.hits(method, path)) == 1
    assert [p.name for p in tmp_path.iterdir()] == []
    for text in (str(e), repr(e)):
        assert "test-access-token" not in text
        assert "test-api-key" not in text


@pytest.mark.parametrize("method, path, call", CALLS, ids=IDS)
def test_retry_after_of_another_error_status(stub, ctx, method, path, call):
    stub.on(method, path, jsonapi_reply(503, {"errors": [{"title": "Service unavailable"}]}, {"Retry-After": "5"}))
    e = capture(lambda: call(ctx))
    assert (e.status_code, e.retry_after) == (503, 5)


@pytest.mark.parametrize("method, path, call", CALLS, ids=IDS)
def test_retry_after_is_none_without_the_header(stub, ctx, method, path, call):
    stub.on(method, path, jsonapi_reply(429, TOO_MANY))
    e = capture(lambda: call(ctx))
    assert (e.status_code, e.retry_after) == (429, None)


@pytest.mark.parametrize("value, seconds", [
    ("1", 1),
    (" 60 ", 60),
    ("999999999", 999999999),
    ("1.5", None),
    ("-1", None),
    ("+5", None),
    ("1e3", None),
    ("abc", None),
    ("", None),
    ("1000000000", None),
    ("99999999999999999999", None),
    ("Thu, 01 Oct 2026 08:05:03 GMT", None),
])
def test_retry_after_values(stub, client, value, seconds):
    stub.on("GET", "/v3/voice_in_trunk_groups", jsonapi_reply(429, TOO_MANY, {"Retry-After": value}))
    e = capture(lambda: client.voice_in_trunk_groups().list())
    assert e.retry_after == seconds


@pytest.mark.parametrize("method, path, call", CALLS, ids=IDS)
def test_429_without_an_errors_document(stub, ctx, method, path, call):
    stub.on(method, path, Reply(429, b"slow down", {"Retry-After": "3"}))
    e = capture(lambda: call(ctx))
    assert (e.status_code, e.errors, e.retry_after) == (429, [{"title": "HTTP 429"}], 3)
