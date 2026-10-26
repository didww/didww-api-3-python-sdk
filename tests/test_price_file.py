import io
import os
import time
from datetime import datetime, timedelta, timezone

import pytest
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from didww.exceptions import DidwwPricesError, PricesErrorKind
from didww.prices import PriceFile
from tests.support.http_stub import RawServer, Reply, fixture_bytes, fixture_json, token_reply

GZ = fixture_bytes("prices/voice_in_prices.csv.gz")
PATH = "/v3/prices.csv.gz"
SMS_PATH = "/v3/sms_out/a2p/prices.csv.gz"
LAST_MODIFIED = "Thu, 01 Oct 2026 08:05:03 GMT"
LAST_MODIFIED_AT = datetime(2026, 10, 1, 8, 5, 3, tzinfo=timezone.utc)


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


def leftovers(directory):
    return [name for name in os.listdir(directory) if name.endswith(".tmp")]


def file_reply(body=GZ, status=200, **headers):
    return Reply(status, body, {"Last-Modified": LAST_MODIFIED, **{k.replace("_", "-"): v for k, v in headers.items()}})


@pytest.fixture
def client(stub, make_client):
    stub.on("POST", "/token", lambda r: token_reply(access_token="tok-" + r.json()["aud"][0], aud=r.json()["aud"]))
    return make_client()


@pytest.fixture
def service(client):
    s = client.voice_in_prices()
    s._sleep = lambda seconds: pytest.fail(f"unexpected sleep {seconds}")
    return s


def raw_service(client, script, **kwargs):
    server = RawServer(script)
    client._voice_in_prices_url = server.url
    service = client.voice_in_prices()
    for name, value in kwargs.items():
        setattr(service, name, value)
    return server, service


