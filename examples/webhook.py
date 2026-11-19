"""
Webhook: validates the X-DIDWW-Signature of a callback with RequestValidator.

DIDWW signs every callback with the callback secret enabled in the User Panel
(APIs -> DIDWW API 3 -> Callback Secrets): HMAC-SHA1 with the secret as the
key over the callback URL followed by each payload key and value, the keys in
sorted order, sent as a hex digest. The URL is signed in full form: scheme,
host, port (80 or 443 when the URL has none), path and query.

This example builds a sample callback, signs it that way and checks it: the
signed callback is valid, the same signature over a changed payload is not.
It sends no request, so it needs no API key.

Usage: python examples/webhook.py
"""
import hashlib
import hmac
from urllib.parse import urlsplit

from didww.callback.request_validator import RequestValidator

CALLBACK_SECRET = "your-callback-secret"


def sign(secret, url, payload):
    """Signs a callback the way DIDWW does, for a URL without user info or fragment."""
    parts = urlsplit(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    query = f"?{parts.query}" if parts.query else ""
    data = f"{parts.scheme}://{parts.hostname}:{port}{parts.path}{query}"
    for key in sorted(payload):
        data += key + payload[key]
    return hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).hexdigest()


# A callback as your endpoint receives it: the full request URL, the payload
# fields (all strings) and the X-DIDWW-Signature header.
callback_url = "https://example.com/callbacks/didww?source=orders"
payload = {
    "id": "1dd7a68b-e235-402b-8912-fe73ee14243a",
    "type": "orders",
    "status": "completed",
}
signature = sign(CALLBACK_SECRET, callback_url, payload)
print(f"X-DIDWW-Signature: {signature}")

validator = RequestValidator(CALLBACK_SECRET)

valid = validator.validate(url=callback_url, payload=payload, signature=signature)
print(f"Signed callback   -> valid: {str(valid).lower()}")  # true

tampered = dict(payload, status="canceled")
valid = validator.validate(url=callback_url, payload=tampered, signature=signature)
print(f"Tampered payload  -> valid: {str(valid).lower()}")  # false
