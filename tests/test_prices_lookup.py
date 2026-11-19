import copy
import enum
import json
import pickle
import time
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from didww.client import DidwwClient
from didww.exceptions import DidwwAuthError, DidwwClientError, DidwwError, DidwwPricesError, PricesErrorKind
from didww.prices import (
    PriceLookup,
    PricesService,
    SmsInPrice,
    SmsOutPrice,
    VoiceInPrice,
    VoiceOutPrice,
    VoiceOutPriceCategory,
)
from tests.support.http_stub import RawServer, Reply, fixture_bytes, fixture_json, http_response, token_reply

VOICE_IN = "api-vin.didww.com"
VOICE_OUT = "api-vout.didww.com"
SMS = "api-sms.didww.com"


def capture(fn):
    try:
        fn()
    except BaseException as e:
        return e
    raise AssertionError("no exception raised")


def jsonapi(body, status=200, headers=None):
    if not isinstance(body, (bytes, str)):
        body = json.dumps(body)
    return Reply(status, body, {"Content-Type": "application/vnd.api+json", **(headers or {})})


def one_row(attributes, row_id="row-1", meta=None):
    document = {"data": [{"id": row_id, "type": "prices", "attributes": attributes}]}
    if meta is not None:
        document["meta"] = meta
    return document


def mints(stub):
    return stub.hits("POST", "/token")


@pytest.fixture
def client(stub, make_client):
    stub.on("POST", "/token", lambda r: token_reply(access_token="tok-" + r.json()["aud"][0], aud=r.json()["aud"]))
    return make_client()


class TestAccessors:
    @pytest.mark.parametrize("accessor, path, audience", [
        ("voice_in_prices", "/v3/lookup/prices", VOICE_IN),
        ("voice_out_prices", "/v3/lookup/prices", VOICE_OUT),
        ("sms_out_a2p_prices", "/v3/sms_out/a2p/lookup/prices", SMS),
        ("sms_out_p2p_prices", "/v3/sms_out/p2p/lookup/prices", SMS),
        ("sms_out_otp_prices", "/v3/sms_out/otp/lookup/prices", SMS),
        ("sms_in_prices", "/v3/sms_in/lookup/prices", SMS),
    ])
    def test_path_and_audience(self, stub, client, accessor, path, audience):
        stub.on("GET", path, jsonapi(fixture_bytes("prices/voice_in/lookup/200.json")))
        service = getattr(client, accessor)()
        filters = {"number": "18005550123"} if "voice" in accessor else {"dst_number": "18005550123"}

        assert len(service.lookup(filters)) == 2

        (mint,) = mints(stub)
        assert mint.json()["aud"] == [audience]
        (hit,) = stub.hits("GET", path)
        assert hit.headers["Authorization"] == "Bearer tok-" + audience
        assert hit.headers["Accept"] == "application/vnd.api+json"
        assert hit.headers["Accept-Encoding"] == "identity"
        assert "Api-Key" not in hit.headers

    def test_paths(self, client):
        service = client.sms_out_a2p_prices()
        assert isinstance(service, PricesService)
        assert service.file_path == "sms_out/a2p/prices.csv.gz"
        assert service.lookup_path == "sms_out/a2p/lookup/prices"
        assert client.voice_in_prices().file_path == "prices.csv.gz"
        assert client.voice_in_prices().allowed_filters == ("number", "src_country_iso")

    @pytest.mark.parametrize("url", ["https://prices.example.com", "https://prices.example.com/",
                                     "https://prices.example.com/v3", "https://prices.example.com/v3/"])
    def test_v3_is_added_once(self, url):
        client = DidwwClient("test-api-key", voice_in_prices_url=url)
        assert repr(client.voice_in_prices()) == "PricesService('https://prices.example.com/v3/lookup/prices')"

    def test_environment_urls(self):
        from didww.configuration import Environment

        client = DidwwClient("test-api-key", environment=Environment.PRODUCTION)
        assert repr(client.voice_out_prices()) == "PricesService('https://api-vout.didww.com/v3/lookup/prices')"
        assert repr(client.sms_in_prices()) == "PricesService('https://api-sms.didww.com/v3/sms_in/lookup/prices')"

    def test_url_with_user_info_is_refused(self):
        e = capture(lambda: DidwwClient("test-api-key", sms_prices_url="https://user:secret@prices.example.com"))
        assert isinstance(e, DidwwClientError)
        assert "secret" not in str(e)