class TestHead:
    def test_metadata(self, stub, service):
        stub.on("HEAD", PATH, Reply(200, b"", {
            "Last-Modified": LAST_MODIFIED,
            "Content-Disposition": 'attachment; filename="voice_in_prices.csv.gz"',
        }, content_length=1234))

        result = service.head()

        assert result == PriceFile(status_code=200, last_modified=LAST_MODIFIED_AT, content_length=1234,
                                   filename="voice_in_prices.csv.gz", bytes_written=0)
        assert not result.not_modified
        (hit,) = stub.hits("HEAD", PATH)
        assert hit.headers["Authorization"] == "Bearer tok-api-vin.didww.com"
        assert hit.headers["Accept-Encoding"] == "identity"
        assert "Accept" not in hit.headers
        assert "If-Modified-Since" not in hit.headers
        assert "If-None-Match" not in hit.headers

    def test_not_modified(self, stub, service):
        stub.on("HEAD", PATH, Reply(304, b"", {"Last-Modified": LAST_MODIFIED}))
        result = service.head(datetime(2026, 10, 1, 10, 5, 3, 999999, tzinfo=timezone(timedelta(hours=2))))
        assert result.not_modified
        assert result.content_length is None
        assert result.last_modified == LAST_MODIFIED_AT
        assert stub.hits("HEAD", PATH)[0].headers["If-Modified-Since"] == LAST_MODIFIED

    def test_if_modified_since_day_is_padded(self, stub, service):
        stub.on("HEAD", PATH, Reply(304, b""))
        service.head(datetime(2026, 11, 2, 3, 4, 5, tzinfo=timezone.utc))
        assert stub.hits("HEAD", PATH)[0].headers["If-Modified-Since"] == "Mon, 02 Nov 2026 03:04:05 GMT"

    def test_naive_datetime_is_refused(self, stub, service):
        e = capture(lambda: service.head(datetime(2026, 10, 1)))
        assert type(e) is ValueError
        assert str(e) == "if_modified_since must be timezone-aware"
        assert isinstance(capture(lambda: service.head("Thu, 01 Oct 2026 08:05:03 GMT")), TypeError)
        assert isinstance(capture(lambda: service.download(io.BytesIO(), datetime(2026, 10, 1))), ValueError)
        assert stub.requests == []

    @pytest.mark.parametrize("value", [
        datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=1))),
        datetime.max.replace(tzinfo=timezone(timedelta(hours=-1))),
    ])
    def test_out_of_range_datetime_is_refused(self, stub, service, value):
        for call in (lambda: service.head(value), lambda: service.download(io.BytesIO(), value)):
            e = capture(call)
            assert type(e) is ValueError
            assert str(e) == "if_modified_since is out of range"
        assert stub.requests == []

    @pytest.mark.parametrize("value", [
        "Wed, 01 Oct 2026 08:05:03 GMT",
        "Thursday, 01-Oct-26 08:05:03 GMT",
        "Thu Oct  1 08:05:03 2026",
        "Thu, 01 Oct 2026 08:05:03 +0200",
        "Thu, 1 Oct 2026 08:05:03 GMT",
        "Thu, 31 Feb 2026 08:05:03 GMT",
        "garbage",
    ])
    def test_last_modified_must_be_an_imf_fixdate(self, stub, service, value):
        stub.on("HEAD", PATH, Reply(200, b"", {"Last-Modified": value}))
        assert service.head().last_modified is None

    @pytest.mark.parametrize("value, expected", [
        ("attachment; filename=\"plain.csv.gz\"; filename*=UTF-8''na%C3%AFve+x.csv.gz", "na\u00efve+x.csv.gz"),
        ("attachment; filename*=UTF-8''na%C3%AFve+x.csv.gz; filename=plain.csv.gz", "na\u00efve+x.csv.gz"),
        ("attachment; filename*=iso-8859-1'en'caf%E9.csv.gz", "caf\u00e9.csv.gz"),
        ("attachment; filename=\"a \\\"b\\\".csv.gz\"", 'a "b".csv.gz'),
        ("attachment; filename=plain.csv.gz", "plain.csv.gz"),
        ("attachment; filename*=UTF-8''bad%ZZ; filename=plain.csv.gz", "plain.csv.gz"),
        ("attachment; filename*=KOI8-R''x; filename=plain.csv.gz", "plain.csv.gz"),
        ("attachment; filename=\"\"", None),
        ("attachment", None),
    ])
    def test_filename(self, stub, service, value, expected):
        stub.on("HEAD", PATH, Reply(200, b"", {"Content-Disposition": value}))
        assert service.head().filename == expected

    @pytest.mark.parametrize("value", ["-1", "+5", "1_000", "1e3", "abc", "1 2"])
    def test_bad_content_length_is_unknown(self, stub, service, value):
        stub.on("HEAD", PATH, Reply(200, b"", {"Content-Length": value}))
        assert service.head().content_length is None

    def test_bodyless_404_is_price_plan_not_assigned(self, stub, service):
        stub.on("HEAD", PATH, Reply(404, b""))
        e = capture(service.head)
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED
        assert e.code == "price_plan_not_assigned"
        assert e.status_code == 404

    @pytest.mark.parametrize("status", [202, 204, 302])
    def test_other_success_statuses_are_unexpected(self, stub, service, status):
        stub.on("HEAD", PATH, Reply(status, b"", {"Location": stub.url + "/elsewhere"}))
        e = capture(service.head)
        assert e.kind is PricesErrorKind.UNEXPECTED_STATUS
        assert stub.hits(path="/elsewhere") == []

    def test_sms_paths(self, stub, client):
        stub.on("HEAD", SMS_PATH, Reply(200, b""))
        client.sms_out_a2p_prices().head()
        (mint,) = stub.hits("POST", "/token")
        assert mint.json()["aud"] == ["api-sms.didww.com"]
        assert len(stub.hits("HEAD", SMS_PATH)) == 1


