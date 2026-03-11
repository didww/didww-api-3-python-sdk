import pytest

from didww.callback.request_validator import RequestValidator

URL_NORMALIZATION_VECTORS = [
    ("http://foo.com/bar", "4d1ce2be656d20d064183bec2ab98a2ff3981f73"),  # NOSONAR
    ("http://foo.com:80/bar", "4d1ce2be656d20d064183bec2ab98a2ff3981f73"),  # NOSONAR
    ("http://foo.com:443/bar", "904eaa65c0759afac0e4d8912de424e2dfb96ea1"),  # NOSONAR
    ("http://foo.com:8182/bar", "eb8fcfb3d7ed4b4c2265d73cf93c31ba614384d1"),  # NOSONAR
    ("foo.com/bar", "4d1ce2be656d20d064183bec2ab98a2ff3981f73"),
    ("http://foo.com/bar?baz=boo", "78b00717a86ce9df06abf45ff818aa94537e1729"),  # NOSONAR
    ("http://user:pass@foo.com/bar", "88615a11a78c021c1da2e1e0bfb8cc165170afc5"),  # NOSONAR
    ("http://foo.com/bar#test", "b1c4391fcdab7c0521bb5b9eb4f41f08529b8418"),  # NOSONAR
    ("https://foo.com/bar", "f26a771c302319a7094accbe2989bad67fff2928"),
    ("https://foo.com:443/bar", "f26a771c302319a7094accbe2989bad67fff2928"),
    ("https://foo.com:80/bar", "bd45af5253b72f6383c6af7dc75250f12b73a4e1"),
    ("https://foo.com:8384/bar", "9c9fec4b7ebd6e1c461cb8e4ffe4f2987a19a5d3"),
    ("https://foo.com/bar?qwe=asd", "4a0e98ddf286acadd1d5be1b0ed85a4e541c3137"),
    ("https://qwe:asd@foo.com/bar", "7a8cd4a6c349910dfecaf9807e56a63787250bbd"),
    ("https://foo.com/bar#baz", "5024919770ea5ca2e3ccc07cb940323d79819508"),
]


class TestRequestValidator:
    def test_sandbox(self):
        validator = RequestValidator("SOMEAPIKEY")
        url = "http://example.com/callback.php?id=7ae7c48f-d48a-499f-9dc1-c9217014b457&reject_reason=&status=approved&type=address_verifications"  # NOSONAR
        payload = {
            "status": "approved",
            "id": "7ae7c48f-d48a-499f-9dc1-c9217014b457",
            "type": "address_verifications",
            "reject_reason": "",
        }
        assert validator.validate(url, payload, "18050028b6b22d0ed516706fba1c1af8d6a8f9d5") is True

    def test_valid_request(self):
        validator = RequestValidator("SOMEAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks", payload, "fe99e416c3547f2f59002403ec856ea386d05b2f") is True  # NOSONAR

    def test_valid_request_with_query_and_fragment(self):
        validator = RequestValidator("OTHERAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks?foo=bar#baz", payload, "32754ba93ac1207e540c0cf90371e7786b3b1cde") is True  # NOSONAR

    def test_empty_signature(self):
        validator = RequestValidator("SOMEAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks", payload, "") is False  # NOSONAR

    def test_invalid_signature(self):
        validator = RequestValidator("SOMEAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks", payload, "fbdb1d1b18aa6c08324b7d64b71fb76370690e1d") is False  # NOSONAR

    @pytest.mark.parametrize("url, expected_signature", URL_NORMALIZATION_VECTORS)
    def test_url_normalization_vectors(self, url, expected_signature):
        validator = RequestValidator("SOMEAPIKEY")
        payload = {
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "status": "completed",
            "type": "orders",
        }
        assert validator.validate(url, payload, expected_signature) is True