class TestFilters:
    @pytest.mark.parametrize("accessor, filters, message", [
        ("voice_in_prices", {}, "Filter number is required on lookup/prices"),
        ("voice_in_prices", None, "Filter number is required on lookup/prices"),
        ("voice_in_prices", {"src_country_iso": "US"}, "Filter number is required on lookup/prices"),
        ("voice_in_prices", {"number": "1", "zeta": "1", "alpha": "1"},
         "Filter alpha, zeta is not allowed on lookup/prices (allowed: number, src_country_iso)"),
        ("voice_out_prices", {"number": "1", "src_country_iso": "US"},
         "Filter src_country_iso is not allowed on lookup/prices (allowed: number)"),
        ("sms_out_a2p_prices", {},
         "One of filters dst_number, dst_country_iso is required on sms_out/a2p/lookup/prices"),
        ("sms_in_prices", {"dst_number": " "},
         "One of filters dst_number, dst_country_iso is required on sms_in/lookup/prices"),
        ("sms_out_otp_prices", {"number": "1"},
         "Filter number is not allowed on sms_out/otp/lookup/prices (allowed: dst_number, dst_country_iso)"),
    ])
    def test_rejected_before_any_request(self, stub, client, accessor, filters, message):
        e = capture(lambda: getattr(client, accessor)().lookup(filters))
        assert type(e) is ValueError
        assert str(e) == message
        assert stub.requests == []

    @pytest.mark.parametrize("filters", [{"number": 1.5}, {"number": True}, {1: "x"}, ["number"]])
    def test_bad_types(self, stub, client, filters):
        assert isinstance(capture(lambda: client.voice_in_prices().lookup(filters)), TypeError)
        assert stub.requests == []

    def test_blank_and_none_dropped_and_encoded_in_order(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", jsonapi(fixture_bytes("prices/voice_in/lookup/200.json")))
        client.voice_in_prices().lookup({"src_country_iso": "US", "number": "1 2+3"})
        client.voice_in_prices().lookup({"number": 18005550123, "src_country_iso": None})
        client.voice_in_prices().lookup({"number": "18005550123", "src_country_iso": "  "})

        first, second, third = stub.hits("GET", "/v3/lookup/prices")
        assert first.query == {"filter[number]": ["1 2+3"], "filter[src_country_iso]": ["US"]}
        assert second.query == {"filter[number]": ["18005550123"]}
        assert third.query == {"filter[number]": ["18005550123"]}

    def test_wire_encoding(self, client):
        seen = []

        def script(conn, request):
            seen.append(request.split(b"\r\n", 1)[0])
            body = fixture_bytes("prices/voice_in/lookup/200.json")
            conn.sendall(http_response(200, body, [("Content-Type", "application/vnd.api+json")]))

        server = RawServer(script)
        try:
            client._voice_in_prices_url = server.url
            client.voice_in_prices().lookup({"src_country_iso": "US", "number": "1 2+3"})
        finally:
            server.close()
        assert seen == [b"GET /v3/lookup/prices?filter%5Bnumber%5D=1+2%2B3&filter%5Bsrc_country_iso%5D=US HTTP/1.1"]

    def test_enum_values_are_sent_as_their_value(self, client):
        class Iso(str, enum.Enum):
            US = "US"

        class Number(enum.IntEnum):
            TOLL_FREE = 18005550123

        params = client.voice_in_prices()._lookup_params({"src_country_iso": Iso.US, "number": Number.TOLL_FREE})
        assert sorted(params) == [("filter[number]", "18005550123"), ("filter[src_country_iso]", "US")]


class TestRows:
    def test_voice_in(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", jsonapi(fixture_bytes("prices/voice_in/lookup/200.json")))
        result = client.voice_in_prices().lookup({"number": "18005550123"})

        assert isinstance(result, PriceLookup)
        assert result.total_records == 2
        assert len(result) == 2
        first, second = result
        assert first == result[0] == result.rows[0]
        assert first == VoiceInPrice(
            id="df73d9e4-46ce-4af0-817e-f090dc8144f1", destination="1800", country="United States",
            src_country_name=None, source_type="cellular", rate=Decimal("0.025"),
            connection_fee=Decimal("0.0"), initial_interval=60, next_interval=60, reject_calls=False)
        assert str(first.rate) == "0.025"
        assert str(first.connection_fee) == "0.0"
        assert second.rate is None
        assert second.connection_fee is None
        assert second.reject_calls is True

    def test_voice_out(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", jsonapi(fixture_bytes("prices/voice_out/lookup/200.json")))
        first, second = client.voice_out_prices().lookup({"number": "4930123456"})

        assert isinstance(first, VoiceOutPrice)
        assert first.category is VoiceOutPriceCategory.INTERNATIONAL
        assert str(first.rate) == "0.0045"
        assert str(first.next_rate) == "0.005"
        assert first.next_initial_increment == 30
        assert first.effective_at == datetime(2026, 11, 1, tzinfo=timezone.utc)
        assert first.effective_at.tzinfo is not None
        assert first.comment == "Increase and Billing increment change"
        assert second.category is VoiceOutPriceCategory.ORIGIN_BASED
        assert second.next_rate is None
        assert second.next_recurring_increment is None
        assert second.effective_at is None
        assert second.comment is None

    def test_sms_out(self, stub, client):
        stub.on("GET", "/v3/sms_out/p2p/lookup/prices", jsonapi(fixture_bytes("prices/sms_out/lookup/200.json")))
        first, second = client.sms_out_p2p_prices().lookup({"dst_country_iso": "DE"})

        assert isinstance(first, SmsOutPrice)
        assert first.source_prefix is None
        assert first.destination_prefix == "49151"
        assert (first.mcc, first.mnc, first.mnc_name) == (262, 1, "Telekom Deutschland")
        assert str(first.price) == "0.075000"
        assert second.reject_sms is True
        assert second.price is None

    def test_sms_in(self, stub, client):
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(fixture_bytes("prices/sms_in/lookup/200.json")))
        (row,) = client.sms_in_prices().lookup({"dst_number": "12125550123", "dst_country_iso": "US"})

        assert row == SmsInPrice(
            id="e93f925e-25ee-4060-bd50-a790b4945d3f", source_prefix=None, source_number_length_min=1,
            source_number_length_max=15, destination_prefix="1", destination_number_length_min=11,
            destination_number_length_max=11, country="United States", price=Decimal("0.005000"))
        assert str(row.price) == "0.005000"
        query = stub.hits("GET", "/v3/sms_in/lookup/prices")[0].query
        assert query == {"filter[dst_country_iso]": ["US"], "filter[dst_number]": ["12125550123"]}

    def test_rows_are_frozen(self, stub, client):
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(fixture_bytes("prices/sms_in/lookup/200.json")))
        result = client.sms_in_prices().lookup({"dst_number": "12125550123"})
        with pytest.raises(AttributeError):
            result[0].price = Decimal("0")
        with pytest.raises(AttributeError):
            result.total_records = 5

    def test_unknown_category_stays_a_string(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", jsonapi(one_row({"category": "Premium", "rate": "1"})))
        (row,) = client.voice_out_prices().lookup({"number": "4930123456"})
        assert row.category == "Premium"
        assert not isinstance(row.category, VoiceOutPriceCategory)

    @pytest.mark.parametrize("value, expected", [
        ("2026-11-01T00:00:00Z", datetime(2026, 11, 1, tzinfo=timezone.utc)),
        ("2026-11-01T00:00:00.12+00:00", datetime(2026, 11, 1, 0, 0, 0, 120000, tzinfo=timezone.utc)),
        ("2026-11-01T02:00:00.1234567+02:00", datetime(2026, 11, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)),
    ])
    def test_effective_at_formats(self, stub, client, value, expected):
        stub.on("GET", "/v3/lookup/prices", jsonapi(one_row({"effective_at": value})))
        (row,) = client.voice_out_prices().lookup({"number": "4930123456"})
        assert row.effective_at == expected

    def test_json_numbers_are_exact(self, stub, client):
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(b'{"data":[{"id":"r","attributes":{"price":0.10}}]}'))
        (row,) = client.sms_in_prices().lookup({"dst_number": "12125550123"})
        assert str(row.price) == "0.10"

    @pytest.mark.parametrize("meta, expected", [(None, 0), ({}, 0), ({"total_records": None}, 0),
                                                ({"total_records": 7}, 7)])
    def test_total_records(self, stub, client, meta, expected):
        document = one_row({"price": "1"})
        if meta is not None:
            document["meta"] = meta
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(document))
        assert client.sms_in_prices().lookup({"dst_number": "12125550123"}).total_records == expected

    @pytest.mark.parametrize("body, reason", [
        ({"data": []}, "the answer holds no prices"),
        ({"data": None}, "the answer holds no prices"),
        ({}, "the answer holds no prices"),
        ([], "the answer is not a JSON:API document"),
        ({"data": {"id": "r"}}, "data is not an array"),
        ({"data": ["r"]}, "data[0] is not a resource object"),
        ({"data": [{"attributes": {}}]}, "data[0] has no id"),
        ({"data": [{"id": 5}]}, "data[0] has no id"),
        ({"data": [{"id": "r", "attributes": []}]}, "data[0].attributes is not an object"),
        (one_row({"price": "NaN"}), "data[0].attributes.price is not a decimal number"),
        (one_row({"price": "Infinity"}), "data[0].attributes.price is not a decimal number"),
        (one_row({"price": " 1.5"}), "data[0].attributes.price is not a decimal number"),
        (one_row({"price": True}), "data[0].attributes.price is not a decimal number"),
        (one_row({"source_number_length_min": True}), "data[0].attributes.source_number_length_min is not an integer"),
        (one_row({"source_number_length_min": "1"}), "data[0].attributes.source_number_length_min is not an integer"),
        (one_row({"country": 5}), "data[0].attributes.country is not a string"),
        (one_row({"price": "1"}, meta={"total_records": True}), "meta.total_records is not a non-negative integer"),
        (one_row({"price": "1"}, meta={"total_records": "2"}), "meta.total_records is not a non-negative integer"),
        (one_row({"price": "1"}, meta=[]), "meta is not an object"),
    ])
    def test_unparseable_answers(self, stub, client, body, reason):
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(body))
        e = capture(lambda: client.sms_in_prices().lookup({"dst_number": "12125550123"}))
        assert type(e) is DidwwClientError
        assert str(e) == "Failed to parse price lookup: " + reason

    @pytest.mark.parametrize("value", ["2026-11-01", "2026-11-01T00:00:00", "2026-13-01T00:00:00Z", 5,
                                       "2026-11-01T00:00:00+24:00", "2026-11-01T00:00:00+05:60"])
    def test_bad_effective_at(self, stub, client, value):
        stub.on("GET", "/v3/lookup/prices", jsonapi(one_row({"effective_at": value})))
        e = capture(lambda: client.voice_out_prices().lookup({"number": "4930123456"}))
        assert type(e) is DidwwClientError
        assert "effective_at" in str(e)

    @pytest.mark.parametrize("body", [b"", b"{", b"<html>", b'{"data": NaN}', b"\xff\xfe",
                                      json.dumps(one_row({"price": "1"})).replace('"1"', "1e99999999999999999999")])
    def test_invalid_json(self, stub, client, body):
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(body))
        e = capture(lambda: client.sms_in_prices().lookup({"dst_number": "12125550123"}))
        assert type(e) is DidwwClientError
        assert str(e).startswith("Failed to parse price lookup: ")

    def test_gzip_answer_is_decoded(self, stub, client):
        import gzip

        body = gzip.compress(fixture_bytes("prices/sms_in/lookup/200.json"))
        stub.on("GET", "/v3/sms_in/lookup/prices", jsonapi(body, headers={"Content-Encoding": "gzip"}))
        assert len(client.sms_in_prices().lookup({"dst_number": "12125550123"})) == 1