class TestDownload:
    def test_writes_the_file_as_served(self, stub, service):
        stub.on("GET", PATH, file_reply(Content_Encoding="gzip", Content_Type="application/gzip"))
        out = io.BytesIO()

        result = service.download(out)

        assert out.getvalue() == GZ
        assert not out.closed
        assert result.content_length == len(GZ)
        assert result.bytes_written == len(GZ)
        assert result.last_modified == LAST_MODIFIED_AT
        (hit,) = stub.hits("GET", PATH)
        assert hit.headers["Accept-Encoding"] == "identity"
        assert "Accept" not in hit.headers
        assert "If-None-Match" not in hit.headers

    def test_not_modified_writes_nothing(self, stub, service):
        stub.on("GET", PATH, Reply(304, b""))
        out = io.BytesIO()
        result = service.download(out, LAST_MODIFIED_AT)
        assert result.not_modified
        assert result.bytes_written == 0
        assert out.getvalue() == b""

    def test_invalid_destination(self, stub, service):
        assert isinstance(capture(lambda: service.download("file.csv.gz")), TypeError)
        assert stub.requests == []

    def test_retried_after_401_without_writing_the_401_body(self, stub, service):
        stub.on("GET", PATH, Reply(401, {"errors": [{"title": "Unauthorized"}]}), file_reply())
        out = io.BytesIO()
        service.download(out)
        assert out.getvalue() == GZ
        assert len(stub.hits("GET", PATH)) == 2

    def test_destination_write_error_propagates(self, stub, service):
        stub.on("GET", PATH, file_reply())

        class Full(io.RawIOBase):
            def writable(self):
                return True

            def write(self, data):
                raise OSError(28, "No space left on device")

        e = capture(lambda: service.download(Full()))
        assert type(e) is OSError
        assert e.errno == 28

    def test_short_writes_are_completed(self, stub, service):
        stub.on("GET", PATH, file_reply())

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
        assert service.download(out).bytes_written == len(GZ)
        assert out.data == GZ

    def test_destination_accepting_no_data_fails(self, stub, service):
        stub.on("GET", PATH, file_reply())

        class Stuck(io.RawIOBase):
            def writable(self):
                return True

            def write(self, data):
                return 0

        e = capture(lambda: service.download(Stuck()))
        assert type(e) is OSError
        assert str(e) == "the destination accepted no data"

    def test_raw_destination_that_would_block_fails(self, stub, service):
        stub.on("GET", PATH, file_reply())

        class WouldBlock(io.RawIOBase):
            def writable(self):
                return True

            def write(self, data):
                return None

        e = capture(lambda: service.download(WouldBlock()))
        assert type(e) is OSError
        assert str(e) == "the destination accepted no data"

    def test_plain_destination_returning_none_takes_the_whole_chunk(self, stub, service):
        stub.on("GET", PATH, file_reply())

        class Sink:
            def __init__(self):
                self.data = b""

            def write(self, data):
                self.data += bytes(data)

        out = Sink()
        service.download(out)
        assert out.data == GZ

    def test_cut_body(self, client):
        def script(conn, request):
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Length: {len(GZ)}\r\nConnection: close\r\n\r\n".encode()
                         + GZ[:10])

        server, service = raw_service(client, script)
        try:
            e = capture(lambda: service.download(io.BytesIO()))
        finally:
            server.close()
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert e.status_code == 200
        assert str(e).startswith("Prices service: incomplete body")

    def test_cut_body_with_a_repeated_content_length(self, client):
        def script(conn, request):
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Length: {len(GZ)}\r\nContent-Length: {len(GZ)}\r\n"
                         f"Connection: close\r\n\r\n".encode() + GZ[:10])

        server, service = raw_service(client, script)
        try:
            e = capture(lambda: service.download(io.BytesIO()))
        finally:
            server.close()
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert str(e).startswith("Prices service: incomplete body")

    def test_chunked_body_ignores_content_length(self, client):
        def script(conn, request):
            conn.sendall(f"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Length: 999999\r\n"
                         f"Connection: close\r\n\r\n{len(GZ):x}\r\n".encode() + GZ + b"\r\n0\r\n\r\n")

        server, service = raw_service(client, script)
        try:
            out = io.BytesIO()
            f = service.download(out)
        finally:
            server.close()
        assert out.getvalue() == GZ
        assert f.content_length is None

    def test_cut_chunked_body(self, client):
        def script(conn, request):
            conn.sendall(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n"
                         b"64\r\n" + GZ[:10])

        server, service = raw_service(client, script)
        try:
            e = capture(lambda: service.download(io.BytesIO()))
        finally:
            server.close()
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert e.status_code == 200

    def test_stalled_body(self, make_client, stub):
        stub.on("POST", "/token", token_reply(aud=("api-vin.didww.com",)))
        client = make_client(read_timeout=0.5)

        def script(conn, request):
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Length: {len(GZ)}\r\n\r\n".encode() + GZ[:10])
            time.sleep(3)

        server, service = raw_service(client, script)
        try:
            started = time.monotonic()
            e = capture(lambda: service.download(io.BytesIO()))
            elapsed = time.monotonic() - started
        finally:
            server.close()
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert e.status_code == 200
        assert elapsed < 2.5

    def test_stall_before_the_headers(self, make_client, stub):
        stub.on("POST", "/token", token_reply(aud=("api-vin.didww.com",)))
        client = make_client(read_timeout=0.5)
        server, service = raw_service(client, lambda conn, request: time.sleep(3))
        try:
            e = capture(lambda: service.download(io.BytesIO()))
        finally:
            server.close()
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert e.status_code is None
        assert server.accepts == 1


