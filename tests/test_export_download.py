import gzip
import io
import json
import os
import time

import pytest

from didww import _http
from didww.exceptions import DidwwApiError, DidwwClientError
from tests.support.http_stub import RawServer, Reply, jsonapi_reply, token_reply

CSV = b"Date/Time Start (UTC),Source,Destination\n2026-10-01 00:00:00,1555,972397239159652\n"
GZ = gzip.compress(CSV)
PATH = "/v3/exports/02bf6df4-3af9-416c-96be-16e5b7eeb651.csv.gz"


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


def leftovers(directory):
    return [name for name in os.listdir(directory) if name.endswith(".tmp")]


@pytest.fixture
def client(stub, make_client):
    stub.on("POST", "/token", token_reply())
    return make_client()


def export_url(stub, path=PATH):
    return stub.url + path


class TestDownload:
    def test_writes_the_file_unchanged(self, stub, client, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ, {"Content-Type": "application/octet-stream"}))
        dest = tmp_path / "export.csv.gz"

        client.download_export(export_url(stub), str(dest))

        assert dest.read_bytes() == GZ
        assert leftovers(tmp_path) == []
        (hit,) = stub.hits("GET", PATH)
        assert hit.headers["Authorization"] == "Bearer test-access-token"
        assert hit.headers["Accept-Encoding"] == "identity"
        assert "Accept" not in hit.headers
        assert "Api-Key" not in hit.headers

    def test_accepts_path_like_destinations(self, stub, client, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ))
        client.download_export(export_url(stub), tmp_path / "export.csv.gz")
        assert (tmp_path / "export.csv.gz").read_bytes() == GZ

    def test_content_encoding_is_not_decoded(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ, {"Content-Encoding": "gzip"}))
        out = io.BytesIO()
        client.download_export(export_url(stub), out)
        assert out.getvalue() == GZ

    def test_file_object_destination_is_left_open(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ))
        out = io.BytesIO()
        client.download_export(export_url(stub), out)
        assert not out.closed
        assert out.getvalue() == GZ

    def test_replaces_an_existing_file(self, stub, client, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ))
        dest = tmp_path / "export.csv.gz"
        dest.write_bytes(b"old")
        client.download_export(export_url(stub), str(dest))
        assert dest.read_bytes() == GZ

    @pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
    @pytest.mark.parametrize("umask, mode", [(0o002, 0o664), (0o027, 0o640)])
    def test_file_mode_follows_the_umask(self, umask, mode, stub, client, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ))
        dest = tmp_path / "export.csv.gz"
        old = os.umask(umask)
        try:
            client.download_export(export_url(stub), str(dest))
        finally:
            os.umask(old)
        assert dest.stat().st_mode & 0o777 == mode

    def test_concurrent_download_to_the_same_path_uses_its_own_temporary_file(
            self, stub, client, tmp_path, monkeypatch):
        stub.on("GET", PATH, Reply(200, GZ))
        dest = tmp_path / "export.csv.gz"
        write_all = _http.write_all
        started = []

        def start_second_download(write, chunk):
            if not started:
                started.append(True)
                client.download_export(export_url(stub), str(dest))
            write_all(write, chunk)

        monkeypatch.setattr(_http, "write_all", start_second_download)
        client.download_export(export_url(stub), str(dest))

        assert started == [True]
        assert dest.read_bytes() == GZ
        assert leftovers(tmp_path) == []
        assert len(stub.hits("GET", PATH)) == 2

    def test_missing_directory(self, stub, client, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ))
        with pytest.raises(FileNotFoundError):
            client.download_export(export_url(stub), str(tmp_path / "missing" / "export.csv.gz"))

    def test_invalid_destination(self, stub, client):
        with pytest.raises(TypeError):
            client.download_export(export_url(stub), 42)
        assert stub.hits("GET") == []

    def test_retried_after_401_without_writing_the_401_body(self, stub, make_client):
        stub.on("POST", "/token", token_reply("old-token"), token_reply("new-token"))

        def reply(request):
            if request.headers.get("Authorization") == "Bearer new-token":
                return Reply(200, GZ)
            return jsonapi_reply(401, {"errors": [{"title": "Unauthorized"}]})

        stub.on("GET", PATH, reply)
        out = io.BytesIO()
        make_client().download_export(export_url(stub), out)
        assert out.getvalue() == GZ
        assert len(stub.hits("GET", PATH)) == 2


