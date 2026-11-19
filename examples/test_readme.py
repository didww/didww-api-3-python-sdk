"""
Runs the Python code snippets of the SDK's README (README.md at the repository
root) against the sandbox: one check per snippet, or per group of snippets
that belong together. A check that fails is reported with its error and the
run goes on. Each check deletes what it creates and puts back what it changes
(a DID's description, capacity limit and voice and SMS routing, the SMS trunk
of a Sender ID verification), also when it fails. Orders and exports cannot be
deleted: the order check buys DIDs. A snippet that cannot run in the sandbox
is reported as skipped with the reason.

The shell snippets (installation, development, release) are not run.

Ends with "Results: N passed, M failed" and exits with status 1 when a check
failed.

Usage: DIDWW_API_KEY=xxx python examples/test_readme.py
"""
import hashlib
import hmac
import itertools
import json
import logging
import math
import os
import sys
import tempfile
import uuid
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlsplit

import requests

from client_factory import create_client
from didww.auth import CACHE_KEY_PREFIX, AccessToken, MemoryTokenStore, TokenStore
from didww.callback.request_validator import RequestValidator
from didww.client import DidwwClient
from didww.configuration import Environment, Scope
from didww.encrypt import Encrypt
from didww.enums import (
    CallbackMethod,
    CliFormat,
    Codec,
    DefaultDstAction,
    ExportServiceType,
    ExportType,
    IceMode,
    IdentityType,
    NumberType,
    OnCliMismatchAction,
    Pop,
    SmsBodyType,
    SmsHttpMethod,
    TransportProtocol,
    VoiceOutCodec,
    enum_value,
    enum_value_list,
)
from didww.exceptions import (
    AuthErrorKind,
    DidwwApiError,
    DidwwAuthError,
    DidwwClientError,
    DidwwError,
    DidwwPricesError,
    PricesErrorKind,
)
from didww.prices import PriceFileReader, VoiceOutPriceCategory
from didww.query_params import QueryParams
from didww.resources.address import Address
from didww.resources.authentication_method import CredentialsAndIpAuthenticationMethod
from didww.resources.available_did import AvailableDid
from didww.resources.capacity_pool import CapacityPool
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.country import Country
from didww.resources.did import Did
from didww.resources.did_reservation import DidReservation
from didww.resources.export import Export
from didww.resources.identity import Identity
from didww.resources.order import Order
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.order_item.capacity_order_item import CapacityOrderItem
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem
from didww.resources.sender_id_verification import SenderIdVerification
from didww.resources.shared_capacity_group import SharedCapacityGroup
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import (
    HttpInConfiguration,
    HttpOutConfiguration,
    SmppEsmeConfiguration,
)
from didww.resources.sms_trunk_group import SmsTrunkGroup
from didww.resources.sms_trunk_regenerate_credential import SmsTrunkRegenerateCredential
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup
from didww.resources.voice_out_trunk import VoiceOutTrunk

client = create_client()
suffix = uuid.uuid4().hex[:8]
SAMPLE_PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.pdf")

passed = 0
failed = 0
failures = []
skipped = []


class Skip(Exception):
    """Raised by a check that cannot run in the sandbox; the message says why."""


def section(title):
    print(f"\n== {title} ==")


def check(name):
    """Runs the decorated function at once as the check ``name``, recording its outcome."""
    def run(fn):
        global passed, failed
        try:
            fn()
        except Skip as e:
            skipped.append(f"{name}: {e}")
            print(f"  - {name}: skipped, {e}")
        except Exception as e:  # a failed check must not stop the others
            failed += 1
            failures.append(f"{name}: {type(e).__name__}: {e}")
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
        else:
            passed += 1
            print(f"  ✓ {name}")
        return fn
    return run


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


# --- Fixtures: created per check and removed by its ExitStack ---

def delete(repository, resource_id, what):
    """Deletes a resource; a 404 means it is gone already, e.g. deleted with its group."""
    try:
        repository.delete(resource_id)
    except DidwwApiError as e:
        if e.status_code != 404:
            raise
    print(f"    deleted {what} {resource_id}")


def new_sip_trunk(cleanup, name):
    sip = SipConfiguration()
    sip.host = "sip.example.com"
    sip.port = 5060
    sip.codecs = [Codec.PCMU, Codec.PCMA]
    sip.transport_protocol_id = TransportProtocol.UDP
    trunk = VoiceInTrunk()
    trunk.name = f"{name} {suffix}"
    trunk.configuration = sip
    created = client.voice_in_trunks().create(trunk).data
    cleanup.callback(delete, client.voice_in_trunks(), created.id, "Voice IN trunk")
    return created


def new_http_in_trunk(cleanup, name):
    http_in = HttpInConfiguration()
    http_in.url = "https://example.com/sms"
    http_in.http_method = SmsHttpMethod.GET  # GET takes no body type and no body
    http_in.query_parameters = {"text": "{SMS_TEXT}", "from": "{SMS_SRC_ADDR}"}
    trunk = SmsTrunk()
    trunk.name = f"{name} {suffix}"
    trunk.configuration = http_in
    created = client.sms_trunks().create(trunk).data
    cleanup.callback(delete, client.sms_trunks(), created.id, "SMS trunk")
    return created


def new_http_out_trunk(cleanup, name):
    http_out = HttpOutConfiguration()
    http_out.callback_url = "https://example.com/sms/status"
    http_out.allowed_ips = ["203.0.113.10"]
    trunk = SmsTrunk()
    trunk.name = f"{name} {suffix}"
    trunk.configuration = http_out
    created = client.sms_trunks().create(trunk).data
    cleanup.callback(delete, client.sms_trunks(), created.id, "SMS trunk")
    return created


_us = []


def us_country():
    if not _us:
        _us.extend(client.countries().list(QueryParams().filter("iso", "US")).data)
    return _us[0]


def new_identity(cleanup, identity_type=IdentityType.PERSONAL):
    identity = Identity()
    identity.first_name = "John"
    identity.last_name = "Doe"
    identity.phone_number = "12125551234"
    identity.identity_type = identity_type
    if identity_type == IdentityType.BUSINESS:
        identity.company_name = f"Example Inc {suffix}"
    identity.country = Country.build(us_country().id)
    created = client.identities().create(identity).data
    cleanup.callback(delete, client.identities(), created.id, "identity")
    return created


def new_address(cleanup, identity):
    address = Address()
    address.city_name = "New York"
    address.postal_code = "10001"
    address.address = "123 Main St"
    address.identity = Identity.build(identity.id)
    address.country = Country.build(us_country().id)
    created = client.addresses().create(address).data
    cleanup.callback(delete, client.addresses(), created.id, "address")
    return created