class TestUnavailable:
    @pytest.mark.parametrize("retry_after, random, wait", [
        ("0", 0.0, 1), ("0", 1.0, 2), ("2", 0.0, 2), ("2", 1.0, 3),
        ("30", 0.0, 30), ("30", 1.0, 36), ("60", 1.0, 72),
    ])
    def test_wait(self, stub, service, retry_after, random, wait):
        stub.on("GET", PATH, Reply(503, {"errors": [{"title": "busy"}]}, {"Retry-After": retry_after}), file_reply())
        waits = []
        service._sleep = waits.append
        service._random = lambda: random
        out = io.BytesIO()

        service.download(out)

        assert waits == [wait]
        assert out.getvalue() == GZ
        assert len(stub.hits("GET", PATH)) == 2

    def test_gives_up_after_two_retries(self, stub, service):
        stub.on("GET", PATH, Reply(503, fixture_json("prices/errors/serving_failure.json"), {"Retry-After": "5"}))
        waits = []
        service._sleep = waits.append
        service._random = lambda: 0.0

        e = capture(lambda: service.download(io.BytesIO()))

        assert e.kind is PricesErrorKind.SERVICE_UNAVAILABLE
        assert e.retry_after == 5
        assert e.code == "serving_failure"
        assert waits == [5, 5]
        assert len(stub.hits("GET", PATH)) == 3

    def test_head_is_retried(self, stub, service):
        stub.on("HEAD", PATH, Reply(503, b"", {"Retry-After": "1"}), Reply(200, b""))
        waits = []
        service._sleep = waits.append
        assert service.head().status_code == 200
        assert len(waits) == 1

    @pytest.mark.parametrize("reply", [
        Reply(503, b"", {"Retry-After": "61"}),
        Reply(503, b"", {"Retry-After": LAST_MODIFIED}),
        Reply(503, b""),
        Reply(429, b"", {"Retry-After": "1"}),
        Reply(500, b"", {"Retry-After": "1"}),
    ])
    def test_not_retried(self, stub, service, reply):
        stub.on("GET", PATH, reply)
        e = capture(lambda: service.download(io.BytesIO()))
        assert isinstance(e, DidwwPricesError)
        assert len(stub.hits("GET", PATH)) == 1

    def test_user_retries_are_not_used(self, stub, make_client):
        import requests

        stub.on("POST", "/token", token_reply(aud=("api-vin.didww.com",)))
        session = requests.Session()
        retry = Retry(total=3, status_forcelist=[503], allowed_methods=None, respect_retry_after_header=True)
        session.mount("http://", HTTPAdapter(max_retries=retry))
        client = make_client(session=session)
        stub.on("GET", PATH, Reply(503, b"", {"Retry-After": "0"}))
        service = client.voice_in_prices()
        waits = []
        service._sleep = waits.append

        e = capture(lambda: service.download(io.BytesIO()))

        assert e.kind is PricesErrorKind.SERVICE_UNAVAILABLE
        assert len(stub.hits("GET", PATH)) == 3
        assert len(waits) == 2

    def test_interrupt_during_the_wait_keeps_the_file(self, stub, service, tmp_path):
        stub.on("GET", PATH, Reply(503, b"", {"Retry-After": "1"}))
        dest = tmp_path / "prices.csv.gz"
        dest.write_bytes(b"old")

        def interrupt(seconds):
            raise KeyboardInterrupt

        service._sleep = interrupt
        assert isinstance(capture(lambda: service.download_to_file(dest)), KeyboardInterrupt)
        assert dest.read_bytes() == b"old"
        assert leftovers(tmp_path) == []


