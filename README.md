Python client for DIDWW API v3.

![Tests](https://github.com/didww/didww-api-3-python-sdk/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

## About DIDWW API v3

The DIDWW API provides a simple yet powerful interface that allows you to fully integrate your own applications with DIDWW services. An extensive set of actions may be performed using this API, such as ordering and configuring phone numbers, setting capacity, creating SIP trunks and retrieving CDRs and other operational data.

The DIDWW API v3 is a fully compliant implementation of the [JSON API specification](http://jsonapi.org/format/).

Read more https://doc.didww.com/api

## Requirements

- Python 3.9+

## Installation

```bash
pip install didww
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

For more examples visit [examples](examples/).

For details on obtaining your API key please visit https://doc.didww.com/api#introduction-api-keys

## Examples

- Source code: [examples/](examples/)
- How to run: [examples/README.md](examples/README.md)

## Configuration

```python
from didww.client import DidwwClient
from didww.configuration import Environment

# Sandbox
client = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.SANDBOX)

# Production
client = DidwwClient(api_key="YOUR_API_KEY", environment=Environment.PRODUCTION)
```

### Environments

| Environment | Base URL |
|-------------|----------|
| `Environment.PRODUCTION` | `https://api.didww.com/v3` |
| `Environment.SANDBOX` | `https://sandbox-api.didww.com/v3` |

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

# POPs (Points of Presence)
pops = client.pops().list().data

# DID Group Types
types = client.did_group_types().list().data

# DID Groups (with stock keeping units)
params = QueryParams().include("stock_keeping_units")
groups = client.did_groups().list(params).data

# Available DIDs (with DID group and stock keeping units)
params = QueryParams().include("did_group.stock_keeping_units")
available = client.available_dids().list(params).data

# Proof Types
proof_types = client.proof_types().list().data

# Public Keys
public_keys = client.public_keys().list().data

# Requirements
requirements = client.requirements().list().data

# Supporting Document Templates
templates = client.supporting_document_templates().list().data

# Balance (singleton)
balance = client.balance().find().data
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

### Voice In Trunks

```python
from didww.enums import CliFormat, Codec, TransportProtocol
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.configuration.sip import SipConfiguration

# Create SIP trunk
trunk = VoiceInTrunk()
trunk.name = "My SIP Trunk"
trunk.priority = 1
trunk.weight = 100
trunk.cli_format = CliFormat.E164
trunk.ringing_timeout = 30

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

### Voice In Trunk Groups

```python
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup

group = VoiceInTrunkGroup()
group.name = "Primary Group"
group.capacity_limit = 50
created = client.voice_in_trunk_groups().create(group).data
```

### Voice Out Trunks

```python
from didww.enums import OnCliMismatchAction
from didww.resources.voice_out_trunk import VoiceOutTrunk

trunk = VoiceOutTrunk()
trunk.name = "My Outbound Trunk"
trunk.allowed_sip_ips = ["0.0.0.0/0"]
trunk.on_cli_mismatch_action = OnCliMismatchAction.REPLACE_CLI
created = client.voice_out_trunks().create(trunk).data
```

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
scg.capacity_pool = CapacityPool.build("pool-uuid")
created = client.shared_capacity_groups().create(scg).data
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
from didww.enums import ExportType
from didww.resources.export import Export

export = Export()
export.export_type = ExportType.CDR_IN
export.filters = {"year": 2025, "month": 1}
created = client.exports().create(export).data

# Download the export when completed
client.download_export(created.url, "/tmp/export.csv")
```

## Filtering, Sorting, and Pagination

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

## Enums

The SDK provides enum classes aligned with the Java SDK (for example `CallbackMethod`, `IdentityType`, `OrderStatus`, `ExportType`, `CliFormat`, `OnCliMismatchAction`, `MediaEncryptionMode`, `TransportProtocol`, `Codec`, and more).

```python
from didww.enums import CallbackMethod, IdentityType
from didww.resources.order import Order
from didww.resources.identity import Identity

order = Order()
order.callback_method = CallbackMethod.POST

identity = Identity()
identity.identity_type = IdentityType.BUSINESS
```

## File Encryption

The SDK provides an `Encrypt` utility for encrypting files before upload, using RSA-OAEP + AES-256-CBC (matching DIDWW's encryption requirements).

```python
from didww.encrypt import Encrypt

# Provide your own public key PEM strings
public_keys = [public_key_pem_1, public_key_pem_2]
fingerprint = Encrypt.calculate_fingerprint(public_keys)
encrypted = Encrypt.encrypt_with_keys(file_bytes, public_keys)
```

Upload encrypted file:

```python
file_ids = client.upload_encrypted_files(
    fingerprint=fingerprint,
    files=[
        {"data": encrypted, "description": "document.pdf", "filename": "document.pdf.enc"},
    ],
)
```

## Webhook Signature Validation

Validate incoming webhook callbacks from DIDWW using HMAC-SHA1 signature verification.

```python
from didww.callback.request_validator import RequestValidator

validator = RequestValidator("YOUR_API_KEY")

# In your webhook handler:
valid = validator.validate(
    url=request_url,       # full original URL
    payload=payload_dict,  # dict of payload key-value pairs
    signature=signature,   # value of X-DIDWW-Signature header
)
```

## Error Handling

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

## Trunk Configuration Types

| Type | Class |
|------|-------|
| SIP | `SipConfiguration` |
| PSTN | `PstnConfiguration` |

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
| Pop | `client.pops()` | list, find |
| DidGroupType | `client.did_group_types()` | list, find |
| DidGroup | `client.did_groups()` | list, find |
| AvailableDid | `client.available_dids()` | list, find |
| ProofType | `client.proof_types()` | list, find |
| PublicKey | `client.public_keys()` | list, find |
| Requirement | `client.requirements()` | list, find |
| SupportingDocumentTemplate | `client.supporting_document_templates()` | list, find |
| Balance | `client.balance()` | find |
| Did | `client.dids()` | list, find, update, delete |
| VoiceInTrunk | `client.voice_in_trunks()` | list, find, create, update, delete |
| VoiceInTrunkGroup | `client.voice_in_trunk_groups()` | list, find, create, update, delete |
| VoiceOutTrunk | `client.voice_out_trunks()` | list, find, create, update, delete |
| VoiceOutTrunkRegenerateCredential | `client.voice_out_trunk_regenerate_credentials()` | create |
| DidReservation | `client.did_reservations()` | list, find, create, delete |
| CapacityPool | `client.capacity_pools()` | list, find |
| SharedCapacityGroup | `client.shared_capacity_groups()` | list, find, create, update, delete |
| Order | `client.orders()` | list, find, create |
| Export | `client.exports()` | list, find, create |
| Address | `client.addresses()` | list, find, create, delete |
| AddressVerification | `client.address_verifications()` | list, create |
| Identity | `client.identities()` | list, find, create, delete |
| EncryptedFile | `client.encrypted_files()` | list, find, delete |
| PermanentSupportingDocument | `client.permanent_supporting_documents()` | create, delete |
| Proof | `client.proofs()` | create, delete |
| RequirementValidation | `client.requirement_validations()` | create |

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/didww/didww-api-3-python-sdk

### Build and Release

**Note:** don't forget to change **version** in `pyproject.toml`

prepare venv
```shell
python3 -m pip install twine
python3 -m pip install build
```

build and check
```shell
python3 -m build --sdist
python3 -m build --wheel
twine check dist/*
```

upload
```shell
twine upload dist/*
```

## License

The package is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