class TestErrors:
    @pytest.mark.parametrize("status, fixture, kind, code", [
        (400, "filter_not_allowed", PricesErrorKind.BAD_REQUEST, "102"),
        (404, "price_not_found", PricesErrorKind.PRICE_NOT_FOUND, "price_not_found"),
        (404, "price_plan_not_assigned", PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED, "price_plan_not_assigned"),
        (404, "filter_not_allowed", PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED, "102"),
        (403, "filter_not_allowed", PricesErrorKind.ACCESS_DENIED, "102"),
        (406, "filter_not_allowed", PricesErrorKind.NOT_ACCEPTABLE, "102"),
        (429, "filter_not_allowed", PricesErrorKind.TOO_MANY_REQUESTS, "102"),
        (503, "serving_failure", PricesErrorKind.SERVICE_UNAVAILABLE, "serving_failure"),
        (500, "serving_failure", PricesErrorKind.UNEXPECTED_STATUS, "serving_failure"),
    ])
    def test_status_mapping(self, stub, client, status, fixture, kind, code):
        stub.on("GET", "/v3/lookup/prices",
                jsonapi(fixture_bytes(f"prices/errors/{fixture}.json"), status, {"Retry-After": "7"}))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert type(e) is DidwwPricesError
        assert e.kind is kind
        assert e.status_code == status
        assert e.code == code
        assert e.retry_after == 7
        expected = fixture_json(f"prices/errors/{fixture}.json")["errors"]
        assert e.errors == expected
        assert str(e) == "Prices service: " + expected[0]["detail"]
        assert len(stub.hits("GET", "/v3/lookup/prices")) == 1

    def test_404_without_body(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", Reply(404, b""))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED
        assert e.code == "price_plan_not_assigned"
        assert e.errors == []
        assert e.retry_after is None
        assert str(e) == "Prices service responded with status 404"

    @pytest.mark.parametrize("status", [202, 204, 301, 302, 304, 307])
    def test_other_statuses_are_unexpected(self, stub, client, status):
        stub.on("GET", "/v3/lookup/prices", Reply(status, b"", {"Location": stub.url + "/elsewhere"}))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.UNEXPECTED_STATUS
        assert e.status_code == status
        assert stub.hits(path="/elsewhere") == []

    def test_redirect_with_unparsable_location(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", Reply(302, b"", {"Location": "http://[::1/x"}))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.UNEXPECTED_STATUS
        assert e.status_code == 302

    def test_401_re_mints_once_then_not_authorized(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", jsonapi({"errors": [{"title": "Unauthorized"}]}, 401))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.NOT_AUTHORIZED
        assert str(e) == "Prices service: Unauthorized"
        assert len(stub.hits("GET", "/v3/lookup/prices")) == 2
        assert len(mints(stub)) == 2

    def test_401_then_200(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", jsonapi({"errors": []}, 401),
                jsonapi(fixture_bytes("prices/voice_in/lookup/200.json")))
        assert len(client.voice_in_prices().lookup({"number": "18005550123"})) == 2

    def test_lookup_503_is_not_retried(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", Reply(503, b"", {"Retry-After": "1"}))
        service = client.voice_in_prices()
        service._sleep = lambda seconds: pytest.fail("slept")
        e = capture(lambda: service.lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.SERVICE_UNAVAILABLE
        assert e.retry_after == 1
        assert len(stub.hits("GET", "/v3/lookup/prices")) == 1

    def test_retry_after_date_is_ignored(self, stub, client):
        stub.on("GET", "/v3/lookup/prices", Reply(429, b"", {"Retry-After": "Thu, 01 Oct 2026 08:05:03 GMT"}))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.TOO_MANY_REQUESTS
        assert e.retry_after is None

    def test_error_body_is_limited_in_size(self, stub, client):
        body = json.dumps({"errors": [{"code": "price_not_found"}], "pad": "x" * (2 << 20)})
        stub.on("GET", "/v3/lookup/prices", jsonapi(body, 404))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED
        assert e.code == "price_plan_not_assigned"

    def test_error_body_is_read_within_a_deadline(self, client):
        def trickle(conn, request):
            conn.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 1000\r\n\r\n"
                         b'{"errors":[{"code":"price_not_found"}]')
            for _ in range(100):
                conn.sendall(b" ")
                time.sleep(0.05)

        server = RawServer(trickle)
        try:
            client._voice_in_prices_url = server.url
            service = client.voice_in_prices()
            service._error_body_timeout = 0.3
            started = time.monotonic()
            e = capture(lambda: service.lookup({"number": "18005550123"}))
            elapsed = time.monotonic() - started
        finally:
            server.close()
        assert e.kind is PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED
        assert elapsed < 2.5

    def test_error_body_with_a_number_out_of_range(self, stub, client):
        body = b'{"errors":[{"code":"price_not_found","meta":{"n":1e99999999999999999999}}]}'
        stub.on("GET", "/v3/lookup/prices", jsonapi(body, 404))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED
        assert e.code == "price_plan_not_assigned"

    def test_gzip_error_body_is_decoded(self, stub, client):
        import gzip

        body = gzip.compress(fixture_bytes("prices/errors/price_not_found.json"))
        stub.on("GET", "/v3/lookup/prices", jsonapi(body, 404, {"Content-Encoding": "gzip"}))
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert e.kind is PricesErrorKind.PRICE_NOT_FOUND

    def test_connection_refused(self, client):
        server = RawServer(lambda conn, request: None)
        url = server.url
        server.close()
        client._voice_in_prices_url = url
        e = capture(lambda: client.voice_in_prices().lookup({"number": "18005550123"}))
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert e.status_code is None
        assert str(e) == "Prices service request failed: ConnectionError"
        assert e.__cause__ is not None
        assert getattr(e.__cause__, "request", None) is None

    def test_cut_body(self, client):
        body = fixture_bytes("prices/sms_in/lookup/200.json")

        def script(conn, request):
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
                         + body[:20])

        server = RawServer(script)
        try:
            client._sms_prices_url = server.url
            e = capture(lambda: client.sms_in_prices().lookup({"dst_number": "12125550123"}))
        finally:
            server.close()
        assert type(e) is DidwwPricesError
        assert e.kind is PricesErrorKind.CONNECTION_ERROR
        assert e.status_code == 200
        assert str(e).startswith("Prices service: incomplete body")

    def test_auth_errors_pass_through(self, stub, make_client):
        stub.on("POST", "/token", Reply(401, {"error": "invalid_client"}))
        e = capture(lambda: make_client().voice_in_prices().lookup({"number": "18005550123"}))
        assert type(e) is DidwwAuthError
        assert stub.hits("GET") == []


class TestPricesError:
    def test_is_a_didww_error_and_not_an_os_error(self):
        e = DidwwPricesError(kind=PricesErrorKind.CONNECTION_ERROR)
        assert isinstance(e, DidwwError)
        assert not isinstance(e, OSError)
        assert str(e) == "Prices service request failed"

    def test_copy_and_pickle(self):
        e = DidwwPricesError(kind=PricesErrorKind.PRICE_NOT_FOUND, status_code=404, code="price_not_found",
                             errors=[{"title": "Price not found"}], retry_after=3)
        for clone in (copy.copy(e), pickle.loads(pickle.dumps(e))):
            assert str(clone) == "Prices service: Price not found"
            assert clone.kind is PricesErrorKind.PRICE_NOT_FOUND
            assert (clone.status_code, clone.code, clone.retry_after) == (404, "price_not_found", 3)
            assert clone.errors == [{"title": "Price not found"}]

    def test_kind_values(self):
        assert [k.value for k in PricesErrorKind] == [
            "bad_request", "not_authorized", "access_denied", "price_plan_not_assigned", "price_not_found",
            "not_acceptable", "too_many_requests", "service_unavailable", "unexpected_status", "connection_error",
        ]