class TestDownloadToFile:
    def test_replaces_the_file_and_sets_the_mtime(self, stub, service, tmp_path):
        stub.on("GET", PATH, file_reply())
        dest = tmp_path / "prices.csv.gz"
        dest.write_bytes(b"old")
        other = tmp_path / "other.tmp"
        other.write_bytes(b"keep")

        result = service.download_to_file(str(dest))

        assert result.bytes_written == len(GZ)
        assert dest.read_bytes() == GZ
        assert dest.stat().st_mtime_ns == int(LAST_MODIFIED_AT.timestamp()) * 1_000_000_000
        assert sorted(os.listdir(tmp_path)) == ["other.tmp", "prices.csv.gz"]
        assert other.read_bytes() == b"keep"

    def test_without_last_modified(self, stub, service, tmp_path):
        stub.on("GET", PATH, Reply(200, GZ))
        dest = tmp_path / "prices.csv.gz"
        before = time.time() - 5
        service.download_to_file(dest)
        assert dest.read_bytes() == GZ
        assert dest.stat().st_mtime > before

    @pytest.mark.parametrize("reply", [
        Reply(404, fixture_json("prices/errors/price_plan_not_assigned.json")),
        Reply(200, GZ, content_length=len(GZ) + 10),
    ])
    def test_errors_keep_the_existing_file(self, stub, service, tmp_path, reply):
        stub.on("GET", PATH, reply)
        dest = tmp_path / "prices.csv.gz"
        dest.write_bytes(b"old")
        e = capture(lambda: service.download_to_file(dest))
        assert isinstance(e, DidwwPricesError)
        assert dest.read_bytes() == b"old"
        assert os.listdir(tmp_path) == ["prices.csv.gz"]

    def test_destination_write_error_removes_the_temporary_file(self, stub, service, tmp_path, monkeypatch):
        from didww import _http

        stub.on("GET", PATH, file_reply())

        def interrupt(write, chunk):
            raise KeyboardInterrupt

        monkeypatch.setattr(_http, "write_all", interrupt)
        assert isinstance(capture(lambda: service.download_to_file(tmp_path / "prices.csv.gz")), KeyboardInterrupt)
        assert os.listdir(tmp_path) == []

    def test_concurrent_download_to_the_same_path_uses_its_own_temporary_file(
            self, stub, service, tmp_path, monkeypatch):
        from didww import _http

        stub.on("GET", PATH, file_reply())
        dest = tmp_path / "prices.csv.gz"
        write_all = _http.write_all
        started = []
        second = []

        def start_second_download(write, chunk):
            if not started:
                started.append(True)
                second.append(service.download_to_file(dest))
            write_all(write, chunk)

        monkeypatch.setattr(_http, "write_all", start_second_download)
        first = service.download_to_file(dest)

        assert first.status_code == 200
        assert [r.status_code for r in second] == [200]
        assert dest.read_bytes() == GZ
        assert leftovers(tmp_path) == []
        assert len(stub.hits("GET", PATH)) == 2

    def test_existing_temporary_file_is_never_reused(self, stub, service, tmp_path, monkeypatch):
        from didww import _http

        monkeypatch.setattr(_http.secrets, "token_hex", lambda n: "0" * (2 * n))
        dest = tmp_path / "prices.csv.gz"
        dest.write_bytes(b"old")
        taken = tmp_path / ".prices.csv.gz.0000000000000000.tmp"
        taken.write_bytes(b"another writer")

        assert isinstance(capture(lambda: service.download_to_file(dest)), FileExistsError)
        assert taken.read_bytes() == b"another writer"
        assert dest.read_bytes() == b"old"
        assert stub.hits("GET") == []

    def test_missing_directory_fails_without_a_request(self, stub, service, tmp_path):
        e = capture(lambda: service.download_to_file(tmp_path / "missing" / "prices.csv.gz"))
        assert isinstance(e, FileNotFoundError)
        assert stub.hits("GET") == []

    def test_bare_file_name(self, stub, service, tmp_path, monkeypatch):
        stub.on("GET", PATH, file_reply())
        monkeypatch.chdir(tmp_path)
        service.download_to_file("prices.csv.gz")
        assert (tmp_path / "prices.csv.gz").read_bytes() == GZ
        assert leftovers(tmp_path) == []

    def test_invalid_path(self, stub, service):
        assert isinstance(capture(lambda: service.download_to_file(io.BytesIO())), TypeError)
        assert isinstance(capture(lambda: service.fetch(None)), TypeError)
        assert stub.requests == []

    @pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
    @pytest.mark.parametrize("umask, mode", [(0o002, 0o664), (0o027, 0o640)])
    def test_file_mode_follows_the_umask(self, umask, mode, stub, service, tmp_path):
        stub.on("GET", PATH, file_reply())
        dest = tmp_path / "prices.csv.gz"
        old = os.umask(umask)
        try:
            service.download_to_file(dest)
        finally:
            os.umask(old)
        assert dest.stat().st_mode & 0o777 == mode