class TestOrigin:
    @pytest.mark.parametrize("url", [
        "https://evil.example.com" + PATH,
        "http://127.0.0.1:1" + PATH,
        "https://127.0.0.1" + PATH,
        "https://user:pw@sandbox-api.didww.com" + PATH,
        "https://sandbox-api.didww.com\\@evil.example.com" + PATH,
        "https://sandbox-api.didww.com\t.evil.example.com" + PATH,
        "http://sandbox-api.didww.com" + PATH,
        "https://sandbox-api.didww.com:8443" + PATH,
        PATH,
        "",
        None,
    ])
    def test_other_origins_refused_without_a_request(self, stub, client, url):
        out = io.BytesIO()
        e = capture(lambda: client.download_export(url, out))
        assert isinstance(e, DidwwClientError)
        assert "does not match the API base URL" in str(e)
        assert "pw" not in str(e)
        assert stub.requests == []
        assert out.getvalue() == b""

    def test_message_names_the_origins(self, stub, client):
        e = capture(lambda: client.download_export("https://evil.example.com/x", io.BytesIO()))
        port = stub.url.rsplit(":", 1)[1]
        assert str(e) == (f"Export URL https://evil.example.com:443 does not match the API base URL "
                          f"http://127.0.0.1:{port} or the environment URL https://sandbox-api.didww.com:443")

    @pytest.mark.parametrize("url", [
        "https://sandbox-api.didww.com" + PATH,
        "https://SANDBOX-API.didww.com" + PATH,
        "HTTPS://sandbox-api.didww.com:443" + PATH,
        "https://sandbox-api.didww.com." + PATH,
    ])
    def test_environment_origin_accepted_with_a_custom_base_url(self, client, url):
        client._check_export_url(url)

    def test_base_url_origin_accepted(self, stub, client):
        client._check_export_url(stub.url + "/anything")
        client._check_export_url(stub.url.replace("127.0.0.1", "127.0.0.1.") + "/anything")


class TestStatus:
    @pytest.mark.parametrize("reply", [
        Reply(204),
        Reply(302, b"", {"Location": "/elsewhere"}),
        Reply(302, b"", {"Location": "http://[::1/x"}),
        Reply(206, GZ[:5]),
    ])
    def test_only_200_is_written(self, stub, client, tmp_path, reply):
        stub.on("GET", PATH, reply)
        dest = tmp_path / "export.csv.gz"
        dest.write_bytes(b"old")
        e = capture(lambda: client.download_export(export_url(stub), str(dest)))
        assert isinstance(e, DidwwApiError)
        assert e.status_code == reply.status
        assert dest.read_bytes() == b"old"
        assert leftovers(tmp_path) == []
        assert stub.hits(path="/elsewhere") == []

    def test_api_errors_parsed(self, stub, client):
        stub.on("GET", PATH, jsonapi_reply(404, {"errors": [{"title": "Not found", "detail": "Export not found"}]}))
        e = capture(lambda: client.download_export(export_url(stub), io.BytesIO()))
        assert e.status_code == 404
        assert str(e) == "Export not found"

    def test_error_body_is_limited_in_size(self, stub, client):
        body = json.dumps({"errors": [{"title": "t", "detail": "real"}], "pad": "x" * (2 << 20)}).encode()
        stub.on("GET", PATH, Reply(404, body))
        e = capture(lambda: client.download_export(export_url(stub), io.BytesIO()))
        assert (e.status_code, e.errors) == (404, [{"title": "HTTP 404"}])

    def test_error_body_is_read_within_a_deadline(self, stub, make_client):
        def trickle(conn, request):
            conn.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 200\r\n\r\n{")
            for _ in range(200):
                conn.sendall(b" ")
                time.sleep(0.05)

        server = RawServer(trickle)
        stub.on("POST", "/token", token_reply())
        try:
            client = make_client(base_url=server.url + "/v3")
            client._error_body_timeout = 0.3
            started = time.monotonic()
            e = capture(lambda: client.download_export(server.url + PATH, io.BytesIO()))
            elapsed = time.monotonic() - started
        finally:
            server.close()
        assert isinstance(e, DidwwApiError)
        assert e.status_code == 503
        assert elapsed < 3


def _short_body_server(body, declared):
    def script(conn, request):
        conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Length: {declared}\r\nConnection: close\r\n\r\n".encode() + body)

    return RawServer(script)


class TestFailures:
    @pytest.mark.parametrize("decompress", [False, True])
    def test_cut_body_is_incomplete_and_keeps_the_destination(self, stub, make_client, tmp_path, decompress):
        server = _short_body_server(GZ[:20], len(GZ))
        stub.on("POST", "/token", token_reply())
        dest = tmp_path / "export"
        dest.write_bytes(b"old")
        try:
            client = make_client(base_url=server.url + "/v3")
            download = client.download_and_decompress_export if decompress else client.download_export
            e = capture(lambda: download(server.url + PATH, str(dest)))
        finally:
            server.close()
        assert isinstance(e, DidwwClientError)
        assert str(e).startswith("Export data is incomplete")
        assert dest.read_bytes() == b"old"
        assert leftovers(tmp_path) == []

    @pytest.mark.parametrize("decompress", [False, True])
    def test_stalled_body_fails_to_read(self, stub, make_client, decompress):
        def stall(conn, request):
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Length: {len(GZ)}\r\n\r\n".encode() + GZ[:12])
            time.sleep(2)

        server = RawServer(stall)
        stub.on("POST", "/token", token_reply())
        try:
            client = make_client(base_url=server.url + "/v3", read_timeout=0.3)
            download = client.download_and_decompress_export if decompress else client.download_export
            e = capture(lambda: download(server.url + PATH, io.BytesIO()))
        finally:
            server.close()
        assert isinstance(e, DidwwClientError)
        assert str(e).startswith("Failed to read export data")

    def test_destination_write_error_propagates(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ))

        class Full(io.RawIOBase):
            def writable(self):
                return True

            def write(self, data):
                raise OSError(28, "No space left on device")

        e = capture(lambda: client.download_export(export_url(stub), Full()))
        assert type(e) is OSError
        assert e.errno == 28

    @pytest.mark.parametrize("decompress", [False, True])
    def test_interrupt_removes_the_temporary_file(self, stub, client, tmp_path, monkeypatch, decompress):
        stub.on("GET", PATH, Reply(200, GZ))
        dest = tmp_path / "export"

        def interrupt(write, chunk):
            raise KeyboardInterrupt

        monkeypatch.setattr(_http, "write_all", interrupt)
        download = client.download_and_decompress_export if decompress else client.download_export
        e = capture(lambda: download(export_url(stub), str(dest)))
        assert isinstance(e, KeyboardInterrupt)
        assert os.listdir(tmp_path) == []

    def test_short_writes_are_completed(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ))

        class Halves(io.RawIOBase):
            def __init__(self):
                self.data = b""

            def writable(self):
                return True

            def write(self, data):
                n = max(1, len(data) // 2)
                self.data += bytes(data[:n])
                return n

        out = Halves()
        client.download_export(export_url(stub), out)
        assert out.data == GZ

    def test_destination_accepting_no_data_fails(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ))

        class Stuck(io.RawIOBase):
            def writable(self):
                return True

            def write(self, data):
                return 0

        e = capture(lambda: client.download_export(export_url(stub), Stuck()))
        assert type(e) is OSError
        assert str(e) == "the destination accepted no data"

    def test_raw_destination_that_would_block_fails(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ))

        class WouldBlock(io.RawIOBase):
            def writable(self):
                return True

            def write(self, data):
                return None

        e = capture(lambda: client.download_export(export_url(stub), WouldBlock()))
        assert type(e) is OSError
        assert str(e) == "the destination accepted no data"

    def test_plain_destination_returning_none_takes_the_whole_chunk(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ))

        class Sink:
            def __init__(self):
                self.data = b""

            def write(self, data):
                self.data += bytes(data)

        out = Sink()
        client.download_export(export_url(stub), out)
        assert out.data == GZ


