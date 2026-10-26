import re
from enum import Enum
from urllib.parse import urlsplit

DEFAULT_API_VERSION = "2026-10-22"

_AUDIENCE_API = "api.didww.com"
_AUDIENCE_VOICE_IN = "api-vin.didww.com"
_AUDIENCE_VOICE_OUT = "api-vout.didww.com"
_AUDIENCE_SMS = "api-sms.didww.com"


class Environment(Enum):
    """A DIDWW environment. The value is the JSON:API base URL."""

    SANDBOX = "https://sandbox-api.didww.com/v3"
    PRODUCTION = "https://api.didww.com/v3"

    @property
    def auth_url(self):
        """The token service base URL."""
        return _ENDPOINTS[self.name][0]

    @property
    def voice_in_prices_url(self):
        """The Voice IN prices service base URL."""
        return _ENDPOINTS[self.name][1]

    @property
    def voice_out_prices_url(self):
        """The Voice OUT prices service base URL."""
        return _ENDPOINTS[self.name][2]

    @property
    def sms_prices_url(self):
        """The SMS prices service base URL."""
        return _ENDPOINTS[self.name][3]


_ENDPOINTS = {
    "SANDBOX": (
        "https://auth-sandbox.didww.com",
        "https://api-vin-sandbox.didww.com/v3",
        "https://api-vout-sandbox.didww.com/v3",
        "https://api-sms-sandbox.didww.com/v3",
    ),
    "PRODUCTION": (
        "https://auth.didww.com",
        "https://api-vin.didww.com/v3",
        "https://api-vout.didww.com/v3",
        "https://api-sms.didww.com/v3",
    ),
}


class Scope(str, Enum):
    """The scope requested for access tokens."""

    READ = "read"
    FULL = "full"


_API_VERSION_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_API_KEY_RE = re.compile(r"[\x21-\x7e]+")


def _is_service_url(url):
    if not isinstance(url, str) or "?" in url or "#" in url or "\\" in url:
        return False
    if any(c <= " " or c == "\x7f" for c in url):
        return False
    try:
        parts = urlsplit(url)
        parts.port
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.hostname) and "@" not in parts.netloc