class TestFetch:
    def test_without_a_file(self, stub, service, tmp_path):
        stub.on("GET", PATH, file_reply())
        dest = tmp_path / "prices.csv.gz"
        result = service.fetch(dest)
        assert result.status_code == 200
        assert dest.read_bytes() == GZ
        assert "If-Modified-Since" not in stub.hits("GET", PATH)[0].headers

    def test_sends_the_mtime_and_keeps_the_file_on_304(self, stub, service, tmp_path):
        stub.on("GET", PATH, Reply(304, b""))
        dest = tmp_path / "prices.csv.gz"
        dest.write_bytes(b"current")
        mtime = int(LAST_MODIFIED_AT.timestamp()) * 1_000_000_000 + 999_999_999
        os.utime(dest, ns=(mtime, mtime))

        result = service.fetch(dest)

        assert result.not_modified
        assert stub.hits("GET", PATH)[0].headers["If-Modified-Since"] == LAST_MODIFIED
        assert dest.read_bytes() == b"current"
        assert dest.stat().st_mtime_ns == mtime
        assert os.listdir(tmp_path) == ["prices.csv.gz"]

    def test_replaces_a_changed_file(self, stub, service, tmp_path):
        stub.on("GET", PATH, file_reply())
        dest = tmp_path / "prices.csv.gz"
        dest.write_bytes(b"stale")
        os.utime(dest, (0, 0))

        result = service.fetch(str(dest))

        assert result.status_code == 200
        assert stub.hits("GET", PATH)[0].headers["If-Modified-Since"] == "Thu, 01 Jan 1970 00:00:00 GMT"
        assert dest.read_bytes() == GZ

    def test_round_trip(self, stub, service, tmp_path):
        stub.on("GET", PATH, file_reply(), Reply(304, b""))
        dest = tmp_path / "prices.csv.gz"
        service.fetch(dest)
        assert service.fetch(dest).not_modified
        assert stub.hits("GET", PATH)[1].headers["If-Modified-Since"] == LAST_MODIFIED