def a_did():
    """An active DID of the account, read with its voice and SMS routing."""
    params = (QueryParams()
              .filter("terminated", "false")
              .filter("blocked", "false")
              .include("voice_in_trunk", "voice_in_trunk_group", "sms_trunk", "sms_trunk_group")
              .page(number=1, size=1))
    dids = client.dids().list(params).data
    if not dids:
        raise Skip("the account has no active DID; order one first, e.g. with examples/orders_sku.py")
    return dids[0]


def restore_did(did):
    """Puts back the description, capacity limit and routing that ``did`` was read with."""
    restore = Did.build(did.id)
    restore.description = did.description
    restore.capacity_limit = did.capacity_limit
    # None unassigns only that relationship, so both of a pair are set to unroute
    if did.voice_in_trunk:
        restore.voice_in_trunk = VoiceInTrunk.build(did.voice_in_trunk.id)
    elif did.voice_in_trunk_group:
        restore.voice_in_trunk_group = VoiceInTrunkGroup.build(did.voice_in_trunk_group.id)
    else:
        restore.voice_in_trunk = None
        restore.voice_in_trunk_group = None
    if did.sms_trunk:
        restore.sms_trunk = SmsTrunk.build(did.sms_trunk.id)
    elif did.sms_trunk_group:
        restore.sms_trunk_group = SmsTrunkGroup.build(did.sms_trunk_group.id)
    else:
        restore.sms_trunk = None
        restore.sms_trunk_group = None
    client.dids().update(restore)
    print(f"    restored DID {did.number}")


def no_price_plan(error):
    return isinstance(error, DidwwPricesError) and error.kind == PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED


def sign(secret, url, payload):
    """Signs a callback the way DIDWW does (see examples/webhook.py)."""
    parts = urlsplit(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    query = f"?{parts.query}" if parts.query else ""
    data = f"{parts.scheme}://{parts.hostname}:{port}{parts.path}{query}"
    for key in sorted(payload):
        data += key + payload[key]
    return hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).hexdigest()


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


# ─── Usage ─────────────────────────────────────────────────

section("Usage")


@check("Usage: balance and DID groups with stock keeping units")
def _():
    balance = client.balance().find().data
    print(f"    Balance: {balance.total_balance}")
    params = QueryParams().include("stock_keeping_units").filter("area_name", "Acapulco")
    did_groups = client.did_groups().list(params).data
    print(f"    {len(did_groups)} DID group(s) in Acapulco")


# ─── Configuration ─────────────────────────────────────────

section("Configuration")


@check("Configuration: production client (built only) and read-only sandbox client")
def _():
    # Production: built to check its settings, no request is sent
    production = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.PRODUCTION)
    expect(production.base_url == "https://api.didww.com/v3", f"base_url is {production.base_url}")
    expect(production.auth_url == "https://auth.didww.com", f"auth_url is {production.auth_url}")
    sandbox = create_client(
        scope=Scope.READ,
        logger=logging.getLogger("myapp.didww"),
        connect_timeout=5,
    )
    expect(sandbox.scope == Scope.READ, f"scope is {sandbox.scope}")
    print(f"    read-only sandbox client, balance: {sandbox.balance().find().data.total_balance}")


@check("HTTP session: a requests.Session of your own")
def _():
    # The README's proxy and CA bundle are placeholders: that client is built only
    session = requests.Session()
    session.proxies = {"https": "http://proxy.example.com:8080"}
    session.verify = "/etc/ssl/certs/my-ca-bundle.pem"
    DidwwClient(api_key="YOUR_API_KEY", environment=Environment.PRODUCTION, session=session)
    # A session without them carries the sandbox calls
    own = requests.Session()
    own.verify = True
    with create_client(session=own) as session_client:
        print(f"    balance through the session: {session_client.balance().find().data.total_balance}")


# ─── Authentication ────────────────────────────────────────

section("Authentication")


@check("Scope: a read-only client reads, a write is refused with 403")
def _():
    read_only = create_client(scope=Scope.READ)  # GET and HEAD only; Scope.FULL allows every method
    print(f"    balance: {read_only.balance().find().data.total_balance}")
    group = VoiceInTrunkGroup()
    group.name = f"README read-only write {suffix}"
    try:
        created = read_only.voice_in_trunk_groups().create(group).data
    except DidwwApiError as e:
        expect(e.status_code == 403, f"expected 403, got {e.status_code}: {e}")
        print(f"    write refused: HTTP {e.status_code} {e}")
    else:
        delete(client.voice_in_trunk_groups(), created.id, "Voice IN trunk group")
        raise AssertionError("a write with a READ token was accepted")


@check("Token cache: a token store with get, set and delete")
def _():
    class MyTokenStore:
        def __init__(self):
            self.tokens = {}

        def get(self, key: str) -> Optional[AccessToken]:
            """The token stored under key, or None when there is none or it has expired."""
            return self.tokens.get(key)

        def set(self, key: str, token: AccessToken, ttl: float) -> None:
            """Store token under key for ttl seconds; ttl <= 0 means no expiry."""
            self.tokens[key] = token

        def delete(self, key: str) -> None:
            """Remove the token stored under key, if any."""
            self.tokens.pop(key, None)

    store = MyTokenStore()
    store_client = create_client(token_store=store)
    store_client.balance().find()
    expect(len(store.tokens) == 1, f"{len(store.tokens)} tokens stored")
    key, token = next(iter(store.tokens.items()))
    expect(key.startswith(CACHE_KEY_PREFIX), "the key starts with the cache key prefix")
    expect("[FILTERED]" in repr(token), "repr() of a token masks it")
    print(f"    stored {token!r}")


@check("Token cache: RedisTokenStore (with an in-memory stand-in for redis.Redis)")
def _():
    # The README's class as written; redis-py and a Redis server are not needed here.
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

    class FakeRedis:
        """The three calls of redis.Redis the store makes, kept in a dict."""

        def __init__(self):
            self.values = {}
            self.expiries = {}

        def get(self, key):
            return self.values.get(key)

        def set(self, key, value, ex=None):
            self.values[key] = value.encode("utf-8")
            self.expiries[key] = ex

        def delete(self, key):
            self.values.pop(key, None)

    redis = FakeRedis()
    store = RedisTokenStore(redis)
    redis_client = create_client(token_store=store)
    redis_client.balance().find()
    redis_client.balance().find()  # the second call reads the token back from the store
    expect(len(redis.values) == 1, f"{len(redis.values)} tokens stored")
    expiry = next(iter(redis.expiries.values()))
    expect(expiry is not None and expiry > 0, f"expiry is {expiry}")
    print(f"    one token stored for {expiry} s")


