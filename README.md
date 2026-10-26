Python client for DIDWW API v3.

![Tests](https://github.com/didww/didww-api-3-python-sdk/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://didww.github.io/didww-api-3-python-sdk/badge.json)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

## About DIDWW API v3

The DIDWW API provides a simple yet powerful interface that allows you to fully integrate your own applications with DIDWW services. An extensive set of actions may be performed using this API, such as ordering and configuring phone numbers, setting capacity, creating SIP trunks and retrieving CDRs and other operational data.

The DIDWW API v3 is a fully compliant implementation of the [JSON API specification](http://jsonapi.org/format/).

This SDK uses [jsonapi-requests](https://github.com/socialwifi/jsonapi-requests) for JSON:API serialization and deserialization.

Read more https://doc.didww.com/api

## API Version

This SDK targets DIDWW API version `2026-10-22` (`DidwwClient.DEFAULT_API_VERSION`). The version is not sent as a header: it is requested in the `api_version` of every access token the SDK mints (see [Authentication](#authentication)).

| Package Version | Branch | DIDWW API Version |
|-----------------|--------|-------------------|
| **4.x** | [`main`](https://github.com/didww/didww-api-3-python-sdk) | [`2026-10-22`](https://doc.didww.com/api3/2026-10-22/index.html) |
| **3.x** | [`release-3`](https://github.com/didww/didww-api-3-python-sdk/tree/release-3) | [`2026-04-16`](https://doc.didww.com/api3/2026-04-16/index.html) |
| **2.x** | [`2022-05-10`](https://github.com/didww/didww-api-3-python-sdk/tree/2022-05-10) | [`2022-05-10`](https://doc.didww.com/api3/2022-05-10/index.html) |

`DidwwClient(..., api_version="YYYY-MM-DD")` requests a later version. The constructor raises a `DidwwClientError` for a value that is not a `YYYY-MM-DD` date and for a version earlier than `2026-10-22`. The resources of earlier API versions are not in this release: use 3.x from the [`release-3`](https://github.com/didww/didww-api-3-python-sdk/tree/release-3) branch for API `2026-04-16` (see [Migrating from 3.x](#migrating-from-3x)).

## Requirements

- Python 3.9+

The SDK depends on [requests](https://requests.readthedocs.io/), [urllib3](https://urllib3.readthedocs.io/) 1.26 or later, [jsonapi-requests](https://github.com/socialwifi/jsonapi-requests) and [cryptography](https://cryptography.io/). urllib3 already came with requests; 4.0.0 only names it, since the SDK uses it directly. Logging, exact numbers and gzip handling use the standard library (see [Logging](#logging)).

## Installation

```bash
pip install didww
```

To stay on this major version:

```bash
pip install "didww>=4,<5"
```

For API `2026-04-16`, stay on 3.x:

```bash
pip install "didww>=3,<4"
```

Or install from source:

```bash
pip install -e .
```

## Usage

```python
from didww.client import DidwwClient
from didww.configuration import Environment
from didww.query_params import QueryParams

client = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.SANDBOX)

# Check balance
balance = client.balance().find().data
print(f"Balance: {balance.total_balance}")

# List DID groups with stock keeping units
params = QueryParams().include("stock_keeping_units").filter("area_name", "Acapulco")
did_groups = client.did_groups().list(params).data
```

One `DidwwClient` may be shared by threads: build one per API key and environment and reuse it. Every call is synchronous. `client.close()`, or a `with DidwwClient(...) as client:` block, releases its connection pools.

For more examples visit [examples](examples/).

For details on obtaining your API key please visit https://doc.didww.com/api3/configuration.html

## Examples

- Source code: [examples/](examples/)
- How to run: [examples/README.md](examples/README.md)

## Configuration

```python
import logging

from didww.client import DidwwClient
from didww.configuration import Environment, Scope

# Production
client = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.PRODUCTION)

# Sandbox, read-only tokens, your own logger, a shorter connect timeout
sandbox = DidwwClient(
    api_key="YOUR_API_KEY",
    environment=Environment.SANDBOX,
    scope=Scope.READ,
    logger=logging.getLogger("myapp.didww"),
    connect_timeout=5,
)
```

`api_key`, `environment`, `base_url` and `session` may be passed by position, as in 3.x; every other argument is keyword-only.

| Argument | Default | Description |
|----------|---------|-------------|
| `api_key` | required | Your API key. |
| `environment` | `Environment.SANDBOX` | `Environment.PRODUCTION` or `Environment.SANDBOX`. It selects the API, token service and price hosts. See [Environments](#environments). |
| `base_url` | API URL of the environment | JSON:API base URL only, including `/v3`. |
| `session` | none | A `requests.Session` whose proxy and TLS settings the SDK copies. See [HTTP session](#http-session-proxy-tls-timeouts). |
| `api_version` | `DidwwClient.DEFAULT_API_VERSION` (`"2026-10-22"`) | API version requested in every token. See [API Version](#api-version). |
| `scope` | `None` | `Scope.READ` or `Scope.FULL` (or `"read"`, `"full"`). With `None` no scope is requested and the token service grants `full`. See [Scope](#scope). |
| `token_store` | one `MemoryTokenStore` shared by every client of the process built without its own | Cache for access tokens. See [Token cache](#token-cache). |
| `logger` | `logging.getLogger("didww")` | A `logging.Logger` or `logging.LoggerAdapter` for the token warnings and debug events. See [Logging](#logging). |
| `connect_timeout` | `10` | Seconds allowed to open a connection: the TCP connection, the tunnel through an HTTP proxy and the TLS handshake. `None` for no limit. |
| `read_timeout` | `60` | Seconds allowed for each read: the wait for the response headers and between two reads of a body. `None` for no limit. There is no limit on a whole call. |
| `auth_url` | Token service of the environment | Token service base URL. |
| `voice_in_prices_url`, `voice_out_prices_url`, `sms_prices_url` | Price hosts of the environment | Price service base URLs, with or without the `/v3` suffix. |

The API key is sent only to the token service. An overridden URL, for example to send the traffic through a gateway of yours, does not change the token audiences (see [Authentication](#authentication)). The values in use can be read back as `client.base_url`, `client.api_version`, `client.scope`, `client.auth_url`, `client.voice_in_prices_url`, `client.voice_out_prices_url`, `client.sms_prices_url` and `client.token_store`.

The constructor raises a `DidwwClientError` (see [Error Handling](#error-handling)), before any request, for:

- an empty API key, or one with a character outside printable ASCII or a space (a control character, such as a trailing newline or a tab, or a non-ASCII character, such as a non-breaking space);
- an `environment` that is not an `Environment` member;
- an API version that is not a `YYYY-MM-DD` date, or that is earlier than `2026-10-22`;
- a `scope` other than `Scope.READ`, `Scope.FULL`, `"read"`, `"full"` or `None`;
- a timeout that is not a positive number of seconds up to 1,000,000, or `None`;
- a `token_store` without callable `get`, `set` and `delete`, or a `logger` without a callable `log`, or either one passed as a class instead of an instance;
- a base, token service or prices URL that is not an http or https URL with a host, contains a space, a control character or a backslash, has a query or fragment, or has user info (`user:password@`).

`repr(client)` does not show the API key.

### Environments

| Environment | API | Token service | Voice IN prices | Voice OUT prices | SMS prices |
|-------------|-----|---------------|-----------------|------------------|------------|
| `Environment.PRODUCTION` | `https://api.didww.com/v3` | `https://auth.didww.com` | `https://api-vin.didww.com/v3` | `https://api-vout.didww.com/v3` | `https://api-sms.didww.com/v3` |
| `Environment.SANDBOX` | `https://sandbox-api.didww.com/v3` | `https://auth-sandbox.didww.com` | `https://api-vin-sandbox.didww.com/v3` | `https://api-vout-sandbox.didww.com/v3` | `https://api-sms-sandbox.didww.com/v3` |

A firewall that limits outgoing traffic must allow the token service, and the price hosts when you use [Prices](#prices).

### HTTP session (proxy, TLS, timeouts)

The SDK sends its requests through `requests` sessions of its own. `requests` has no default timeout, so the SDK passes `timeout=(connect_timeout, read_timeout)` on every call: connections are opened within 10 s, and each read, of the response headers or of the next part of a body, may wait up to 60 s. The read timeout applies to each read, not to the whole call, so a large price or export file is not cut off while its data keeps arriving.

You can pass your own `requests.Session`, for example for a proxy or a custom CA bundle:

```python
import requests

from didww.client import DidwwClient
from didww.configuration import Environment

session = requests.Session()
session.proxies = {
    "https": "http://proxy.example.com:8080",
}
session.verify = "/etc/ssl/certs/my-ca-bundle.pem"

client = DidwwClient(
    api_key="YOUR_API_KEY",
    environment=Environment.PRODUCTION,
    session=session,
)
```

The SDK copies the settings below from your session into its own and never changes or uses your session. The copies are used for every call: the token service, the JSON:API, export download, encrypted file upload and prices.

- **Copied:** `proxies`, `verify`, `cert`, `trust_env` and, for each mounted adapter prefix, the pool sizes and blocking flag of the adapter. The adapter's `max_retries` is kept for the JSON:API, export download and upload calls; token service and prices requests are never resent by urllib3.
- **Not copied:** `auth`, `headers`, `cookies`, `hooks`, `params`, `max_redirects`, and the adapters themselves: the SDK mounts plain `requests.adapters.HTTPAdapter` objects, so a custom adapter subclass and its own settings (such as an SSL context) are not used.

On every call the SDK:

- follows no redirects (`allow_redirects=False`), so that neither a token nor the API key is sent to another URL; a 3xx answer is an error (see [Error Handling](#error-handling));
- stores and sends no cookies (its sessions use a cookie policy that refuses every cookie), so no state is carried between calls or API keys;
- sets the bearer token through a per-request `requests` auth object. `requests` would otherwise replace an `Authorization` header with the Basic credentials of `~/.netrc` (or `$NETRC`) or of `session.auth`: neither is used for SDK calls. With `trust_env` left on, as in `requests`, the proxy (`HTTPS_PROXY`, `NO_PROXY`) and CA bundle (`REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`) environment variables still apply.

Price files, price lookups and export files are requested with `Accept-Encoding: identity`, and the files are written exactly as served (gzipped). JSON:API and upload calls send `Accept-Encoding: gzip, deflate`, whatever `requests` and urllib3 would offer, and `requests` decodes the content coding of their answers. Each attempt of a token request connects within 10 s, waits up to 10 s for each read of the answer, and must receive the body within 10 s of sending, independently of your timeouts. An error answer is read up to 1 MiB, within the read timeout. With `read_timeout=None` the 60 s limit is checked between reads: a body that stops arriving is waited for like any other read.

Your own debugging output can show secrets: `http.client.HTTPConnection.debuglevel = 1` prints the request headers, `Api-Key` and `Authorization` included. urllib3's `DEBUG` logging prints only the method, URL and status.

## Authentication

Every request carries `Authorization: Bearer <token>`. The SDK mints the tokens itself with `POST /token` on the token service, sending your API key in the `Api-Key` header. The API key is sent nowhere else. No code change is needed for this: `DidwwClient(api_key="YOUR_API_KEY", environment=...)` works as before.

- **Audience.** One token per audience, minted on the first call to a service and reused until it expires. The audience is the production hostname of the service, in the sandbox too:

  | Calls | Token audience |
  |-------|----------------|
  | JSON:API resources, export download, encrypted file upload | `api.didww.com` |
  | Voice IN prices | `api-vin.didww.com` |
  | Voice OUT prices | `api-vout.didww.com` |
  | SMS OUT (A2P, P2P, OTP) and SMS IN prices | `api-sms.didww.com` |

  `client.public_keys()` is sent without a token and without any `Authorization` header.
- **Expiry and 401.** A cached token lives for the `expires_in` granted; the SDK adds no local expiry margin. When a request is answered 401, the SDK drops that token, mints a new one and sends the request once more. A second 401 drops the new token too and is not retried: it becomes the error of the call (see [Error Handling](#error-handling)). A 403, such as `insufficient_scope`, is never retried.
- **Concurrency.** Concurrent calls in one process that need the same token from the same store, from one client or several, wait for a single mint, which runs on the thread of the first caller. A waiting thread gives up after 300 s with `AuthErrorKind.CONNECTION_ERROR`.
- **Token service errors** are raised as `DidwwAuthError` from any call that needs a new token (kinds in [Error Handling](#error-handling)):
  - A 429 raises `AuthErrorKind.RATE_LIMITED` with `retry_after` (the `Retry-After` seconds, at least 1). Every further mint for the same token service and API key in the process fails the same way without a request until that time has passed, plus a small random delay so that clients do not retry in step. Such a refusal reports the time still left, so retry in a loop rather than once.
  - A 5xx answer, a connection failure or a timeout is retried with exponential backoff and full jitter (0.5 s base, 8 s cap, 4 attempts in all), then raises `SERVER_ERROR` or `CONNECTION_ERROR`.
  - A 400, a 401 or a TLS failure (such as an untrusted certificate) is raised at once, without a retry.

### Scope

```python
from didww.client import DidwwClient
from didww.configuration import Environment, Scope

read_only = DidwwClient(
    api_key="YOUR_API_KEY",
    environment=Environment.PRODUCTION,
    scope=Scope.READ,  # GET and HEAD only; Scope.FULL allows every method
)
# Without scope no scope is sent and the token service grants full.
```

A `READ` token is enough for the price lookups and price files. A write with a `READ` token is answered 403, which the JSON:API repositories raise as a `DidwwApiError` (see [Error Handling](#error-handling)).

The SDK compares each token it receives with what it asked for:

- a different `scope` (for example `full` granted for a `read` request) or a different `api_version` is logged as a warning (see [Logging](#logging)), and the token is used;
- a token with an empty access token, one that is not a valid header value, or one whose `aud` does not include the requested audience, raises `AuthErrorKind.INVALID_GRANT` and is not cached.

### Token cache

Tokens are cached in a token store, keyed by the token service URL, the API key (as a SHA-256 hash), the audience, the API version and the scope. The key is an opaque string starting with `didww:token:v1:` (`didww.auth.CACHE_KEY_PREFIX`). Each entry is stored for the token's `expires_in`.

The default is one `didww.auth.MemoryTokenStore` in process memory, shared by every client of the process built without `token_store=`, so an application that builds a client per request or per task still reuses its tokens; since the key covers the API key, clients of different accounts never see each other's tokens. Pass `token_store=MemoryTokenStore()` to give a client a cache of its own.

Separate processes, such as gunicorn or uWSGI workers, Celery workers or `multiprocessing` pools, each mint their own tokens unless they share a store. To share tokens between processes, pass your own store. It may subclass `didww.auth.TokenStore` or be any object with these three methods:

```python
from typing import Optional

from didww.auth import AccessToken


class MyTokenStore:
    def get(self, key: str) -> Optional[AccessToken]:
        """The token stored under key, or None when there is none or it has expired."""

    def set(self, key: str, token: AccessToken, ttl: float) -> None:
        """Store token under key for ttl seconds; ttl <= 0 means no expiry."""

    def delete(self, key: str) -> None:
        """Remove the token stored under key, if any."""
```

`AccessToken` is an immutable dataclass (`access_token`, `token_type`, `expires_in`, `aud`, `scope`, `api_version`, `minted_at`). `token.to_dict()` returns it under its wire names, the access token included, and `AccessToken.from_dict(data)` builds it back, so that a store can persist it. Its `repr()` and `str()` never show the access token. A store backed by Redis, for example with [redis-py](https://pypi.org/project/redis/):

```python
import json
import math

import redis

from didww.auth import AccessToken, TokenStore
from didww.client import DidwwClient
from didww.configuration import Environment


class RedisTokenStore(TokenStore):
    def __init__(self, redis_client):
        self._redis = redis_client

    def get(self, key):
        raw = self._redis.get(key)
        if raw is None:
            return None
        return AccessToken.from_dict(json.loads(raw))

    def set(self, key, token, ttl):
        expiry = math.ceil(ttl) if ttl > 0 else None
        self._redis.set(key, json.dumps(token.to_dict()), ex=expiry)

    def delete(self, key):
        self._redis.delete(key)


store = RedisTokenStore(redis.Redis(host="localhost", port=6379, socket_connect_timeout=5, socket_timeout=5))
client = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.PRODUCTION, token_store=store)
```

A shared store holds live bearer tokens, so protect it like the API key. Processes that share a store can each mint once when a token is missing. A store must be safe for concurrent use.

A store that raises does not fail the call: the error is logged as a warning, and the call goes on with a newly minted token (a failed write leaves the token uncached). `get` must return an `AccessToken`, for example built with `AccessToken.from_dict`, or `None`; any other value, such as the `dict` of `to_dict()`, is logged as `DIDWW token store read failed` and ignored. Each call to a store other than `MemoryTokenStore` itself is limited to 10 seconds; the SDK runs it on a daemon thread and stops waiting after that, but an abandoned call keeps its thread until it returns, so bound the store's own I/O as well, as with the Redis timeouts above. The store runs with a copy of the caller's `contextvars`, so it must not depend on thread-locals. After a 401 the refused token is deleted from the store only while it is still the stored one, so that a token another process has just stored survives; a store that keeps returning the refused token, for example after a failed delete, does not get it reused.

**Forked processes.** After `os.fork()` the child keeps a copy of the tokens cached in process memory, and the SDK resets its own locks and pending mints, so a mint in flight in the parent at fork time cannot block the child. Build clients in the child, for example in a gunicorn `post_fork` hook or on first use in the worker, rather than using one built before the fork: its pooled HTTP connections would be shared with the parent.

### Logging

The SDK logs through the standard `logging` module, under the `didww` logger. Following the library convention, `didww` attaches a `logging.NullHandler` to it, so nothing is printed until your application configures logging. To see the events:

```python
import logging

logging.basicConfig()
logging.getLogger("didww").setLevel(logging.DEBUG)
```

Or pass a logger of your own, which the client then uses instead of `didww`:

```python
import logging

from didww.client import DidwwClient
from didww.configuration import Environment

client = DidwwClient(
    api_key="YOUR_API_KEY",
    environment=Environment.PRODUCTION,
    logger=logging.getLogger("myapp.didww"),
)
```

- `WARNING`: `DIDWW token scope mismatch` and `DIDWW token api_version mismatch` (followed by the requested and granted values), and token store failures (`DIDWW token store read failed`, `write failed`, `write skipped`, `delete failed`, with the exception as `exc_info`).
- `DEBUG`: `DIDWW token minted`, with `aud`, `scope`, `api_version`, `expires_in` and `duration_ms`.

Neither the token nor the API key is ever logged. A logger, handler or filter that raises does not fail the call.

### SDK design decisions

- **Audience strategy.** One token per audience, minted on first use, rather than one token naming every service. An account that never calls the prices services never requests their audiences, so a refused audience cannot break DID management, and every token is valid for one service only.
- **Cache store.** In-process memory by default, shared by the clients of the process, because Python applications often build a client per request or task. A shared store is opt-in through `token_store=`. Lifetime is decided by the server through the 401 refresh, not by a local expiry margin.
- **Logger.** The standard `logging` module, silent until your application configures it, so that the SDK does not add a dependency or print on its own.
- **HTTP defaults.** Connect and read timeouts but no total timeout, so that large files are not cut off. No redirects, so that credentials stay on the configured hosts; no cookies, and neither `~/.netrc` nor `session.auth`, so that no state or other credentials reach the requests; no decompression of files, so that they are written as served.
- **Gzip handling.** Price and export files are streamed to your file object or path exactly as served, still gzipped, without being held in memory. The SDK never decompresses a price file on its own: `PriceFileReader` reads a downloaded file when you want rows, and `download_and_decompress_export` writes an export as plain CSV.
- **Upload retry.** The 401 retry sends the request body a second time. `upload_encrypted_file` reads its content into memory once (bytes, or a binary file object read to the end) and builds the multipart body from it, so the retry always resends the complete body.
- **Errors.** One exception class per subsystem with a `kind`, all derived from `DidwwError`, so that `except DidwwError` catches every API, token service, prices and transport failure. A destination that cannot be written raises its `OSError` as is, invalid arguments raise `TypeError` or `ValueError`, and `PriceFileReader` raises `gzip.BadGzipFile`, `EOFError` or `csv.Error` for a damaged file (see [Error Handling](#error-handling) and [Price files](#price-files)).
- **Exact numbers.** Fractional JSON numbers are read as `decimal.Decimal` and written back exactly (see [Numbers](#numbers)).
- **Blocking waits.** Calls are synchronous: the token backoff and the price file 503 retry sleep on the calling thread.

## Resources

### Read-Only Resources

```python
from didww.client import DidwwClient
from didww.configuration import Environment
from didww.query_params import QueryParams

client = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.SANDBOX)

# Countries
countries = client.countries().list().data
country = client.countries().find("uuid").data

# Regions
regions = client.regions().list().data

# Cities
cities = client.cities().list().data

# Areas
areas = client.areas().list().data

# NANPA Prefixes
prefixes = client.nanpa_prefixes().list().data

# DID Groups (with stock keeping units), filtered by number type
params = QueryParams().include("stock_keeping_units").filter("number_type", "toll_free")
groups = client.did_groups().list(params).data

# Available DIDs (with DID group and stock keeping units)
params = QueryParams().include("did_group.stock_keeping_units")
available = client.available_dids().list(params).data

# Proof Types
proof_types = client.proof_types().list().data

# Public Keys
public_keys = client.public_keys().list().data

# Address Requirements
requirements = client.address_requirements().list().data

# Supporting Document Templates
templates = client.supporting_document_templates().list().data

# Balance (singleton)
balance = client.balance().find().data
```

`DidGroup`, `AddressRequirement`, `EmergencyRequirement` and `EmergencyCallingService` carry `number_type`, one of the `NumberType` values (`LOCAL`, `NATIONAL`, `MOBILE`, `TOLL_FREE`, `SHARED_COST`, `GLOBAL`; in filters use the wire value, such as `toll_free`). `DidGroup.is_demo` flags demo groups. `NumberType` replaces the `DidGroupType` resource and the `did_group_type` relationship, which API `2026-10-22` no longer has. The `pops` resource is gone too: a Voice IN trunk carries its point of presence in the `pop` attribute (see [Voice In Trunks](#voice-in-trunks)).

```python
from didww.enums import NumberType

group = client.did_groups().find("uuid").data
if group.number_type == NumberType.TOLL_FREE and not group.is_demo:
    print(group.number_type.value)  # "toll_free"
```

### DIDs

```python
from didww.resources.voice_in_trunk import VoiceInTrunk

# List DIDs
dids = client.dids().list().data

# Update DID - assign trunk and capacity
did = client.dids().find("uuid").data
did.description = "Updated"
did.capacity_limit = 20
did.voice_in_trunk = VoiceInTrunk.build("trunk-uuid")
client.dids().update(did)
```

#### SMS routing

A DID's inbound messages go to an SMS trunk or to an SMS trunk group. The two are exclusive: assigning `sms_trunk` also sends `sms_trunk_group` as `null` in the same request, and assigning `sms_trunk_group` sends `sms_trunk` as `null`, as `voice_in_trunk` and `voice_in_trunk_group` do. Assigning `None` to one of them sends only that one as `null`; set both to unroute the DID.

```python
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_group import SmsTrunkGroup

# sends sms_trunk and sms_trunk_group: null
route = Did.build("did-uuid")
route.sms_trunk = SmsTrunk.build("sms-trunk-uuid")
client.dids().update(route)

# sends sms_trunk_group and sms_trunk: null
to_group = Did.build("did-uuid")
to_group.sms_trunk_group = SmsTrunkGroup.build("sms-trunk-group-uuid")
client.dids().update(to_group)

# unroute: sends sms_trunk: null and sms_trunk_group: null
unroute = Did.build("did-uuid")
unroute.sms_trunk = None
unroute.sms_trunk_group = None
client.dids().update(unroute)

params = QueryParams().filter("sms_trunk.id", "sms-trunk-uuid").include("sms_trunk", "sms_trunk_group")
routed = client.dids().list(params).data  # did.sms_trunk, did.sms_trunk_group
```

An SMS trunk cannot be deleted while DIDs are routed to it, nor an SMS trunk group while DIDs are routed to it or to one of its trunks: unroute those DIDs, or route them elsewhere, first.

### Dirty Serialization

The SDK tracks which attributes and relationships have been changed since a resource was loaded or built.
When `update()` is called, only the modified fields are sent in the PATCH request. Relationships loaded through an include are never sent back; only the ones you assign are.

```python
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.voice_in_trunk import VoiceInTrunk

# Only "description" is sent in the PATCH body
did = client.dids().find("uuid").data
did.description = "Updated"
client.dids().update(did)

# Explicit None sends null to clear a field
did = Did.build("uuid")
did.description = None
client.dids().update(did)

# Exclusive relationships: setting voice_in_trunk automatically nullifies voice_in_trunk_group
did = Did.build("uuid")
did.voice_in_trunk = VoiceInTrunk.build("trunk-uuid")
client.dids().update(did)
# PATCH body: {"data": {"type": "dids", "id": "uuid", "attributes": {}, "relationships": {"voice_in_trunk": {"data": {"type": "voice_in_trunks", "id": "trunk-uuid"}}, "voice_in_trunk_group": {"data": null}}}}

# None unassigns a to-one relationship: sends only "voice_in_trunk": {"data": null}
did = Did.build("uuid")
did.voice_in_trunk = None
client.dids().update(did)

# Included resources also support dirty tracking
params = QueryParams().include("voice_in_trunk")
did = client.dids().find("uuid", params).data
trunk = did.voice_in_trunk
trunk.description = "Updated via include"
client.voice_in_trunks().update(trunk)
```

### Voice In Trunks

```python
from didww.enums import CliFormat, Codec, Pop, TransportProtocol
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.configuration.sip import SipConfiguration

# Create SIP trunk
trunk = VoiceInTrunk()
trunk.name = "My SIP Trunk"
trunk.priority = 1
trunk.weight = 100
trunk.cli_format = CliFormat.E164
trunk.ringing_timeout = 30
trunk.pop = Pop.FRA  # optional; None lets DIDWW choose

sip = SipConfiguration()
sip.host = "sip.example.com"
sip.port = 5060
sip.codec_ids = [Codec.PCMU, Codec.PCMA]
sip.transport_protocol_id = TransportProtocol.UDP
trunk.configuration = sip

created = client.voice_in_trunks().create(trunk).data

# Update trunk
created.description = "Updated"
client.voice_in_trunks().update(created)

# Delete trunk
client.voice_in_trunks().delete(created.id)
```

`pop` is a plain attribute, one of the `didww.enums.Pop` values (`NYC`, `FRA`, `LAC`, `MIA`, `SG`, `HK`, `AMS`). Leave it unset to let DIDWW choose; `trunk.pop = None` on a built or fetched trunk sends `"pop": null`. A value this SDK does not know reads as a plain `str`. It is no longer a relationship and cannot be included.

```python
from didww.enums import Pop
from didww.resources.voice_in_trunk import VoiceInTrunk

pop_update = VoiceInTrunk.build("trunk-uuid")
pop_update.pop = Pop.AMS
client.voice_in_trunks().update(pop_update)
```

#### SIP Registration (2026-04-16)

A Voice In Trunk can also authenticate inbound calls via SIP registration
credentials generated by DIDWW. The SDK auto-cascades the dependent fields
the server requires:

* setting `enabled_sip_registration = True` clears any previously-set
  `host` / `port` (the server rejects them with 422 otherwise);
* setting `host` to a non-`None` value flips `enabled_sip_registration`
  back to `False` and forces `use_did_in_ruri = False` so the server
  accepts the disable PATCH.

The server generates `incoming_auth_username` and `incoming_auth_password`
and surfaces them in the response when SIP registration is enabled.

```python
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.voice_in_trunk import VoiceInTrunk

sip = SipConfiguration()
sip.enabled_sip_registration = True
sip.use_did_in_ruri = True
sip.cnam_lookup = True

trunk = VoiceInTrunk()
trunk.name = "Office (registered)"
trunk.configuration = sip
created = client.voice_in_trunks().create(trunk).data

# created.configuration.incoming_auth_username — server-generated
# created.configuration.incoming_auth_password — server-generated
```

To disable SIP registration on an existing trunk, just set `host` — the
cascade flips `enabled_sip_registration` to `False` and `use_did_in_ruri`
to `False` automatically:

```python
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.voice_in_trunk import VoiceInTrunk

disable = SipConfiguration()
disable.host = "sip.example.com"

trunk = VoiceInTrunk()
trunk.id = "trunk-uuid"
trunk.configuration = disable
client.voice_in_trunks().update(trunk)
```

### Voice In Trunk Groups

```python
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup

group = VoiceInTrunkGroup()
group.name = "Primary Group"
group.capacity_limit = 50
created = client.voice_in_trunk_groups().create(group).data
```

### Voice Out Trunks

> **Note:** Voice Out Trunks require additional account configuration. Contact DIDWW support to enable.

Voice Out Trunks use a polymorphic `authentication_method` (2026-04-16). Three types are supported:

- **`credentials_and_ip`** -- default method; `username` and `password` are server-generated and returned in the response.
- **`twilio`** -- requires a `twilio_account_sid`.
- **`ip_only`** -- read-only; can only be configured by DIDWW staff upon request. Cannot be set via the API.

```python
from didww.enums import DefaultDstAction, OnCliMismatchAction
from didww.resources.voice_out_trunk import VoiceOutTrunk
from didww.resources.authentication_method import CredentialsAndIpAuthenticationMethod

trunk = VoiceOutTrunk()
trunk.name = "My Outbound Trunk"
# NOTE: 203.0.113.0/24 is RFC 5737 TEST-NET-3 documentation space.
# Replace with the real CIDR of your SIP infrastructure.
trunk.authentication_method = CredentialsAndIpAuthenticationMethod(
    allowed_sip_ips=["203.0.113.0/24"],
)
trunk.default_dst_action = DefaultDstAction.ALLOW_ALL
trunk.on_cli_mismatch_action = OnCliMismatchAction.REJECT_CALL
created = client.voice_out_trunks().create(trunk).data
# created.authentication_method.username -- server-generated
# created.authentication_method.password -- server-generated
```

### SMS Trunks

An SMS trunk delivers inbound messages, accepts outbound ones, or both. Its configuration is one of five classes in `didww.resources.sms_trunk_configuration`:

| Type | Class | Notes |
|------|-------|-------|
| `sms_to_email` | `SmsToEmailConfiguration` | Inbound messages are forwarded as email. `send_to`, `subject` and `message` are required. |
| `http_in` | `HttpInConfiguration` | Inbound messages are sent as an HTTP request to your `url`. `http_method` is one of the `SmsHttpMethod` values (`GET`, `POST`, `PUT`); `POST` and `PUT` also need `body_type` (an `SmsBodyType` value) and `body`, which `GET` refuses. `body` is a JSON string for `SmsBodyType.JSON`, a dict for the form encodings and a string for `SmsBodyType.RAW`. Query parameters, headers and body may use the placeholders `{SMS_TEXT}`, `{SMS_TEXT_BASE64_ENCODED}`, `{SMS_SRC_ADDR}`, `{SMS_DST_ADDR}` and `{SMS_TIME}`. |
| `http_out` | `HttpOutConfiguration` | You submit outbound messages over HTTP. `auth_name` and `auth_password` are generated. The submit URL is `trunk.host` (from the trunk's meta). |
| `smpp_esme` | `SmppEsmeConfiguration` | You bind to DIDWW as an SMPP ESME. `server_location` is required; `system_id` and `password` are generated. |
| `smpp_smsc` | `SmppSmscConfiguration` | DIDWW binds to your SMSC with your `host`, `system_id`, `password` and `server_location`. `tx_port` defaults to 2775 and `rx_port` to 2776. |

`configuration.type` is the wire type. The read-only `trunk.allow_in` and `trunk.allow_out` tell which directions a trunk handles. `priority` (0 to 32767, default 100) must stay unset on `http_out` trunks. `server_location` is `SmsServerLocation.NYC` or `SmsServerLocation.AMS`; the sandbox accepts `nyc` only. A configuration type this SDK does not know is read as a `GenericSmsTrunkConfiguration` and sent back unchanged; its numbers keep their exact value.

```python
from didww.enums import SmsBodyType, SmsHttpMethod
from didww.query_params import QueryParams
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import HttpInConfiguration

http_in = HttpInConfiguration()
http_in.url = "https://example.com/sms"
http_in.http_method = SmsHttpMethod.POST
http_in.body_type = SmsBodyType.JSON
http_in.body = '{"text":"{SMS_TEXT}","from":"{SMS_SRC_ADDR}","to":"{SMS_DST_ADDR}"}'

trunk = SmsTrunk()
trunk.name = "Inbound webhook"
trunk.configuration = http_in
created = client.sms_trunks().create(trunk).data

# On update the configuration type must stay the same; attributes never set keep their values.
new_url = HttpInConfiguration()
new_url.url = "https://example.com/sms/v2"
update = SmsTrunk.build(created.id)
update.configuration = new_url
client.sms_trunks().update(update)

# An attribute set to None is sent as null, which clears it
clear = HttpInConfiguration()
clear.http_method = SmsHttpMethod.GET
clear.body_type = None
clear.body = None
cleared = SmsTrunk.build(created.id)
cleared.configuration = clear
client.sms_trunks().update(cleared)

# List by configuration type, with the group
params = QueryParams().filter("configuration.type", "http_in,sms_to_email").include("sms_trunk_group")
trunks = client.sms_trunks().list(params).data
```

A configuration is a value. `trunk.configuration` returns a new copy on every read, so changes made to it are not sent until you assign it back; the assignment marks the configuration for the next update, which sends it as a whole:

```python
trunk = client.sms_trunks().find("sms-trunk-uuid").data
configuration = trunk.configuration  # a copy
configuration.url = "https://example.com/sms/v3"
trunk.configuration = configuration  # sent by the next update
client.sms_trunks().update(trunk)
```

In a configuration, an attribute set to `None` is sent as `null`, and an attribute never set is left out, so on update it keeps its stored value.

`trunk.outgoing_dids = [...]` replaces the whole `outgoing_dids` list of the trunk: list every DID to keep (include `outgoing_dids` to read the current list), or assign an empty list to clear it. `outgoing_dids` must stay empty while `allow_any_did_as_source` is on, so `trunk.allow_any_did_as_source = True` also clears an `outgoing_dids` list that was loaded or assigned before. `incoming_dids` and `sender_id_verifications` can be included but are read-only: assigning them raises `AttributeError`, and they are never sent back. `trunk.sms_trunk_group = None` takes the trunk out of its group.

The generated credentials of `http_out` and `smpp_esme` trunks are read-only and are never sent in a request. The `repr()` of a configuration masks them, the `password` of an `SmppSmscConfiguration`, and the `headers` of an `HttpInConfiguration`, which may carry the credentials of your endpoint, as `[FILTERED]`. A `GenericSmsTrunkConfiguration` masks every attribute value, since its fields are not known; only the attribute names and explicit `None` values are shown. The attributes themselves return the real values, and so does `trunk.attributes`, the raw attribute dict of a resource, whose `repr()` is not masked. To rotate the generated credentials:

```python
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import HttpOutConfiguration, SmppEsmeConfiguration
from didww.resources.sms_trunk_regenerate_credential import SmsTrunkRegenerateCredential

regenerate = SmsTrunkRegenerateCredential()
regenerate.sms_trunk = SmsTrunk.build("sms-trunk-uuid")
client.sms_trunk_regenerate_credentials().create(regenerate)

# The response carries no credentials: read the trunk again
out_trunk = client.sms_trunks().find("sms-trunk-uuid").data
configuration = out_trunk.configuration
if isinstance(configuration, HttpOutConfiguration):
    pass  # configuration.auth_name and configuration.auth_password are the new credentials
elif isinstance(configuration, SmppEsmeConfiguration):
    pass  # configuration.system_id and configuration.password are the new credentials
```

### SMS Trunk Groups

An SMS trunk group spreads a DID's inbound messages over its trunks by their `priority` (the higher value first). `http_out` trunks cannot join a group. Deleting a group also deletes the trunks in it.

```python
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_group import SmsTrunkGroup

group = SmsTrunkGroup()
group.name = "Inbound SMS"
group.sms_trunks = [SmsTrunk.build("sms-trunk-uuid")]
created = client.sms_trunk_groups().create(group).data
print(created.sms_trunks_count)  # 1
```

`group.sms_trunks = [...]` replaces the whole membership of the group: list every trunk to keep. Build the list from the included `sms_trunks`:

```python
from didww.query_params import QueryParams
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_group import SmsTrunkGroup

current = client.sms_trunk_groups().find(
    "sms-trunk-group-uuid", QueryParams().include("sms_trunks")
).data
members = list(current.sms_trunks or [])
members.append(SmsTrunk.build("another-sms-trunk-uuid"))

update = SmsTrunkGroup.build("sms-trunk-group-uuid")
update.sms_trunks = members
client.sms_trunk_groups().update(update)

# An empty list (or None) removes every trunk from the group
empty = SmsTrunkGroup.build("sms-trunk-group-uuid")
empty.sms_trunks = []
client.sms_trunk_groups().update(empty)
```

`incoming_dids` can be included but is read-only.

### Sender ID Verifications

A Sender ID verification covers the sender IDs your outbound messages use. It is created and reviewed outside the API: the API lists and reads verifications, and changes only their `name` and the SMS trunk their messages are routed through. A closed verification cannot be changed. `status` is one of the `SenderIdVerificationStatus` values and `sender_type` one of the `SenderType` values; `is_active`, `is_closed` and the other `is_*` properties test the status. `verification.meta["setup_price"]` and `verification.meta["monthly_price"]` hold the prices of the meta as decimal strings.

```python
from didww.query_params import QueryParams
from didww.resources.sender_id_verification import SenderIdVerification
from didww.resources.sms_trunk import SmsTrunk

params = QueryParams().filter("status", "active").include("sms_trunk")
verifications = client.sender_id_verifications().list(params).data

# http_out, smpp_esme or smpp_smsc trunks only
route = SenderIdVerification.build(verifications[0].id)
route.sms_trunk = SmsTrunk.build("sms-trunk-uuid")
client.sender_id_verifications().update(route)

# Outbound messages stop until a trunk is assigned again
unroute = SenderIdVerification.build(verifications[0].id)
unroute.sms_trunk = None
client.sender_id_verifications().update(unroute)
```

Deleting an SMS trunk leaves the verifications routed through it without a trunk. The other relationships (`countries`, `dids`, `order`, `identity`, `address`) can be included but are read-only and never sent back.

### Orders

```python
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.resources.order_item.capacity_order_item import CapacityOrderItem
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem

# Order by SKU
order = Order()
item = DidOrderItem()
item.sku_id = "sku-uuid"
item.qty = 2
order.items = [item]
created = client.orders().create(order).data

# Order available DID
item = AvailableDidOrderItem()
item.available_did_id = "available-did-uuid"
item.sku_id = "sku-uuid"

# Order reserved DID
item = ReservationDidOrderItem()
item.did_reservation_id = "reservation-uuid"
item.sku_id = "sku-uuid"

# Order capacity
item = CapacityOrderItem()
item.capacity_pool_id = "pool-uuid"
item.qty = 1
```

### DID Reservations

```python
from didww.resources.did_reservation import DidReservation
from didww.resources.available_did import AvailableDid

reservation = DidReservation()
reservation.description = "Reserved for client"
reservation.available_did = AvailableDid.build("available-did-uuid")
created = client.did_reservations().create(reservation).data

# Delete reservation
client.did_reservations().delete(created.id)
```

### Shared Capacity Groups

```python
from didww.resources.shared_capacity_group import SharedCapacityGroup
from didww.resources.capacity_pool import CapacityPool

scg = SharedCapacityGroup()
scg.name = "Shared Group"
scg.shared_channels_count = 20
scg.metered_channels_count = 5
scg.capacity_pool = CapacityPool.build("pool-uuid")
created = client.shared_capacity_groups().create(scg).data
```

### Address Verifications

```python
from didww.resources.address_verification import AddressVerification
from didww.resources.address import Address

# List address verifications
verifications = client.address_verifications().list().data

# Create address verification
verification = AddressVerification()
verification.address = Address.build("address-uuid")
created = client.address_verifications().create(verification).data

# Update external_reference_id
created.external_reference_id = "my-ref-123"
client.address_verifications().update(created)
```

### Emergency Requirements

```python
# List emergency requirements
emergency_reqs = client.emergency_requirements().list().data
for req in emergency_reqs:
    print(f"{req.name}: {req.estimate_setup_time}")

# Find a specific emergency requirement
req = client.emergency_requirements().find("uuid").data
```

### Emergency Verifications

```python
from didww.resources.emergency_verification import EmergencyVerification
from didww.resources.address import Address

# List emergency verifications
verifications = client.emergency_verifications().list().data

# Create emergency verification
verification = EmergencyVerification()
verification.address = Address.build("address-uuid")
created = client.emergency_verifications().create(verification).data

# Update external_reference_id
created.external_reference_id = "ext-ref-456"
client.emergency_verifications().update(created)
```

### Emergency Calling Services

```python
# List emergency calling services
services = client.emergency_calling_services().list().data
for svc in services:
    print(f"Status: {svc.status}, Renew: {svc.renew_date}")

# Find a specific emergency calling service
service = client.emergency_calling_services().find("uuid").data

# Delete an emergency calling service
client.emergency_calling_services().delete("uuid")
```

### DID History

```python
from didww.query_params import QueryParams

# List DID history records
params = QueryParams().filter("did.id", "did-uuid")
history = client.did_history().list(params).data
for record in history:
    print(f"DID: {record.number}, Order Date: {record.order_created_at}")

# Find a specific DID history record
record = client.did_history().find("uuid").data
```

### Identities

```python
from didww.enums import IdentityType
from didww.resources.identity import Identity
from didww.resources.country import Country

identity = Identity()
identity.first_name = "John"
identity.last_name = "Doe"
identity.phone_number = "12125551234"
identity.identity_type = IdentityType.PERSONAL
identity.country = Country.build("country-uuid")
created = client.identities().create(identity).data
```

`company_website` belongs to business identities; a personal identity refuses it. It is left out of a create request while `None`, and `identity.company_website = None` on a built or fetched identity clears it on update.

```python
from didww.resources.identity import Identity

business = Identity.build("identity-uuid")
business.company_website = "https://www.example.com"
client.identities().update(business)
```

### Addresses

```python
from didww.resources.address import Address
from didww.resources.identity import Identity
from didww.resources.country import Country

address = Address()
address.city_name = "New York"
address.postal_code = "10001"
address.address = "123 Main St"
address.identity = Identity.build("identity-uuid")
address.country = Country.build("country-uuid")
created = client.addresses().create(address).data
```

### Exports

```python
from datetime import datetime, timedelta, timezone

from didww.enums import ExportType
from didww.resources.export import Export

# Dates are "YYYY-MM-DD HH:MM:SS" in UTC: from is inclusive, to is exclusive and not in the future
today = datetime.now(timezone.utc).date()
date_from = f"{today - timedelta(days=1)} 00:00:00"
date_to = f"{today} 00:00:00"

export = Export()
export.export_type = ExportType.CDR_IN
export.filters = {"from": date_from, "to": date_to}
created = client.exports().create(export).data

# SMS export
sms_out = Export()
sms_out.export_type = ExportType.SMS_OUT
sms_out.filters = {
    "from": date_from,
    "to": date_to,
    "service_type": "a2p",
    "sms_trunk.id": ["sms-trunk-uuid"],
}
created_sms = client.exports().create(sms_out).data

# The export is pending until its file is generated; read it again later
completed = client.exports().find(created_sms.id).data
if completed.is_completed:
    client.download_export(completed.url, "export.csv.gz")              # gzipped CSV, as served
    client.download_and_decompress_export(completed.url, "export.csv")  # plain CSV

    with open("copy.csv.gz", "wb") as out:
        client.download_export(completed.url, out)                      # any binary file object
```

The export downloads send the token only to the origin (scheme, host and port) of the JSON:API base URL or of the environment, so export URLs, which the API builds on the environment's host, are still downloaded when `base_url` points elsewhere. A URL on any other origin raises a `DidwwClientError` and nothing is sent. Only a 200 answer is written, as it arrives, without holding the file in memory; redirects are not followed, and any other status, a 3xx or a 204 included, raises a `DidwwApiError` (see [Error Handling](#error-handling)). A file whose size differs from its `Content-Length`, a transfer that breaks off and gzip data that cannot be decompressed raise a `DidwwClientError`.

A path destination is written to a temporary file next to it, which replaces it (`os.replace`) only once the whole file has arrived (or has been decompressed); after a failure an existing file is left as it was. The new file gets the permissions of a new file (the umask on POSIX systems), not those of the file it replaces, and a symlink at the path is replaced, not followed. To keep an existing file's permissions, pass a binary file object opened on it. A binary file object destination is written as the data arrives and is not closed, so it may hold part of the file after a failure. A destination that cannot be written raises the `OSError` as is.

`from` and `to` are required for every export type (`cdr_in`, `cdr_out`, `sms_in`, `sms_out`). The other filter keys depend on the type:

- `cdr_in`: `did_number`, `source_number`, `source_number_out`, `source_country_iso`;
- `cdr_out`: `voice_out_trunk.id`, `source`, `cli`, `destination`;
- `sms_in` and `sms_out`: `source_address_eq`, `source_address_cont`, `destination_address_eq`, `destination_address_cont`, `status`, `sms_id`, `sms_trunk.id` (a string or a list of strings);
- `sms_in` only: `trunk_type`, one or more of the `ExportTrunkType` values (`SMPP SMSC`, `SMPP ESME`, `Email`, `HTTP IN`);
- `sms_out` only: `service_type` (`a2p` or `p2p`) and `sender_id_verification.id` (a string or a list of strings).

The docstring of `Export.filters` lists the keys of every type. Enum members in `filters`, such as `ExportTrunkType.HTTP_IN`, are sent as their value.

## Prices

Prices are served by three services outside the JSON:API (hosts in [Environments](#environments)). Each price list has a price file and a lookup:

| Accessor | Service | Price file | Lookup | Lookup rows |
|----------|---------|------------|--------|-------------|
| `client.voice_in_prices()` | Voice IN | `prices.csv.gz` | `lookup/prices` | `VoiceInPrice` |
| `client.voice_out_prices()` | Voice OUT | `prices.csv.gz` | `lookup/prices` | `VoiceOutPrice` |
| `client.sms_out_a2p_prices()` | SMS | `sms_out/a2p/prices.csv.gz` | `sms_out/a2p/lookup/prices` | `SmsOutPrice` |
| `client.sms_out_p2p_prices()` | SMS | `sms_out/p2p/prices.csv.gz` | `sms_out/p2p/lookup/prices` | `SmsOutPrice` |
| `client.sms_out_otp_prices()` | SMS | `sms_out/otp/prices.csv.gz` | `sms_out/otp/lookup/prices` | `SmsOutPrice` |
| `client.sms_in_prices()` | SMS | `sms_in/prices.csv.gz` | `sms_in/lookup/prices` | `SmsInPrice` |

Each accessor returns a `PricesService`; it, the row classes, `PriceLookup`, `PriceFile` and `PriceFileReader` are in package `didww.prices`. The account needs a price plan of that service: without one, every call raises `PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED`.

### Price lookups

```python
from didww.prices import VoiceOutPriceCategory

result = client.voice_in_prices().lookup({"number": "18005550123", "src_country_iso": "US"})
print(result.total_records)
for price in result:
    if price.rate is not None:
        print(f"{price.destination} {price.source_type}: {price.rate} USD/min")

voice_out = client.voice_out_prices().lookup({"number": "493012345678"})
if voice_out[0].category == VoiceOutPriceCategory.INTERNATIONAL:
    print(voice_out[0].rate)
a2p = client.sms_out_a2p_prices().lookup({"dst_number": "4915123456789"})
sms_in = client.sms_in_prices().lookup({"dst_country_iso": "US"})
```

| Service | Filters |
|---------|---------|
| Voice IN | `number` (required), `src_country_iso` |
| Voice OUT | `number` (required); no other filter |
| SMS OUT and SMS IN | `dst_number`, `dst_country_iso`; at least one |

Filter names are given without `filter[...]`, and values as strings. A missing or unknown filter raises a `ValueError` before any request; `None` and blank values are dropped (`service.allowed_filters` lists the names). The server checks the value formats and answers a bad value with 400 (`PricesErrorKind.BAD_REQUEST`). A lookup is not retried, except once with a new token after a 401.

`lookup` returns a `PriceLookup` with `rows` (a tuple) and `total_records` (0 when the answer does not give it); it can also be iterated, indexed and measured with `len()`. It always holds at least one row: no match raises `PricesErrorKind.PRICE_NOT_FOUND`, never an empty result. The rows are frozen dataclasses. Prices and fees are `decimal.Decimal` in USD, VAT excluded, as exact as the answer; they are `None` when the row rejects the calls or messages (see `reject_calls` and `reject_sms`). Intervals and increments are `int`, `SmsOutPrice.mcc` and `mnc` are `int`, `VoiceOutPrice.effective_at` is a timezone-aware `datetime` and `VoiceOutPrice.category` is one of the `VoiceOutPriceCategory` values (`INTERNATIONAL`, `ORIGIN_BASED`, `LOCAL`), or a plain `str` for a category this SDK does not know.

The `id` of an SMS OUT or SMS IN lookup row is derived from its content: it changes when the row or its price changes, so do not use it to track a destination over time. A Voice OUT `id` stays the same when a re-import changes only the price. A Voice IN `id` names the answering row of the plan.

### Price files

The files are gzipped CSV with a header row. The SDK writes them exactly as served and never decompresses them.

```python
import itertools
from datetime import datetime, timezone

from didww.prices import PriceFileReader

prices = client.voice_in_prices()
path = "voice_in_prices.csv.gz"

# Download unless the copy at the path is current
file = prices.fetch(path)
if file.not_modified:
    print("answered 304, the file was kept")
else:
    print(f"downloaded {file.bytes_written} bytes, last modified {file.last_modified}")

# Read the rows, keyed by the header line
with PriceFileReader(path) as rows:
    for row in itertools.islice(rows, 5):
        print(f"{row['Destination']}: {row['Rate (USD, excl. VAT)']}")

# Lower-level calls
status = prices.head(file.last_modified)  # sent as If-Modified-Since; None sends none
# status.not_modified, status.content_length (None when unknown),
# status.filename (from Content-Disposition, e.g. "voice_in_prices.csv.gz")
status = prices.head(datetime(2026, 10, 1, tzinfo=timezone.utc))  # an aware datetime

file = prices.download_to_file(path)
with open("copy_of_voice_in_prices.csv.gz", "wb") as out:
    file = prices.download(out)  # any binary file object; download(out, if_modified_since) sends If-Modified-Since
```

- `fetch(path)` sends the modification time of the file at `path` as `If-Modified-Since`, when the file is there; an unchanged price file is answered 304 and the file is kept. A file written by `download_to_file` or `fetch` gets the `Last-Modified` of the response as its modification time, so the date matches the copy on disk. `fetch` trusts the modification time of any file at `path`: a file copied or changed by other means can be answered 304 and kept, so replace such a file with `download_to_file`.
- `if_modified_since` of `head` and `download` must be a timezone-aware `datetime` (a naive one, or one whose UTC time falls outside years 1 to 9999, raises `ValueError`) or `None`; it is sent in whole seconds as an HTTP date in GMT.
- `download_to_file` and `fetch` stream the body into a temporary file next to `path`, unique to the call, which gets the permissions of a new file (the umask on POSIX systems), is flushed to the disk and replaces `path` atomically (`os.replace`) only on a complete 200. A 304 or an error leaves an existing file untouched, the temporary file is always removed, and concurrent downloads to one path do not mix their bytes. A directory that does not exist raises a `FileNotFoundError` without a request. **On Windows the replacement fails while `path` is open**, for example by a `PriceFileReader` that has not been closed.
- `download(fileobj)` and `download(fileobj, if_modified_since)` write the body into the binary file object only on a 200, as it arrives, so after a transfer error it may hold part of it. The file object is not closed. An `OSError` of the file object is raised as is.
- A body whose size differs from its `Content-Length` raises `PricesErrorKind.CONNECTION_ERROR`; it never replaces a file.
- `head` and the downloads return a `PriceFile`: `status_code`, `last_modified` (an aware UTC `datetime`, or `None` when absent), `content_length`, `filename` (as sent: check it before using it as a path), `bytes_written` and `not_modified`.
- `PriceFileReader(path)` and `PriceFileReader(fileobj)` gunzip a downloaded file and iterate over its rows, each a `dict` keyed by the header line, as served (for example `Rate (USD, excl. VAT)`), in header order. A UTF-8 byte order mark and empty lines are skipped, and invalid UTF-8 reads as U+FFFD. A file of several gzip members is read in full. While the rows are read, input that is not valid gzip (a bad checksum, corrupt compressed data or other data after the gzip data) raises `gzip.BadGzipFile`; gzip data cut short, an empty input included, raises `EOFError` or `gzip.BadGzipFile`; bad quoting or a row whose field count differs from the header raises `csv.Error`. Rows before the error have already been passed on. Use it as a context manager, or call `close()`: a reader of a path closes the file, a reader of a file object leaves it open.
- Only `Last-Modified` and `If-Modified-Since` are used, in whole seconds. The service sends no `ETag`, and the SDK never sends `If-None-Match`, which would make the service ignore `If-Modified-Since`.
- A 503 on a price file is retried up to 2 times when its `Retry-After` is 60 seconds or less, after waiting that long (at least 1 s) plus a small random delay so that clients do not retry in step. Otherwise it raises `PricesErrorKind.SERVICE_UNAVAILABLE` with `retry_after`. Lookups and other statuses, 429 included, are not retried.
- A 404 `price_not_found` raises `PRICE_NOT_FOUND`; any other 404, `price_plan_not_assigned` included, and any 404 on `head`, which has no body, raises `PRICE_PLAN_NOT_ASSIGNED`. `DidwwPricesError.code` holds the code of the answer, or `price_plan_not_assigned` for a 404 without one.
- Redirects are not followed. A status without its own kind in [Error Handling](#error-handling), such as a 3xx, a 202 or a 204, raises `PricesErrorKind.UNEXPECTED_STATUS`. An error is never turned into an empty file or an empty result.

## Filtering, Sorting, and Pagination

> See [`FILTERS.md`](FILTERS.md) for the list of `filter[KEY]` keys accepted by every list endpoint at API version `2026-10-22`.

```python
from didww.query_params import QueryParams

params = (
    QueryParams()
    .filter("country.id", "uuid")
    .filter("name", "Arizona")
    .include("country")
    .sort("name")
    .page(1, 25)
)

regions = client.regions().list(params).data
```

## Date and Datetime Fields

The SDK distinguishes between date-only and datetime fields:

- **Datetime fields** are deserialized as timezone-aware `datetime.datetime`:
  - `created_at` — present on most resources
  - `updated_at` — `SmsTrunk`, `SmsTrunkGroup`
  - `expires_at` — `Did`, `DidReservation`, `Proof`, `EncryptedFile` (nullable)
  - `activated_at` — `EmergencyCallingService`, `SenderIdVerification` (nullable)
  - `canceled_at` — `EmergencyCallingService` (nullable)
  - `closed_at` — `SenderIdVerification` (nullable)
  - `effective_at` — `VoiceOutPrice` price lookup rows (nullable)
- **Date-only fields** remain as `str` in `"YYYY-MM-DD"` format:
  - `Identity.birth_date`
  - `CapacityPool.renew_date`, `EmergencyCallingService.renew_date` (nullable)
  - `SenderIdVerification.renew_date` — `None` once the verification is closed
  - `DidOrderItem.billed_from` / `billed_to`
- **String fields** (not numeric):
  - `EmergencyRequirement.estimate_setup_time` — e.g. `"7-14 days"`, `"1"`
  - `EmergencyRequirement.requirement_restriction_message` — nullable

**Important changes from previous API versions:**
- `expire_at` renamed to `expires_at` on `DidReservation` and `EncryptedFile`
- `renew_date` is a date-only string, NOT a datetime
- `estimate_setup_time` is a string, NOT an integer

```python
did = client.dids().find("uuid").data
print(did.created_at)   # datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
print(did.expires_at)   # None or datetime(...)

identity = client.identities().find("uuid").data
print(identity.birth_date)  # "1990-05-20"
```

## Numbers

Fractional JSON numbers in API answers are read as `decimal.Decimal`, with their exact value, and integers as `int`; values the API sends as JSON strings stay `str`. This covers every place the SDK reads JSON: resource attributes, `meta`, the unknown configurations of `GenericSmsTrunkConfiguration`, export `filters` and the `errors` of a `DidwwApiError`. The price lookup rows convert prices and fees to `Decimal` too (see [Price lookups](#price-lookups)).

Request bodies are encoded by the SDK: a `Decimal` is sent exactly as it is, a `float` as its shortest `repr`, and enum members as their value. `NaN` and infinities are refused with a `ValueError`. Compare money with `Decimal` (`Decimal("0.10") == Decimal("0.1")` is `True`), not with `float`.

## Enums

The SDK provides enum classes in `didww.enums` for all API option fields:

`CallbackMethod`, `IdentityType`, `OrderStatus`, `ExportType`, `ExportStatus`, `CliFormat`,
`OnCliMismatchAction`\*, `MediaEncryptionMode`, `DefaultDstAction`, `VoiceOutTrunkStatus`,
`EmergencyCallingServiceStatus`, `EmergencyVerificationStatus`, `DiversionRelayPolicy`,
`TransportProtocol`, `Codec`, `RxDtmfFormat`, `TxDtmfFormat`, `SstRefreshMethod`,
`ReroutingDisconnectCode`, `Feature`, `AreaLevel`, `AddressVerificationStatus`, `StirShakenMode`,
`NumberType`, `Pop`, `SenderIdVerificationStatus`, `SenderType`, `SmsHttpMethod`, `SmsBodyType`,
`SmsServerLocation`, `ExportTrunkType`

\* `REPLACE_CLI` and `RANDOMIZE_CLI` require additional account configuration. Contact DIDWW support to enable these values.

`ExportType` includes `SMS_IN` and `SMS_OUT`. `VoiceOutPriceCategory` is in `didww.prices`, `Scope` in `didww.configuration`, and `AuthErrorKind` and `PricesErrorKind` in `didww.exceptions`. A value the API sends that this SDK does not know reads as a plain `str`.

```python
from didww.enums import CallbackMethod, ExportType, IdentityType
from didww.resources.order import Order
from didww.resources.identity import Identity

order = Order()
order.callback_method = CallbackMethod.POST

identity = Identity()
identity.identity_type = IdentityType.BUSINESS

print(ExportType.CDR_IN.value)  # "cdr_in"
```

The string enums are `str` subclasses, so they compare equal to their wire value and can be passed to `QueryParams().filter(...)`. Print or format their `.value`: `str()` and f-strings show the member name on some Python versions.

## File Encryption

The SDK provides an `Encrypt` utility for encrypting files before upload, using RSA-OAEP + AES-256-CBC (matching DIDWW's encryption requirements).

```python
from didww.encrypt import Encrypt

# The public keys of DIDWW (public_keys is called without a token)
public_keys = [pk.key for pk in client.public_keys().list().data]

with open("document.pdf", "rb") as f:
    file_bytes = f.read()

fingerprint = Encrypt.calculate_fingerprint(public_keys)
encrypted = Encrypt.encrypt_with_keys(file_bytes, public_keys)
```

Upload the encrypted file, one file per request:

```python
encrypted_file_id = client.upload_encrypted_file(
    fingerprint,                 # Encrypt.calculate_fingerprint(...)
    encrypted,                   # encrypted bytes, or a binary file object
    description="document.pdf",
    filename="document.pdf.enc",
)
```

`upload_encrypted_file(fingerprint, data, description=None, filename="file.enc")` returns the ID of the new encrypted file. `data` is read into memory once, so that the request can be sent again with a new token after a 401. The upload goes through the SDK's session (proxy, TLS settings) with a bearer token. An error status raises a `DidwwApiError` with the errors of the answer.

## Webhook Signature Validation

Validate incoming webhook callbacks from DIDWW using HMAC-SHA1 signature verification.

Initialize the validator with the callback secret that is enabled in the DIDWW User Panel (**APIs → DIDWW API 3 → Callback Secrets**). DIDWW signs every callback with it and sends callbacks only while a callback secret is enabled.

```python
from didww.callback.request_validator import RequestValidator

validator = RequestValidator("YOUR_CALLBACK_SECRET")

# In your webhook handler:
valid = validator.validate(
    url=request_url,       # full original URL
    payload=payload_dict,  # dict of payload key-value pairs
    signature=signature,   # value of X-DIDWW-Signature header
)
```

## Error Handling

The SDK's own exceptions derive from `DidwwError`, in `didww.exceptions`. Their messages, `str()` and `repr()` never contain the API key or a token, and neither do the `repr()` of tokens, token stores and SMS trunk configurations. When a `requests` exception is the cause of an SDK exception, the request and response it held are detached, since their headers carry the key or the token. Tools that record the local variables of stack frames, such as some error trackers, can still see the key held by the client: configure them to scrub `api_key`, `Api-Key` and `Authorization`.

```python
from didww.exceptions import DidwwApiError, DidwwClientError

try:
    client.voice_in_trunks().find("nonexistent")
except DidwwApiError as e:
    print(f"HTTP Status: {e.status_code}")
    for error in e.errors:
        print(f"Error: {error.get('detail', error.get('title'))}")
except DidwwClientError as e:
    print(f"Client error: {e}")
```

| Exception | Raised for |
|-----------|------------|
| `DidwwApiError` | An error status of the JSON:API repositories, of `upload_encrypted_file` and of the export downloads, with `status_code` and `errors` (a list of dicts; `[{"title": "HTTP <status>"}]` when the answer has none). |
| `DidwwClientError` | A failure on the client side: an invalid constructor argument (see [Configuration](#configuration)), a JSON:API, upload or export call that fails in transport (a connection failure, a timeout or a TLS error; the `requests` exception is the `__cause__`), an answer that is not valid JSON, a refused export URL, an export download that breaks off, is incomplete or cannot be decompressed, a price lookup answer that cannot be parsed or holds no prices. |
| `DidwwAuthError` | The token service, from any call that needs a new token. |
| `DidwwPricesError` | The prices services. |

`DidwwApiError` also reports the authentication failures of the API: a 401 still answered after the token was replaced once (`status_code` 401), and a 403 such as `insufficient_scope` for a write with a `READ` token, which is never retried. Redirects are not followed: a 3xx answer of the JSON:API raises a `DidwwApiError` with that status, and the export downloads raise one for any status other than 200, such as a 3xx or a 204.

The token service and prices errors carry a `kind`:

```python
from didww.exceptions import (
    AuthErrorKind,
    DidwwAuthError,
    DidwwError,
    DidwwPricesError,
    PricesErrorKind,
)

try:
    client.sms_out_a2p_prices().lookup({"dst_number": "4915123456789"})
except DidwwAuthError as e:
    if e.kind == AuthErrorKind.RATE_LIMITED:
        # Wait retry_after seconds and try again; repeat while the kind is RATE_LIMITED.
        print(f"Token service rate limit, retry after {e.retry_after} s")
    elif e.kind == AuthErrorKind.INVALID_CLIENT:
        print(f"API key refused: {e}")
    else:
        raise
except DidwwPricesError as e:
    if e.kind == PricesErrorKind.PRICE_NOT_FOUND:
        print("No price for this number")
    elif e.kind == PricesErrorKind.TOO_MANY_REQUESTS:
        print(f"Prices rate limit, retry after {e.retry_after} s")
    else:
        raise
except DidwwError as e:
    print(f"Error: {e}")
```

**Token service** (`DidwwAuthError`, with `kind`, `status_code`, `error`, `error_description` and `retry_after`):

| `AuthErrorKind` | Raised when |
|-----------------|-------------|
| `INVALID_CLIENT` | 401: the token service refused the API key. Not retried. |
| `INVALID_REQUEST` | 400, e.g. `invalid_request` or `invalid_scope`. |
| `RATE_LIMITED` | 429. `retry_after` is the server's wait in seconds. Further mints fail without a request until that time plus a small random delay has passed; such a refusal reports the time still left in `retry_after`, so retry in a loop rather than once. |
| `SERVER_ERROR` | 5xx on the last of the 4 attempts. |
| `CONNECTION_ERROR` | Connection failure or timeout on the last attempt, a TLS failure (not retried), an answer that could not be read, or a wait for another thread's mint that failed or did not end. `status_code` is `None` unless an answer arrived. |
| `INVALID_GRANT` | The token is empty, not a valid header value, or does not cover the requested audience. |
| `UNEXPECTED_STATUS` | Any other status, such as a redirect. |

**Prices** (`DidwwPricesError`, with `kind`, `status_code`, `code`, `errors` and `retry_after`):

| `PricesErrorKind` | Status |
|-------------------|--------|
| `BAD_REQUEST` | 400, e.g. a filter value of the wrong format |
| `NOT_AUTHORIZED` | 401 after the token was replaced once |
| `ACCESS_DENIED` | 403 |
| `PRICE_PLAN_NOT_ASSIGNED` | 404 `price_plan_not_assigned`, and any other 404 except `price_not_found`, including any 404 on `head`, which has no body |
| `PRICE_NOT_FOUND` | 404 `price_not_found`: no price matches the lookup |
| `NOT_ACCEPTABLE` | 406 |
| `TOO_MANY_REQUESTS` | 429, with `retry_after` when the service sends it in seconds. Not retried. |
| `SERVICE_UNAVAILABLE` | 503, with `retry_after`. Retried on price files only, see [Price files](#price-files). |
| `UNEXPECTED_STATUS` | Any other status, such as a redirect, a 202, a 204 or a 304 to a lookup |
| `CONNECTION_ERROR` | Connection failure, timeout, TLS failure, or a response body that breaks off or whose size differs from its `Content-Length`. Not retried. |

The prices services can also raise a `DidwwAuthError`, and `lookup` a `ValueError` or `TypeError` for invalid filters and a `DidwwClientError` when a 200 answer is not a JSON:API document it can parse or holds no prices. A destination file object or file that cannot be written, and the file system errors of `download_to_file` and `fetch` (temporary file, times, replacement), raise the `OSError` as is; so do the export downloads. Outside `DidwwError`, the SDK also raises `TypeError` for an argument of the wrong type, such as a destination that is neither a path nor a binary file object, and `ValueError` for a naive or out-of-range `if_modified_since`.

## Trunk Configuration Types

| Type | Class |
|------|-------|
| SIP | `SipConfiguration` |
| PSTN | `PstnConfiguration` |

For the SMS trunk configuration types, see [SMS Trunks](#sms-trunks).

## Order Item Types

| Type | Class |
|------|-------|
| DID | `DidOrderItem` |
| Available DID | `AvailableDidOrderItem` |
| Reservation DID | `ReservationDidOrderItem` |
| Capacity | `CapacityOrderItem` |
| Generic | `GenericOrderItem` |

## All Supported Resources

| Resource | Repository | Operations |
|----------|-----------|------------|
| Country | `client.countries()` | list, find |
| Region | `client.regions()` | list, find |
| City | `client.cities()` | list, find |
| Area | `client.areas()` | list, find |
| NanpaPrefix | `client.nanpa_prefixes()` | list, find |
| DidGroup | `client.did_groups()` | list, find |
| AvailableDid | `client.available_dids()` | list, find |
| ProofType | `client.proof_types()` | list, find |
| PublicKey | `client.public_keys()` | list |
| AddressRequirement | `client.address_requirements()` | list, find |
| SupportingDocumentTemplate | `client.supporting_document_templates()` | list, find |
| Balance | `client.balance()` | find |
| Did | `client.dids()` | list, find, update |
| VoiceInTrunk | `client.voice_in_trunks()` | list, find, create, update, delete |
| VoiceInTrunkGroup | `client.voice_in_trunk_groups()` | list, find, create, update, delete |
| VoiceOutTrunk | `client.voice_out_trunks()` | list, find, create, update, delete |
| VoiceOutTrunkRegenerateCredential | `client.voice_out_trunk_regenerate_credentials()` | create |
| SmsTrunk | `client.sms_trunks()` | list, find, create, update, delete |
| SmsTrunkGroup | `client.sms_trunk_groups()` | list, find, create, update, delete |
| SmsTrunkRegenerateCredential | `client.sms_trunk_regenerate_credentials()` | create |
| SenderIdVerification | `client.sender_id_verifications()` | list, find, update |
| DidReservation | `client.did_reservations()` | list, find, create, delete |
| CapacityPool | `client.capacity_pools()` | list, find, update |
| SharedCapacityGroup | `client.shared_capacity_groups()` | list, find, create, update, delete |
| Order | `client.orders()` | list, find, create, update, delete |
| Export | `client.exports()` | list, find, create, update |
| Address | `client.addresses()` | list, find, create, update, delete |
| AddressVerification | `client.address_verifications()` | list, find, create, update |
| Identity | `client.identities()` | list, find, create, update, delete |
| EncryptedFile | `client.encrypted_files()` | list, find, delete |
| PermanentSupportingDocument | `client.permanent_supporting_documents()` | list, find, create, delete |
| Proof | `client.proofs()` | list, find, create, delete |
| AddressRequirementValidation | `client.address_requirement_validations()` | create |
| DidHistory | `client.did_history()` | list, find |
| EmergencyRequirement | `client.emergency_requirements()` | list, find |
| EmergencyRequirementValidation | `client.emergency_requirement_validations()` | create |
| EmergencyCallingService | `client.emergency_calling_services()` | list, find, delete |
| EmergencyVerification | `client.emergency_verifications()` | list, find, create, update |
| StockKeepingUnit | _(include-only)_ | included via `did_groups`, `available_dids` |
| QtyBasedPricing | _(include-only)_ | included via `capacity_pools` |
| VoiceInPrice | `client.voice_in_prices()` | lookup, head, download, download_to_file, fetch |
| VoiceOutPrice | `client.voice_out_prices()` | lookup, head, download, download_to_file, fetch |
| SmsOutPrice | `client.sms_out_a2p_prices()`, `client.sms_out_p2p_prices()`, `client.sms_out_otp_prices()` | lookup, head, download, download_to_file, fetch |
| SmsInPrice | `client.sms_in_prices()` | lookup, head, download, download_to_file, fetch |

> **Include-only resources** have no standalone API endpoint. They are returned as included
> relationships when fetching their parent resources with the appropriate `include` parameter.
> The price rows are served by the prices services outside the JSON:API, see [Prices](#prices).

## Migrating from 3.x

4.0.0 targets API `2026-10-22` only. To stay on API `2026-04-16`, keep 3.x (`pip install "didww>=3,<4"`, branch [`release-3`](https://github.com/didww/didww-api-3-python-sdk/tree/release-3)).

Most code keeps working: `DidwwClient(api_key, environment)` is unchanged, and the SDK mints the access tokens itself. The breaking changes:

- **Authentication.** Every request carries a bearer token minted from the API key (see [Authentication](#authentication)). The `Api-Key` header is sent only to the token service, so outgoing traffic must reach `auth.didww.com` (`auth-sandbox.didww.com` in the sandbox), and the price hosts when you use prices. The token service can raise a `DidwwAuthError` from any call; an API key that is refused now raises `DidwwAuthError` with `AuthErrorKind.INVALID_CLIENT` instead of a `DidwwApiError` with status 401.
- **API version.** `X-DIDWW-API-Version` is no longer sent: the version is requested in the token. `DidwwClient.API_VERSION` is removed; use `DidwwClient.DEFAULT_API_VERSION` (also `didww.configuration.DEFAULT_API_VERSION`) or `client.api_version`. The default is `2026-10-22`, and an earlier version makes the constructor raise a `DidwwClientError`.
- **Pickling.** A `DidwwClient` can no longer be pickled or deep-copied: it holds locks and its token cache. Build a client in each process or worker instead of passing one to it.
- **Environment.** `environment` also selects the token service and the price hosts, and is not derived from `base_url`: to reach production, pass `environment=Environment.PRODUCTION` (a production `base_url` alone mints at the sandbox token service and fails with `DidwwAuthError`).
- **API key.** `client.api_key` is read-only: the key is used when tokens are minted, so build a new `DidwwClient` to use another key.
- **Validation.** The constructor raises a `DidwwClientError` for an invalid API key, API version, scope, timeout or service URL (see [Configuration](#configuration)), which 3.x accepted.
- **Removed resources.** `client.pops()`, `client.did_group_types()` and the modules `didww.resources.pop` and `didww.resources.did_group_type` are removed, with the `did_group_type` relationship and include. `DidGroup`, `AddressRequirement`, `EmergencyRequirement` and `EmergencyCallingService` have `number_type` instead of `did_group_type`; filter with `number_type` instead of `did_group_type.id`, and with `did_group.number_type` on available DIDs.
- **Point of presence.** `VoiceInTrunk.pop` is the enum `didww.enums.Pop` (for example `Pop.FRA`), an attribute, no longer a relationship, and cannot be included.
- **Exact numbers.** Fractional JSON numbers in answers are `decimal.Decimal`, not `float` (see [Numbers](#numbers)), for example in `meta`, export `filters` and the attributes of unknown configurations or authentication methods. Integers are unchanged.
- **HTTP defaults.** 3.x set no timeouts, followed redirects and stored cookies. 4.x opens connections within 10 s, waits up to 60 s for each read, follows no redirects (a 3xx is an error), sends and stores no cookies, and ignores `~/.netrc` (see [HTTP session](#http-session-proxy-tls-timeouts)). Of a session you pass, `auth` and `max_redirects` are no longer copied, and `trust_env` now is.
- **Transport errors.** A connection failure, timeout or TLS error is no longer raised as a `requests` exception: the JSON:API, upload and export calls raise a `DidwwClientError` with the `requests` exception as its `__cause__`, the token service a `DidwwAuthError` and the prices services a `DidwwPricesError`.
- **Export download and file upload.** `download_export` and `download_and_decompress_export` take `dest` (a path or a binary file object) where 3.x named the parameter `file_path`. They download only from the API origin or the environment origin (a `DidwwClientError` otherwise, without a request), succeed only on a 200 (any other status, a 2xx or 3xx included, raises a `DidwwApiError` with the status and the parsed errors), write the file exactly as served, check it against its `Content-Length`, stream the decompression, and replace a destination path only once the file is complete. The new file gets the permissions of a new file and replaces a symlink at the path instead of following it, where 3.x wrote into the existing file at the path; to keep an existing file's permissions, pass a binary file object opened on it. `upload_encrypted_file` reports the errors of the answer in its `DidwwApiError` and also accepts a binary file object.
- **Exceptions.** `DidwwApiError` and `DidwwClientError` still derive from `DidwwError`, which is also the base of the new `DidwwAuthError` and `DidwwPricesError`.

New in 4.0.0: [SMS trunks](#sms-trunks), [SMS trunk groups](#sms-trunk-groups), [Sender ID verifications](#sender-id-verifications), [DID SMS routing](#sms-routing), `sms_in` and `sms_out` [exports](#exports), [prices](#prices), `DidGroup.is_demo`, `Identity.company_website`, unassigning a to-one relationship with `None`, and the `api_version`, `scope`, `token_store`, `logger`, timeout and service URL arguments of `DidwwClient`.

## Development

```bash
# Install the SDK with the test dependencies
pip install -e ".[dev]"

# Run the tests
pytest

# Compile the examples
python -m compileall -q examples

# Run an example (see examples/README.md)
DIDWW_API_KEY=your_api_key python examples/balance.py
```

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/didww/didww-api-3-python-sdk

### Build and Release

#### Preconditions
- prepare venv
- install build and twine packages

```shell
python3 -m pip install twine
python3 -m pip install build
```

#### 1. Change version in `pyproject.toml` to the new version (e.g. `4.0.0`)

#### 2. Build the package
```shell
python3 -m build --sdist
python3 -m build --wheel
```

#### 3. Check the package
```shell
twine check dist/*
```

#### 4. Publish new version to PyPI
```shell
twine upload dist/*
```

#### 5. Commit `pyproject.toml` and create tag
```shell
git add pyproject.toml
git commit -m "chore: bump version to 4.0.0"
git tag -a v4.0.0 -m "Release version 4.0.0"
```

#### 6. Push to GitHub

Push `main` for a 4.x release, or `release-3` for a 3.x patch release:

```shell
git push origin main --follow-tags
```

## License

The package is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
