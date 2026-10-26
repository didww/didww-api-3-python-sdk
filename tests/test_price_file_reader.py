import csv
import gzip
import io
import zlib

import pytest

from didww.prices import PriceFileReader
from tests.support.http_stub import fixture_bytes

VOICE_IN = fixture_bytes("prices/voice_in_prices.csv.gz")
VOICE_OUT = fixture_bytes("prices/voice_out_prices.csv.gz")


def gz(text):
    return gzip.compress(text if isinstance(text, bytes) else text.encode(), mtime=0)


def read_all(data):
    with PriceFileReader(io.BytesIO(data)) as rows:
        return list(rows)


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


class TestRows:
    def test_voice_in_fixture(self):
        rows = read_all(VOICE_IN)
        assert len(rows) == 4
        assert rows[1] == {
            "Country": "United Kingdom",
            "Src country name": "United Kingdom",
            "Source type": "fixed",
            "Destination": "4480012",
            "Rate (USD, excl. VAT)": "0.0125",
            "Connection fee (USD, excl. VAT)": "0.0",
            "Initial interval": "60",
            "Next interval": "60",
            "Reject calls": "false",
        }

    def test_voice_out_fixture(self):
        rows = read_all(VOICE_OUT)
        assert len(rows) == 4
        assert rows[0]["Effective date"] == "2026-11-01T00:00:00Z"
        assert rows[2]["Prefix"] == "99950,99951,99952"
        assert rows[3]["Rate"] == ""

    def test_fixtures_have_no_name_and_mtime_zero(self):
        for data in (VOICE_IN, VOICE_OUT):
            assert data[3] & 0x08 == 0
            assert data[4:8] == b"\0\0\0\0"

    def test_byte_order_mark_is_skipped_once(self):
        assert read_all(gz(b"\xef\xbb\xbfa,b\n\xef\xbb\xbf1,2\n")) == [{"a": "\ufeff1", "b": "2"}]

    def test_crlf_quotes_and_empty_lines(self):
        data = gz(b'a,b\r\n\r\n"x\r\ny","q""q"\r\n\n3,\r\n')
        assert read_all(data) == [{"a": "x\r\ny", "b": 'q"q'}, {"a": "3", "b": ""}]

    def test_invalid_utf8_is_replaced(self):
        assert read_all(gz(b"a\n\xff\n")) == [{"a": "\ufffd"}]

    def test_header_only_and_empty_csv(self):
        assert read_all(gz("a,b\n")) == []
        assert read_all(gz("")) == []

    def test_multi_member_read_in_full(self):
        assert read_all(gz("a,b\n1,2\n") + gz("3,4\n")) == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]

    def test_duplicate_header_names_keep_the_last_value(self):
        assert read_all(gz("a,a\n1,2\n")) == [{"a": "2"}]


class TestErrors:
    @pytest.mark.parametrize("data", [b"a,b\n1,2\n", gz("a\n1\n") + b"junk"])
    def test_not_gzip(self, data):
        assert isinstance(capture(lambda: read_all(data)), gzip.BadGzipFile)

    def test_bad_checksum(self):
        data = bytearray(gz("a\n1\n"))
        data[-8] ^= 0xFF
        assert isinstance(capture(lambda: read_all(bytes(data))), gzip.BadGzipFile)

    def test_corrupt_compressed_data(self):
        header = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff"
        reserved_block_type = b"\x07"  # BFINAL=1, BTYPE=11
        data = header + reserved_block_type + bytes(7) + bytes(8)
        e = capture(lambda: read_all(data))
        assert type(e) is gzip.BadGzipFile
        assert str(e).startswith("invalid compressed data: ")
        assert isinstance(e.__cause__, zlib.error)

    @pytest.mark.parametrize("data", [
        VOICE_IN[:-8],
        VOICE_IN[:20],
        gz("a\n1\n") + gz("2\n")[:1],
        gz("a\n1\n") + gz("2\n")[:9],
    ])
    def test_cut_short(self, data):
        assert isinstance(capture(lambda: read_all(data)), (EOFError, gzip.BadGzipFile))

    def test_cut_short_is_eof(self):
        e = capture(lambda: read_all(VOICE_IN[:-8]))
        assert type(e) is EOFError

    def test_empty_input(self):
        e = capture(lambda: read_all(b""))
        assert type(e) is EOFError
        assert str(e) == "price file is empty"

    def test_field_count_mismatch(self):
        e = capture(lambda: read_all(gz("a,b\n1,2\n3\n")))
        assert type(e) is csv.Error
        assert str(e) == "price file record on line 3: wrong number of fields"

    def test_bad_quoting(self):
        assert type(capture(lambda: read_all(gz('a,b\n"x"y,1\n')))) is csv.Error

    def test_rows_before_an_error_are_returned(self):
        rows = []
        with PriceFileReader(io.BytesIO(gz("a\n1\n2,3\n"))) as reader:
            e = capture(lambda: rows.extend(reader))
        assert rows == [{"a": "1"}]
        assert type(e) is csv.Error


class TestSources:
    def test_path_is_opened_at_once_and_closed_on_exit(self, tmp_path):
        path = tmp_path / "prices.csv.gz"
        path.write_bytes(VOICE_IN)
        with PriceFileReader(str(path)) as rows:
            first = next(rows)
            opened = rows._file
            assert not opened.closed
        assert first["Destination"] == "44800"
        assert opened.closed

    def test_path_like(self, tmp_path):
        path = tmp_path / "prices.csv.gz"
        path.write_bytes(VOICE_OUT)
        with PriceFileReader(path) as rows:
            assert len(list(rows)) == 4

    def test_missing_file_fails_at_construction(self, tmp_path):
        assert isinstance(capture(lambda: PriceFileReader(tmp_path / "missing.csv.gz")), FileNotFoundError)

    def test_file_object_is_left_open(self):
        source = io.BytesIO(VOICE_IN)
        with PriceFileReader(source) as rows:
            list(rows)
        assert not source.closed

    def test_invalid_source(self):
        assert isinstance(capture(lambda: PriceFileReader(42)), TypeError)

    def test_closed_reader(self):
        reader = PriceFileReader(io.BytesIO(VOICE_IN))
        reader.close()
        reader.close()
        assert isinstance(capture(lambda: next(reader)), ValueError)

    def test_iterates_once(self):
        with PriceFileReader(io.BytesIO(VOICE_IN)) as rows:
            assert iter(rows) is rows
            assert len(list(rows)) == 4
            assert list(rows) == []

    def test_reads_a_download(self, stub, make_client, tmp_path):
        from tests.support.http_stub import Reply, token_reply

        stub.on("POST", "/token", token_reply(aud=("api-vout.didww.com",)))
        stub.on("GET", "/v3/prices.csv.gz", Reply(200, VOICE_OUT))
        path = tmp_path / "voice_out.csv.gz"
        make_client().voice_out_prices().download_to_file(path)
        with PriceFileReader(path) as rows:
            assert [row["Category"] for row in rows] == ["International", "Origin based", "International",
                                                         "International"]