@check("Logging: the didww logger at DEBUG")
def _():
    root = logging.getLogger()
    root_handlers = list(root.handlers)
    didww_logger = logging.getLogger("didww")
    captured = ListHandler()
    didww_logger.addHandler(captured)
    try:
        logging.basicConfig()
        logging.getLogger("didww").setLevel(logging.DEBUG)
        # A token store of its own makes the client mint a token, which is logged
        create_client(token_store=MemoryTokenStore()).balance().find()
    finally:
        didww_logger.setLevel(logging.NOTSET)
        didww_logger.removeHandler(captured)
        for handler in list(root.handlers):
            if handler not in root_handlers:
                root.removeHandler(handler)
    minted = [m for m in captured.messages if m.startswith("DIDWW token minted")]
    expect(minted, f"no mint event logged: {captured.messages}")
    print(f"    {minted[0]}")


@check("Logging: a logger of your own")
def _():
    logger = logging.getLogger("myapp.didww")
    captured = ListHandler()
    logger.addHandler(captured)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    try:
        logged_client = create_client(logger=logger, token_store=MemoryTokenStore())
        logged_client.balance().find()
    finally:
        logger.removeHandler(captured)
        logger.setLevel(logging.NOTSET)
        logger.propagate = True
    expect(any(m.startswith("DIDWW token minted") for m in captured.messages),
           f"no mint event logged: {captured.messages}")
    print(f"    {len(captured.messages)} event(s) logged to myapp.didww")


# ─── Read-only resources ───────────────────────────────────

section("Read-only resources")


@check("Read-only resources")
def _():
    countries = client.countries().list().data
    country = client.countries().find(countries[0].id).data
    regions = client.regions().list().data
    cities = client.cities().list().data
    areas = client.areas().list().data
    prefixes = client.nanpa_prefixes().list().data
    params = QueryParams().include("stock_keeping_units").filter("number_type", "toll_free")
    groups = client.did_groups().list(params).data
    params = QueryParams().include("did_group.stock_keeping_units")
    available = client.available_dids().list(params).data
    proof_types = client.proof_types().list().data
    public_keys = client.public_keys().list().data
    requirements = client.address_requirements().list().data
    templates = client.supporting_document_templates().list().data
    balance = client.balance().find().data
    expect(country.id == countries[0].id, "find returns the country")
    expect(public_keys, "no public keys")
    print(f"    {len(countries)} countries, {len(regions)} regions, {len(cities)} cities, {len(areas)} areas,"
          f" {len(prefixes)} NANPA prefixes, {len(groups)} toll-free DID groups, {len(available)} available DIDs,"
          f" {len(proof_types)} proof types, {len(public_keys)} public keys, {len(requirements)} address"
          f" requirements, {len(templates)} document templates, balance {balance.total_balance}")


@check("Number type of a DID group")
def _():
    groups = client.did_groups().list(QueryParams().filter("number_type", "toll_free").page(number=1, size=1)).data
    if not groups:
        raise Skip("no toll-free DID group in the sandbox")
    group = client.did_groups().find(groups[0].id).data
    expect(group.number_type == NumberType.TOLL_FREE, f"number_type is {group.number_type!r}")
    if group.number_type == NumberType.TOLL_FREE and not group.is_demo:
        print(f"    {group.number_type.value}")  # "toll_free"
    print(f"    {group.prefix} {group.area_name}: is_demo={group.is_demo}")


@check("Mandatory fields of an address requirement")
def _():
    requirements = client.address_requirements().list(QueryParams().page(number=1, size=1)).data
    if not requirements:
        raise Skip("no address requirement in the sandbox")
    requirement = client.address_requirements().find(requirements[0].id).data
    expect(isinstance(requirement.business_mandatory_fields, list), "business_mandatory_fields is a list")
    if "tax_id" in requirement.business_mandatory_fields:
        print("    The business identity needs its vat_id")
    print(f"    personal: {requirement.personal_mandatory_fields}, business: {requirement.business_mandatory_fields}")


# ─── DIDs ──────────────────────────────────────────────────

section("DIDs")


@check("DIDs: list, then assign a trunk and capacity to a DID")
def _():
    dids = client.dids().list().data
    print(f"    {len(dids)} DID(s)")
    with ExitStack() as cleanup:
        original = a_did()
        trunk = new_sip_trunk(cleanup, "README DID trunk")
        cleanup.callback(restore_did, original)  # runs before the trunk is deleted

        did = client.dids().find(original.id).data
        did.description = "Updated"
        did.capacity_limit = 20
        did.voice_in_trunk = VoiceInTrunk.build(trunk.id)
        client.dids().update(did)

        updated = client.dids().find(original.id, QueryParams().include("voice_in_trunk")).data
        expect(updated.voice_in_trunk and updated.voice_in_trunk.id == trunk.id, "the trunk is assigned")
        expect(updated.capacity_limit == 20, f"capacity_limit is {updated.capacity_limit}")
        print(f"    {updated.number}: trunk {updated.voice_in_trunk.name}, capacity limit {updated.capacity_limit}")


@check("SMS routing: SMS trunk, SMS trunk group, unroute, DIDs by SMS trunk")
def _():
    with ExitStack() as cleanup:
        original = a_did()
        trunk = new_http_in_trunk(cleanup, "README SMS route")
        member = new_http_in_trunk(cleanup, "README SMS group member")
        group = SmsTrunkGroup()
        group.name = f"README SMS routing {suffix}"
        group.sms_trunks = [SmsTrunk.build(member.id)]
        group = client.sms_trunk_groups().create(group).data
        cleanup.callback(delete, client.sms_trunk_groups(), group.id, "SMS trunk group")
        cleanup.callback(restore_did, original)
        routing = QueryParams().include("sms_trunk", "sms_trunk_group")

        def routed():
            did = client.dids().find(original.id, routing).data
            return (did.sms_trunk.id if did.sms_trunk else None,
                    did.sms_trunk_group.id if did.sms_trunk_group else None)

        # sends sms_trunk and sms_trunk_group: null
        route = Did.build(original.id)
        route.sms_trunk = SmsTrunk.build(trunk.id)
        client.dids().update(route)
        expect(routed() == (trunk.id, None), f"routed to {routed()}")

        # sends sms_trunk_group and sms_trunk: null
        to_group = Did.build(original.id)
        to_group.sms_trunk_group = SmsTrunkGroup.build(group.id)
        client.dids().update(to_group)
        expect(routed() == (None, group.id), f"routed to {routed()}")

        # unroute: sends sms_trunk: null and sms_trunk_group: null
        unroute = Did.build(original.id)
        unroute.sms_trunk = None
        unroute.sms_trunk_group = None
        client.dids().update(unroute)
        expect(routed() == (None, None), f"routed to {routed()}")

        params = QueryParams().filter("sms_trunk.id", trunk.id).include("sms_trunk", "sms_trunk_group")
        dids = client.dids().list(params).data
        print(f"    {len(dids)} DID(s) routed to the SMS trunk after unrouting")


