from didww.callback.request_validator import RequestValidator


class TestRequestValidator:
    def test_sandbox(self):
        validator = RequestValidator("SOMEAPIKEY")
        url = "http://example.com/callback.php?id=7ae7c48f-d48a-499f-9dc1-c9217014b457&reject_reason=&status=approved&type=address_verifications"
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
        assert validator.validate("http://example.com/callbacks", payload, "fe99e416c3547f2f59002403ec856ea386d05b2f") is True

    def test_valid_request_with_query_and_fragment(self):
        validator = RequestValidator("OTHERAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks?foo=bar#baz", payload, "32754ba93ac1207e540c0cf90371e7786b3b1cde") is True

    def test_empty_signature(self):
        validator = RequestValidator("SOMEAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks", payload, "") is False

    def test_invalid_signature(self):
        validator = RequestValidator("SOMEAPIKEY")
        payload = {
            "status": "completed",
            "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
            "type": "orders",
        }
        assert validator.validate("http://example.com/callbacks", payload, "fbdb1d1b18aa6c08324b7d64b71fb76370690e1d") is False
