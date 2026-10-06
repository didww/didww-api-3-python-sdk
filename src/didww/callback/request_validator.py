import hashlib
import hmac
import warnings
from urllib.parse import urlparse


class RequestValidator:
    """Validates the X-DIDWW-Signature header of DIDWW callbacks.

    :param callback_secret: the callback secret enabled in the DIDWW User Panel.
    :param api_key: deprecated alias of ``callback_secret``, kept for keyword-argument callers.
    """

    def __init__(self, callback_secret=None, *, api_key=None):
        if callback_secret is not None and api_key is not None:
            raise TypeError("Pass either callback_secret or the deprecated api_key, not both.")
        if api_key is not None:
            warnings.warn(
                "The api_key argument is deprecated, pass callback_secret instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if callback_secret is None:
            callback_secret = api_key
        if callback_secret is None:
            raise TypeError("RequestValidator() missing required argument: 'callback_secret'")
        self.callback_secret = callback_secret

    @property
    def api_key(self):
        """Deprecated alias of :attr:`callback_secret`."""
        warnings.warn(
            "The api_key attribute is deprecated, use callback_secret instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.callback_secret

    @api_key.setter
    def api_key(self, value):
        warnings.warn(
            "The api_key attribute is deprecated, use callback_secret instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.callback_secret = value

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
            self.callback_secret.encode("utf-8"),
            data_str.encode("utf-8"),
            hashlib.sha1,
        ).hexdigest()

    def _normalize_url(self, url):
        parsed = urlparse(url)
        scheme = parsed.scheme
        hostname = parsed.hostname or ""
        # Wrap IPv6 addresses in brackets
        if ":" in hostname:
            host = f"[{hostname}]"
        else:
            host = hostname
        port = parsed.port
        if port is None:
            port = 443 if scheme == "https" else 80
        path = parsed.path
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""

        userinfo = ""
        if parsed.username:
            userinfo = parsed.username
            if parsed.password:
                userinfo += f":{parsed.password}"
            userinfo += "@"

        return f"{scheme}://{userinfo}{host}:{port}{path}{query}{fragment}"