@check("Dirty serialization")
def _():
    with ExitStack() as cleanup:
        original = a_did()
        trunk = new_sip_trunk(cleanup, "README dirty")
        cleanup.callback(restore_did, original)

        # Only "description" is sent in the PATCH body
        did = client.dids().find(original.id).data
        did.description = "Updated"
        sent = did.to_jsonapi(include_id=True, dirty_only=True)
        expect(sent["attributes"] == {"description": "Updated"} and "relationships" not in sent, f"sent {sent}")
        client.dids().update(did)

        # Explicit None sends null to clear a field
        did = Did.build(original.id)
        did.description = None
        client.dids().update(did)
        expect(client.dids().find(original.id).data.description is None, "the description is cleared")

        # Exclusive relationships: setting voice_in_trunk automatically nullifies voice_in_trunk_group
        did = Did.build(original.id)
        did.voice_in_trunk = VoiceInTrunk.build(trunk.id)
        sent = did.to_jsonapi(include_id=True, dirty_only=True)
        expect(sent["relationships"]["voice_in_trunk_group"] == {"data": None}, f"sent {sent}")
        client.dids().update(did)

        # None unassigns a to-one relationship: sends only "voice_in_trunk": {"data": null}
        did = Did.build(original.id)
        did.voice_in_trunk = None
        sent = did.to_jsonapi(include_id=True, dirty_only=True)
        expect(sent["relationships"] == {"voice_in_trunk": {"data": None}}, f"sent {sent}")
        client.dids().update(did)

        # Included resources also support dirty tracking (the DID is routed to the
        # trunk of this check first, so that only that trunk is changed)
        assign = Did.build(original.id)
        assign.voice_in_trunk = VoiceInTrunk.build(trunk.id)
        client.dids().update(assign)
        params = QueryParams().include("voice_in_trunk")
        did = client.dids().find(original.id, params).data
        included_trunk = did.voice_in_trunk
        included_trunk.description = "Updated via include"
        client.voice_in_trunks().update(included_trunk)
        expect(client.voice_in_trunks().find(trunk.id).data.description == "Updated via include",
               "the included trunk is updated")


# ─── Voice IN trunks ───────────────────────────────────────

section("Voice IN trunks")


@check("Voice IN trunks: create a SIP trunk, update, delete")
def _():
    trunk = VoiceInTrunk()
    trunk.name = f"My SIP Trunk {suffix}"
    trunk.priority = 1
    trunk.weight = 100
    trunk.cli_format = CliFormat.E164
    trunk.ringing_timeout = 30
    trunk.pop = Pop.FRA  # optional; None lets DIDWW choose

    sip = SipConfiguration()
    sip.host = "sip.example.com"
    sip.port = 5060
    sip.codecs = [Codec.PCMA, Codec.PCMU, Codec.TELEPHONE_EVENT]  # priority order
    sip.ice_mode = IceMode.ACCEPT
    sip.transport_protocol_id = TransportProtocol.UDP
    trunk.configuration = sip

    created = client.voice_in_trunks().create(trunk).data
    deleted = False
    try:
        expect(created.pop == Pop.FRA, f"pop is {created.pop!r}")
        expect(enum_value_list(created.configuration.codecs) == ["pcma", "pcmu", "telephone_event"],
               f"codecs are {enum_value_list(created.configuration.codecs)}")
        print(f"    created {created.id}")

        # Update trunk
        created.description = "Updated"
        client.voice_in_trunks().update(created)
        expect(client.voice_in_trunks().find(created.id).data.description == "Updated", "description updated")

        # Delete trunk
        client.voice_in_trunks().delete(created.id)
        deleted = True
        print("    deleted")
    finally:
        if not deleted:
            delete(client.voice_in_trunks(), created.id, "Voice IN trunk")


@check("Voice IN trunks: codecs of a fetched trunk")
def _():
    with ExitStack() as cleanup:
        trunk_id = new_sip_trunk(cleanup, "README codecs").id

        trunk = client.voice_in_trunks().find(trunk_id).data
        sip = trunk.configuration
        sip.codecs = [Codec.G729, Codec.PCMA]
        trunk.configuration = sip
        client.voice_in_trunks().update(trunk)

        codecs = enum_value_list(client.voice_in_trunks().find(trunk_id).data.configuration.codecs)
        expect(codecs == ["g729", "pcma"], f"codecs are {codecs}")
        print(f"    codecs: {codecs}")


@check("Voice IN trunks: point of presence")
def _():
    with ExitStack() as cleanup:
        trunk_id = new_sip_trunk(cleanup, "README pop").id

        pop_update = VoiceInTrunk.build(trunk_id)
        pop_update.pop = Pop.AMS
        client.voice_in_trunks().update(pop_update)

        pop = client.voice_in_trunks().find(trunk_id).data.pop
        expect(pop == Pop.AMS, f"pop is {pop!r}")
        print(f"    pop: {enum_value(pop)}")


@check("SIP registration: create with registration, disable by setting host")
def _():
    with ExitStack() as cleanup:
        sip = SipConfiguration()
        sip.enabled_sip_registration = True
        sip.use_did_in_ruri = True
        sip.cnam_lookup = True

        trunk = VoiceInTrunk()
        trunk.name = f"Office (registered) {suffix}"
        trunk.configuration = sip
        created = client.voice_in_trunks().create(trunk).data
        cleanup.callback(delete, client.voice_in_trunks(), created.id, "Voice IN trunk")

        # created.configuration.incoming_auth_username — server-generated
        # created.configuration.incoming_auth_password — server-generated
        expect(created.configuration.incoming_auth_username, "no incoming_auth_username")
        expect(created.configuration.incoming_auth_password, "no incoming_auth_password")

        disable = SipConfiguration()
        disable.host = "sip.example.com"

        trunk = VoiceInTrunk()
        trunk.id = created.id
        trunk.configuration = disable
        client.voice_in_trunks().update(trunk)

        fresh = client.voice_in_trunks().find(created.id).data.configuration
        expect(fresh.enabled_sip_registration is False, f"enabled_sip_registration is {fresh.enabled_sip_registration}")
        print(f"    registration disabled, host {fresh.host}")