class TestDecompress:
    def test_to_path(self, stub, client, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ))
        dest = tmp_path / "export.csv"
        client.download_and_decompress_export(export_url(stub), str(dest))
        assert dest.read_bytes() == CSV
        assert leftovers(tmp_path) == []

    def test_to_file_object(self, stub, client):
        stub.on("GET", PATH, Reply(200, GZ, {"Content-Encoding": "gzip"}))
        out = io.BytesIO()
        client.download_and_decompress_export(export_url(stub), out)
        assert out.getvalue() == CSV

    def test_multi_member_gzip_read_in_full(self, stub, client):
        stub.on("GET", PATH, Reply(200, gzip.compress(b"a,b\n") + gzip.compress(b"c,d\n")))
        out = io.BytesIO()
        client.download_and_decompress_export(export_url(stub), out)
        assert out.getvalue() == b"a,b\nc,d\n"

    @pytest.mark.parametrize("body", [
        gzip.compress(b"a,b\n") + gzip.compress(b"c,d\n")[:5],
        gzip.compress(b"a,b\n") + b"junk",
        GZ[:-8],
        b"Date,Source\n",
    ])
    def test_bad_gzip_fails_to_decompress(self, stub, client, tmp_path, body):
        stub.on("GET", PATH, Reply(200, body))
        dest = tmp_path / "export.csv"
        dest.write_bytes(b"old")
        e = capture(lambda: client.download_and_decompress_export(export_url(stub), str(dest)))
        assert isinstance(e, DidwwClientError)
        assert str(e) == "Failed to decompress export data"
        assert dest.read_bytes() == b"old"
        assert leftovers(tmp_path) == []

    def test_empty_body_fails_to_decompress(self, stub, client):
        stub.on("GET", PATH, Reply(200, b""))
        e = capture(lambda: client.download_and_decompress_export(export_url(stub), io.BytesIO()))
        assert str(e) == "Failed to decompress export data: the export is empty"
