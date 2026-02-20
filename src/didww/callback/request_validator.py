import hashlib
import hmac
from urllib.parse import urlparse


class RequestValidator:
    def __init__(self, api_key):
        self.api_key = api_key

    def validate(self, url, payload, signature):
        if not signature:
            return False
        expected = self._compute_signature(url, payload)
        return hmac.compare_digest(expected, signature)

    def _compute_signature(self, url, payload):
        normalized_url = self._normalize_url(url)
        sorted_keys = sorted(payload.keys())
        data_str = normalized_url
        for key in sorted_keys:
            data_str += key + payload[key]
        return hmac.new(
            self.api_key.encode("utf-8"),
            data_str.encode("utf-8"),
            hashlib.sha1,
        ).hexdigest()

    def _normalize_url(self, url):
        parsed = urlparse(url)
        scheme = parsed.scheme
        host = parsed.hostname or ""
        port = parsed.port
        if port is None:
            port = 443 if scheme == "https" else 80
        path = parsed.path or ""
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""

        userinfo = ""
        if parsed.username:
            userinfo = parsed.username
            if parsed.password:
                userinfo += f":{parsed.password}"
            userinfo += "@"

        return f"{scheme}://{userinfo}{host}:{port}{path}{query}{fragment}"