@check("Voice IN trunk groups: create")
def _():
    group = VoiceInTrunkGroup()
    group.name = f"Primary Group {suffix}"
    group.capacity_limit = 50
    created = client.voice_in_trunk_groups().create(group).data
    try:
        expect(created.capacity_limit == 50, f"capacity_limit is {created.capacity_limit}")
        print(f"    created {created.id}")
    finally:
        delete(client.voice_in_trunk_groups(), created.id, "Voice IN trunk group")


# ─── Voice OUT trunks ──────────────────────────────────────

section("Voice OUT trunks")


@check("Voice OUT trunks: create with credentials_and_ip")
def _():
    trunk = VoiceOutTrunk()
    trunk.name = f"My Outbound Trunk {suffix}"
    trunk.authentication_method = CredentialsAndIpAuthenticationMethod(
        allowed_sip_ips=["203.0.113.0/24"],
    )
    trunk.default_dst_action = DefaultDstAction.ALLOW_ALL
    trunk.on_cli_mismatch_action = OnCliMismatchAction.REJECT_CALL
    trunk.codecs = [VoiceOutCodec.OPUS, VoiceOutCodec.PCMA, VoiceOutCodec.TELEPHONE_EVENT]
    try:
        created = client.voice_out_trunks().create(trunk).data
    except DidwwApiError as e:
        if e.status_code == 403:
            raise Skip(f"Voice OUT trunks are not enabled for the account, DIDWW support enables them ({e})") from None
        raise
    try:
        auth = created.authentication_method
        expect(isinstance(auth, CredentialsAndIpAuthenticationMethod), f"authentication method is {auth!r}")
        expect(auth.username and auth.password, "username and password are server-generated")
        expect(enum_value_list(created.codecs) == ["opus", "pcma", "telephone_event"],
               f"codecs are {enum_value_list(created.codecs)}")
        print(f"    created {created.id}")
    finally:
        delete(client.voice_out_trunks(), created.id, "Voice OUT trunk")


# ─── SMS trunks ────────────────────────────────────────────

section("SMS trunks")


@check("SMS trunks: HTTP IN trunk, update, clear, list by type")
def _():
    with ExitStack() as cleanup:
        http_in = HttpInConfiguration()
        http_in.url = "https://example.com/sms"
        http_in.http_method = SmsHttpMethod.POST
        http_in.body_type = SmsBodyType.JSON
        http_in.body = '{"text":"{SMS_TEXT}","from":"{SMS_SRC_ADDR}","to":"{SMS_DST_ADDR}"}'

        trunk = SmsTrunk()
        trunk.name = f"Inbound webhook {suffix}"
        trunk.configuration = http_in
        created = client.sms_trunks().create(trunk).data
        cleanup.callback(delete, client.sms_trunks(), created.id, "SMS trunk")
        expect(created.allow_in, "the trunk accepts inbound messages")

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

        config = client.sms_trunks().find(created.id).data.configuration
        expect(config.url == "https://example.com/sms/v2", f"url is {config.url}")
        expect(config.http_method == SmsHttpMethod.GET and config.body is None, f"configuration is {config!r}")

        # List by configuration type, with the group
        params = QueryParams().filter("configuration.type", "http_in,sms_to_email").include("sms_trunk_group")
        trunks = client.sms_trunks().list(params).data
        expect(all(t.configuration is not None and t.configuration.type in ("http_in", "sms_to_email")
                   for t in trunks),
               "the list holds other configuration types")
        print(f"    {len(trunks)} http_in or sms_to_email trunk(s) on the first page")
        # A list call returns one page: narrow it by name to find the new trunk on any account
        params = QueryParams().filter("configuration.type", "http_in,sms_to_email").filter("name", created.name)
        expect(any(t.id == created.id for t in client.sms_trunks().list(params).data), "the new trunk is listed")


@check("SMS trunks: a configuration is a copy, sent once assigned back")
def _():
    with ExitStack() as cleanup:
        trunk_id = new_http_in_trunk(cleanup, "README configuration copy").id

        trunk = client.sms_trunks().find(trunk_id).data
        configuration = trunk.configuration  # a copy
        configuration.url = "https://example.com/sms/v3"
        trunk.configuration = configuration  # sent by the next update
        client.sms_trunks().update(trunk)

        url = client.sms_trunks().find(trunk_id).data.configuration.url
        expect(url == "https://example.com/sms/v3", f"url is {url}")
        print(f"    url: {url}")


@check("SMS trunks: regenerate the credentials of an HTTP OUT trunk")
def _():
    with ExitStack() as cleanup:
        trunk_id = new_http_out_trunk(cleanup, "README regenerate").id

        regenerate = SmsTrunkRegenerateCredential()
        regenerate.sms_trunk = SmsTrunk.build(trunk_id)
        client.sms_trunk_regenerate_credentials().create(regenerate)

        # The response carries no credentials: read the trunk again
        out_trunk = client.sms_trunks().find(trunk_id).data
        configuration = out_trunk.configuration
        if isinstance(configuration, HttpOutConfiguration):
            expect(configuration.auth_name and configuration.auth_password, "no credentials")
        elif isinstance(configuration, SmppEsmeConfiguration):
            expect(configuration.system_id and configuration.password, "no credentials")
        else:
            raise AssertionError(f"configuration is {configuration!r}")
        print(f"    credentials regenerated, submit URL {out_trunk.host}")


@check("SMS trunk groups: create with a trunk")
def _():
    with ExitStack() as cleanup:
        trunk_id = new_http_in_trunk(cleanup, "README group").id

        group = SmsTrunkGroup()
        group.name = f"Inbound SMS {suffix}"
        group.sms_trunks = [SmsTrunk.build(trunk_id)]
        created = client.sms_trunk_groups().create(group).data
        cleanup.callback(delete, client.sms_trunk_groups(), created.id, "SMS trunk group")
        expect(created.sms_trunks_count == 1, f"sms_trunks_count is {created.sms_trunks_count}")
        print(f"    {created.sms_trunks_count} trunk in the group")


@check("SMS trunk groups: replace and clear the membership")
def _():
    with ExitStack() as cleanup:
        first_id = new_http_in_trunk(cleanup, "README member 1").id
        another_id = new_http_in_trunk(cleanup, "README member 2").id
        group = SmsTrunkGroup()
        group.name = f"README membership {suffix}"
        group.sms_trunks = [SmsTrunk.build(first_id)]
        group_id = client.sms_trunk_groups().create(group).data.id
        cleanup.callback(delete, client.sms_trunk_groups(), group_id, "SMS trunk group")

        current = client.sms_trunk_groups().find(
            group_id, QueryParams().include("sms_trunks")
        ).data
        members = list(current.sms_trunks or [])
        members.append(SmsTrunk.build(another_id))

        update = SmsTrunkGroup.build(group_id)
        update.sms_trunks = members
        client.sms_trunk_groups().update(update)
        count = client.sms_trunk_groups().find(group_id).data.sms_trunks_count
        expect(count == 2, f"sms_trunks_count is {count}")

        # An empty list (or None) removes every trunk from the group
        empty = SmsTrunkGroup.build(group_id)
        empty.sms_trunks = []
        client.sms_trunk_groups().update(empty)
        count = client.sms_trunk_groups().find(group_id).data.sms_trunks_count
        expect(count == 0, f"sms_trunks_count is {count}")
        print("    2 trunks, then none")


@check("Sender ID verifications: list active, route and unroute")
def _():
    params = QueryParams().filter("status", "active").include("sms_trunk")
    verifications = client.sender_id_verifications().list(params).data
    print(f"    {len(verifications)} active verification(s)")
    if not verifications:
        raise Skip("no active Sender ID verification on the account; they are created outside the API")
    original = verifications[0]

    def restore():
        back = SenderIdVerification.build(original.id)
        back.sms_trunk = SmsTrunk.build(original.sms_trunk.id) if original.sms_trunk else None
        client.sender_id_verifications().update(back)
        print(f"    restored the SMS trunk of {original.reference}")

    with ExitStack() as cleanup:
        trunk_id = new_http_out_trunk(cleanup, "README sender ID").id
        cleanup.callback(restore)  # runs before the trunk is deleted

        # http_out, smpp_esme or smpp_smsc trunks only
        route = SenderIdVerification.build(verifications[0].id)
        route.sms_trunk = SmsTrunk.build(trunk_id)
        client.sender_id_verifications().update(route)

        # Outbound messages stop until a trunk is assigned again
        unroute = SenderIdVerification.build(verifications[0].id)
        unroute.sms_trunk = None
        client.sender_id_verifications().update(unroute)

        reread = client.sender_id_verifications().find(original.id, QueryParams().include("sms_trunk")).data
        expect(reread.sms_trunk is None, "the verification is unrouted")


# ─── Orders and capacity ───────────────────────────────────

section("Orders and capacity")


@check("Orders: order by SKU; build the other item types")
def _():
    groups = client.did_groups().list(QueryParams().include("stock_keeping_units").page(number=1, size=10)).data
    group = next((g for g in groups if g.stock_keeping_units), None)
    if group is None:
        raise Skip("no DID group with stock keeping units")

    # Order by SKU
    order = Order()
    item = DidOrderItem()
    item.sku_id = group.stock_keeping_units[0].id
    item.qty = 2
    order.items = [item]
    created = client.orders().create(order).data
    print(f"    order {created.reference}: {enum_value(created.status)}, amount {created.amount}")

    # The other item types, built only (orders_all_item_types.py sends them)
    item = AvailableDidOrderItem()
    item.available_did_id = "available-did-uuid"
    item.sku_id = "sku-uuid"
    expect(item.to_jsonapi()["type"] == "did_order_items", "an available DID item is a did_order_items")

    item = ReservationDidOrderItem()
    item.did_reservation_id = "reservation-uuid"
    item.sku_id = "sku-uuid"
    expect(item.to_jsonapi()["type"] == "did_order_items", "a reserved DID item is a did_order_items")

    item = CapacityOrderItem()
    item.capacity_pool_id = "pool-uuid"
    item.qty = 1
    expect(item.to_jsonapi()["type"] == "capacity_order_items", "a capacity item is a capacity_order_items")


@check("DID reservations: create, list by expiry, delete")
def _():
    available = client.available_dids().list(QueryParams().page(number=1, size=1)).data
    if not available:
        raise Skip("no available DID in the sandbox")

    reservation = DidReservation()
    reservation.description = "Reserved for client"
    reservation.available_did = AvailableDid.build(available[0].id)
    created = client.did_reservations().create(reservation).data
    try:
        expect(isinstance(created.expires_at, datetime), f"expires_at is {created.expires_at!r}")
        print(f"    reserved {available[0].number} until {created.expires_at}")

        # The reservations that expire first
        reservations = client.did_reservations().list(QueryParams().sort("expires_at")).data
        expiries = [r.expires_at for r in reservations if r.expires_at is not None]
        expect(expiries == sorted(expiries), "the reservations are not sorted by expiry")
        # A list call returns one page, where a new reservation can be missing: read it by ID
        expect(client.did_reservations().find(created.id).data.id == created.id, "the reservation is found")
        print(f"    {len(reservations)} reservation(s) on the first page, the first expires at"
              f" {expiries[0] if expiries else None}")
    finally:
        # Delete reservation
        delete(client.did_reservations(), created.id, "DID reservation")


@check("Shared capacity groups: create")
def _():
    pools = client.capacity_pools().list().data
    if not pools:
        raise Skip("the account has no capacity pool")
    scg = SharedCapacityGroup()
    scg.name = f"Shared Group {suffix}"
    scg.shared_channels_count = 1  # the README uses 20; 1 fits a sandbox pool with few channels
    scg.metered_channels_count = 5
    scg.capacity_pool = CapacityPool.build(pools[0].id)
    created = client.shared_capacity_groups().create(scg).data
    try:
        print(f"    created {created.id} in {pools[0].name}")
    finally:
        delete(client.shared_capacity_groups(), created.id, "shared capacity group")


# ─── Verifications and emergency ───────────────────────────

section("Verifications and emergency")


@check("Address verifications: list")
def _():
    verifications = client.address_verifications().list().data
    print(f"    {len(verifications)} address verification(s)")


@check("Address verifications: create and update external_reference_id")
def _():
    raise Skip("needs a DID that requires an address and an address with its proofs; "
               "DIDWW reviews the request and it cannot be deleted")


@check("Emergency requirements: list and find")
def _():
    emergency_reqs = client.emergency_requirements().list().data
    for req in emergency_reqs:
        print(f"    {req.id}: {req.identity_type}, setup {req.estimate_setup_time}")
    if emergency_reqs:
        req = client.emergency_requirements().find(emergency_reqs[0].id).data
        print(f"    found {req.id}")


@check("Emergency verifications: list")
def _():
    verifications = client.emergency_verifications().list().data
    print(f"    {len(verifications)} emergency verification(s)")


@check("Emergency verifications: create and update external_reference_id")
def _():
    raise Skip("needs a DID with emergency calling and an address that meets its requirement; "
               "DIDWW reviews the request and it cannot be deleted")


@check("Emergency calling services: list and find")
def _():
    services = client.emergency_calling_services().list().data
    for svc in services:
        print(f"    Status: {svc.status}, Renew: {svc.renew_date}")
    if services:
        service = client.emergency_calling_services().find(services[0].id).data
        print(f"    found {service.id}")


@check("Emergency calling services: delete")
def _():
    raise Skip("deleting cancels an emergency calling service of the account, which cannot be undone")


@check("DID history: list for a DID and find")
def _():
    dids = client.dids().list(QueryParams().page(number=1, size=1)).data
    if not dids:
        raise Skip("the account has no DID")
    params = QueryParams().filter("did_number", dids[0].number)
    history = client.did_history().list(params).data
    for record in history:
        print(f"    {record.created_at} {record.did_number}: {record.action} ({record.method})")
    if history:
        record = client.did_history().find(history[0].id).data
        print(f"    found {record.id}")


# ─── Identities, addresses, exports ────────────────────────

section("Identities, addresses, exports")


@check("Identities: create a personal identity")
def _():
    with ExitStack() as cleanup:
        created = new_identity(cleanup)
        expect(created.identity_type == IdentityType.PERSONAL, f"identity_type is {created.identity_type!r}")
        print(f"    created {created.id}")


@check("Identities: company_website of a business identity")
def _():
    with ExitStack() as cleanup:
        identity_id = new_identity(cleanup, IdentityType.BUSINESS).id

        business = Identity.build(identity_id)
        business.company_website = "https://www.example.com"
        client.identities().update(business)

        website = client.identities().find(identity_id).data.company_website
        expect(website == "https://www.example.com", f"company_website is {website}")
        print(f"    company_website: {website}")


@check("Addresses: create")
def _():
    with ExitStack() as cleanup:
        created = new_address(cleanup, new_identity(cleanup))
        print(f"    created {created.id}: {created.address}, {created.city_name}")


@check("Exports: CDR IN and SMS OUT exports")
def _():
    with ExitStack() as cleanup:
        sms_trunk_id = new_http_out_trunk(cleanup, "README export").id

        # Dates are "YYYY-MM-DD HH:MM:SS" in UTC: from is inclusive, to is exclusive and not in the future
        today = datetime.now(timezone.utc).date()
        date_from = f"{today - timedelta(days=1)} 00:00:00"
        date_to = f"{today} 00:00:00"

        export = Export()
        export.export_type = ExportType.CDR_IN
        export.filters = {"from": date_from, "to": date_to}
        created = client.exports().create(export).data
        print(f"    CDR IN export {created.id}: {enum_value(created.status)}")

        # SMS export
        sms_out = Export()
        sms_out.export_type = ExportType.SMS_OUT
        sms_out.filters = {
            "from": date_from,
            "to": date_to,
            "service_type": ExportServiceType.A2P,
            "sms_trunk.id": [sms_trunk_id],
        }
        created_sms = client.exports().create(sms_out).data

        # The export is pending until its file is generated; read it again later
        completed = client.exports().find(created_sms.id).data
        expect(completed.export_type == ExportType.SMS_OUT, f"export_type is {completed.export_type!r}")
        print(f"    SMS OUT export {completed.id}: {enum_value(completed.status)}")


@check("Exports: download a completed export")
def _():
    params = QueryParams().filter("status", "completed").page(number=1, size=1)
    exports = client.exports().list(params).data
    if not exports:
        raise Skip("no completed export on the account yet; the exports of the previous check complete later")
    completed = exports[0]
    with tempfile.TemporaryDirectory() as directory:
        gzipped = os.path.join(directory, "export.csv.gz")
        plain = os.path.join(directory, "export.csv")
        client.download_export(completed.url, gzipped)              # gzipped CSV, as served
        client.download_and_decompress_export(completed.url, plain)  # plain CSV

        with open(os.path.join(directory, "copy.csv.gz"), "wb") as out:
            client.download_export(completed.url, out)                # any binary file object
        print(f"    {os.path.getsize(gzipped)} bytes gzipped, {os.path.getsize(plain)} bytes plain")


# ─── Prices ────────────────────────────────────────────────

section("Prices")


@check("Price lookups")
def _():
    prices_client = create_client(scope=Scope.READ)

    def lookup(service, filters):
        try:
            return service.lookup(filters)
        except DidwwPricesError as e:
            if e.kind not in (PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED, PricesErrorKind.PRICE_NOT_FOUND):
                raise
            print(f"    {filters}: {e.kind.value}")
            return None

    result = lookup(prices_client.voice_in_prices(), {"number": "18005550123", "src_country_iso": "US"})
    if result is not None:
        print(f"    {result.total_records} Voice IN record(s)")
        for price in result:
            if price.rate is not None:
                print(f"    {price.destination} {price.source_type}: {price.rate} USD/min")

    voice_out = lookup(prices_client.voice_out_prices(), {"number": "493012345678"})
    if voice_out is not None and voice_out[0].category == VoiceOutPriceCategory.INTERNATIONAL:
        print(f"    Voice OUT international rate: {voice_out[0].rate}")
    a2p = lookup(prices_client.sms_out_a2p_prices(), {"dst_number": "4915123456789"})
    sms_in = lookup(prices_client.sms_in_prices(), {"dst_country_iso": "US"})
    if result is None and voice_out is None and a2p is None and sms_in is None:
        raise Skip("the account has no price plan, or no price matches the sample numbers")


@check("Price files: fetch, read, head, download")
def _():
    prices = client.voice_in_prices()
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "voice_in_prices.csv.gz")
        try:
            # Download unless the copy at the path is current
            file = prices.fetch(path)
        except DidwwPricesError as e:
            if no_price_plan(e):
                raise Skip("the account has no Voice IN price plan") from None
            raise
        if file.not_modified:
            print("    answered 304, the file was kept")
        else:
            print(f"    downloaded {file.bytes_written} bytes, last modified {file.last_modified}")

        # Read the rows, keyed by the header line
        with PriceFileReader(path) as rows:
            for row in itertools.islice(rows, 5):
                print(f"    {row['Destination']}: {row['Rate']}")

        # Lower-level calls
        status = prices.head(file.last_modified)  # sent as If-Modified-Since; None sends none
        print(f"    head: not_modified={status.not_modified}, filename={status.filename}")
        status = prices.head(datetime(2026, 10, 1, tzinfo=timezone.utc))  # an aware datetime

        file = prices.download_to_file(path)
        with open(os.path.join(directory, "copy_of_voice_in_prices.csv.gz"), "wb") as out:
            file = prices.download(out)
        expect(file.bytes_written > 0, "the copy is empty")


# ─── Query parameters, dates, enums ────────────────────────

section("Query parameters, dates, enums")


@check("Filtering, sorting and pagination")
def _():
    params = (
        QueryParams()
        .filter("country.id", us_country().id)
        .filter("name", "Arizona")
        .include("country")
        .sort("name")
        .page(1, 25)
    )
    regions = client.regions().list(params).data
    for region in regions:
        print(f"    {region.name}, {region.country.name if region.country else None}")


@check("Date and datetime fields")
def _():
    dids = client.dids().list(QueryParams().page(number=1, size=1)).data
    if dids:
        did = client.dids().find(dids[0].id).data
        expect(isinstance(did.created_at, datetime) and did.created_at.tzinfo is not None,
               f"created_at is {did.created_at!r}")
        expect(did.expires_at is None or isinstance(did.expires_at, datetime), f"expires_at is {did.expires_at!r}")
        print(f"    created_at {did.created_at!r}, expires_at {did.expires_at!r}")
    with ExitStack() as cleanup:
        identity_id = new_identity(cleanup).id
        identity = client.identities().find(identity_id).data
        expect(identity.birth_date is None or isinstance(identity.birth_date, str),
               f"birth_date is {identity.birth_date!r}")
        print(f"    birth_date {identity.birth_date!r}")


@check("Enums")
def _():
    order = Order()
    order.callback_method = CallbackMethod.POST

    identity = Identity()
    identity.identity_type = IdentityType.BUSINESS

    expect(ExportType.CDR_IN.value == "cdr_in", "ExportType.CDR_IN.value")
    expect(order.attributes["callback_method"] == "post", "enums are stored as their value")
    print(f"    {ExportType.CDR_IN.value}, {order.callback_method.value}, {identity.identity_type.value}")


# ─── Files and callbacks ───────────────────────────────────

section("Files and callbacks")


@check("File encryption and upload")
def _():
    # The public keys of DIDWW (public_keys is called without a token)
    public_keys = [pk.key for pk in client.public_keys().list().data]

    with open(SAMPLE_PDF, "rb") as f:
        file_bytes = f.read()

    fingerprint = Encrypt.calculate_fingerprint(public_keys)
    encrypted = Encrypt.encrypt_with_keys(file_bytes, public_keys)

    encrypted_file_id = client.upload_encrypted_file(
        fingerprint,
        encrypted,
        description="document.pdf",
        filename="document.pdf.enc",
    )
    try:
        expect(encrypted_file_id, "no encrypted file ID")
        print(f"    uploaded {encrypted_file_id}")
    finally:
        delete(client.encrypted_files(), encrypted_file_id, "encrypted file")


@check("Webhook signature validation")
def _():
    validator = RequestValidator("YOUR_CALLBACK_SECRET")
    request_url = "https://example.com/callbacks/didww"
    payload_dict = {"id": "1dd7a68b-e235-402b-8912-fe73ee14243a", "type": "orders", "status": "completed"}
    signature = sign("YOUR_CALLBACK_SECRET", request_url, payload_dict)

    valid = validator.validate(
        url=request_url,       # full original URL
        payload=payload_dict,  # dict of payload key-value pairs
        signature=signature,   # value of X-DIDWW-Signature header
    )
    expect(valid is True, "the signed callback is not valid")
    tampered = dict(payload_dict, status="canceled")
    expect(validator.validate(url=request_url, payload=tampered, signature=signature) is False,
           "a tampered callback is valid")
    print("    signed callback valid, tampered callback not valid")


# ─── Error handling ────────────────────────────────────────

section("Error handling")


@check("Error handling: DidwwApiError of an unknown trunk")
def _():
    caught = None
    try:
        client.voice_in_trunks().find("nonexistent")
    except DidwwApiError as e:
        caught = e
        print(f"    HTTP Status: {e.status_code}")
        for error in e.errors:
            print(f"    Error: {error.get('detail', error.get('title'))}")
    except DidwwClientError as e:
        print(f"    Client error: {e}")
    expect(caught is not None, "no DidwwApiError")


@check("Error handling: a 429 of the API")
def _():
    try:
        client.dids().list()
    except DidwwApiError as e:
        if e.status_code != 429:
            raise
        print(f"    API rate limit, retry after {e.retry_after} s")


@check("Error handling: token service and prices error kinds")
def _():
    try:
        try:
            client.sms_out_a2p_prices().lookup({"dst_number": "4915123456789"})
        except DidwwAuthError as e:
            if e.kind == AuthErrorKind.RATE_LIMITED:
                # Wait retry_after seconds and try again; repeat while the kind is RATE_LIMITED.
                print(f"    Token service rate limit, retry after {e.retry_after} s")
            elif e.kind == AuthErrorKind.INVALID_CLIENT:
                print(f"    API key refused: {e}")
            else:
                raise
        except DidwwPricesError as e:
            if e.kind == PricesErrorKind.PRICE_NOT_FOUND:
                print("    No price for this number")
            elif e.kind == PricesErrorKind.TOO_MANY_REQUESTS:
                print(f"    Prices rate limit, retry after {e.retry_after} s")
            else:
                raise
        except DidwwError as e:
            print(f"    Error: {e}")
    except DidwwPricesError as e:
        if no_price_plan(e):
            raise Skip("the account has no SMS OUT A2P price plan") from None
        raise


# ─── Summary ───────────────────────────────────────────────

print("\n" + "=" * 50)
if skipped:
    print(f"Skipped ({len(skipped)}):")
    for line in skipped:
        print(f"  - {line}")
if failures:
    print(f"Failures ({len(failures)}):")
    for line in failures:
        print(f"  - {line}")
print(f"Results: {passed} passed, {failed} failed")
print("=" * 50)

sys.exit(1 if failed else 0)
