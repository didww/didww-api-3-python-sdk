# Examples

All examples read the API key from the `DIDWW_API_KEY` environment variable and use the sandbox. `webhook.py` sends no request and needs no key.

## Prerequisites

- Python 3.11+
- DIDWW API key for sandbox account

## Environment variables

- `DIDWW_API_KEY` (required): your DIDWW API key
- `FILE_PATH` (optional for `upload_file.py`): file to encrypt and upload. Defaults to `sample.pdf`
- `XDG_CACHE_HOME` (optional for `prices_download.py`, Linux and other Unix systems): user cache directory, `~/.cache` if not set

## Install

From the repository root:

```bash
pip install -e .
```

## Run an example

From the repository root:

```bash
DIDWW_API_KEY=your_api_key python examples/balance.py
```

### Pass an argument

`prices_lookup.py` takes an optional number:

```bash
DIDWW_API_KEY=your_api_key python examples/prices_lookup.py 18005550123
```

## Available examples

| # | Script | Description |
|---|---|---|
| 1 | [`balance.py`](balance.py) | Fetches and prints the account balance and credit. |
| 2 | [`countries.py`](countries.py) | Lists countries with a filter and a sort, and fetches one country by ID. |
| 3 | [`regions.py`](regions.py) | Lists the regions of a country with the country included, and fetches one region. |
| 4 | [`did_groups.py`](did_groups.py) | Lists DID groups with included SKUs, number type, demo flag and group details. |
| 5 | [`did_history.py`](did_history.py) | Lists DID history events of the last 90 days, then those of one number. |
| 6 | [`dids.py`](dids.py) | Lists DIDs with their emergency relationships and updates the first DID: trunk, capacity pool, capacity limit and description. |
| 7 | [`did_trunk_assignment.py`](did_trunk_assignment.py) | Assigns a DID to a trunk, then to a trunk group (the trunk is cleared: they are exclusive), then restores the DID's original routing. |
| 8 | [`did_sms_routing.py`](did_sms_routing.py) | Routes a DID's inbound SMS to an SMS trunk, then to an SMS trunk group (exclusive), then restores the original routing. |
| 9 | [`did_reservations.py`](did_reservations.py) | Reserves an available DID, lists and finds reservations, deletes the reservation. |
| 10 | [`capacity_pools.py`](capacity_pools.py) | Lists capacity pools with included shared capacity groups and qty-based pricings, finds one. |
| 11 | [`shared_capacity_groups.py`](shared_capacity_groups.py) | Creates a shared capacity group in a capacity pool, lists the groups, updates and deletes it. |
| 12 | [`orders.py`](orders.py) | Lists recent orders, orders a DID by SKU and cancels (deletes) that order. |
| 13 | [`orders_sku.py`](orders_sku.py) | Orders DIDs by SKU and quantity (a `DidOrderItem` with `sku_id` and `qty`) and lists the ordered DIDs. |
| 14 | [`orders_available_dids.py`](orders_available_dids.py) | Orders a specific available DID with the SKU of its included DID group. |
| 15 | [`orders_reservation_dids.py`](orders_reservation_dids.py) | Reserves a DID, then orders it from the reservation. |
| 16 | [`orders_nanpa.py`](orders_nanpa.py) | Orders a NANPA DID by NPA/NXX prefix. |
| 17 | [`orders_capacity.py`](orders_capacity.py) | Buys capacity channels in a capacity pool. |
| 18 | [`orders_all_item_types.py`](orders_all_item_types.py) | One order with the three DID item variants: by SKU and quantity, an available DID and a reserved DID. Capacity cannot share an order with DID items. |
| 19 | [`orders_emergency.py`](orders_emergency.py) | Picks the emergency orders (created by DIDWW) among the recent orders and follows an emergency calling service to its order. |
| 20 | [`trunks.py`](trunks.py) | Lists Voice IN trunks with their trunk group (codecs, ICE / RTCP modes, `pop`), finds one, creates a SIP and a PSTN trunk, updates and deletes both. |
| 21 | [`voice_in_trunk_groups.py`](voice_in_trunk_groups.py) | Creates two trunks and a trunk group with them, lists groups, renames the group, deletes the group and the trunks. |
| 22 | [`voice_in_trunk_sip_registration.py`](voice_in_trunk_sip_registration.py) | End-to-end SIP registration flow: create with `enabled_sip_registration=True`, rename, disable by setting `host`, re-enable by toggling the flag. The SDK keeps the dependent fields (`host`, `port`, `use_did_in_ruri`) aligned with the server's validation rules automatically. The trunk is left in place. |
| 23 | [`voice_out_trunks.py`](voice_out_trunks.py) | Lists Voice OUT trunks, creates one (with codecs and ICE mode), updates and deletes it. Requires account configuration. |
| 24 | [`sms_trunks.py`](sms_trunks.py) | Lists SMS trunks, creates and updates an HTTP IN trunk, regenerates the credentials of an HTTP OUT trunk, deletes both. |
| 25 | [`sms_trunk_groups.py`](sms_trunk_groups.py) | Creates two inbound SMS trunks, groups them by priority, lists groups, deletes the group (and its trunks). |
| 26 | [`sender_id_verifications.py`](sender_id_verifications.py) | Lists Sender ID verifications with their SMS trunks, renames an active one, then restores its name. |
| 27 | [`identity_address_proofs.py`](identity_address_proofs.py) | Creates an identity and an address, encrypts and uploads files, creates proofs for both, prints the verified flags, deletes them. |
| 28 | [`address_verifications.py`](address_verifications.py) | Lists address verifications with the address and DIDs included. |
| 29 | [`upload_file.py`](upload_file.py) | Encrypts a file with the DIDWW public keys and uploads it with `upload_encrypted_file`; prints the encrypted file ID. |
| 30 | [`exports.py`](exports.py) | Creates a CDR export with from/to datetime range filters (UTC), lists exports, updates its external reference. |
| 31 | [`exports_sms.py`](exports_sms.py) | Creates `sms_in` and `sms_out` exports with their filters and reads the columns of a completed one, downloaded in memory. |
| 32 | [`emergency_requirements.py`](emergency_requirements.py) | Lists emergency requirements per country and number type. |
| 33 | [`emergency_requirement_validations.py`](emergency_requirement_validations.py) | Validates an emergency requirement with an address and an identity. |
| 34 | [`emergency_verifications.py`](emergency_verifications.py) | Lists emergency verifications with the address and DIDs included. |
| 35 | [`emergency_calling_services.py`](emergency_calling_services.py) | Lists emergency calling services. |
| 36 | [`emergency_scenario.py`](emergency_scenario.py) | End-to-end: order a DID → check requirements → validate → create verification → get service. |
| 37 | [`prices_lookup.py`](prices_lookup.py) `[number]` | Looks up Voice IN, Voice OUT, SMS OUT (A2P, P2P, OTP) and SMS IN prices for a number with a read-scoped client. |
| 38 | [`prices_download.py`](prices_download.py) | Downloads the Voice IN price file, fetches it again with If-Modified-Since (304), reads the first rows. Directory: `didww-prices` in the user cache directory, created for the current user only. |
| 39 | [`includes.py`](includes.py) | Reads regions with their country, DID groups with SKUs, available DIDs with a nested include and DIDs with their trunk; shows that a relationship not included reads as `None`. |
| 40 | [`webhook.py`](webhook.py) | Signs a sample callback the way DIDWW does and checks it with `RequestValidator`: `valid: true`, and `valid: false` for a tampered payload. |
| 41 | [`test_readme.py`](test_readme.py) | Runs the code snippets of the SDK's README against the sandbox, one check per snippet, and cleans up; prints `Results: N passed, M failed` and exits with 1 when a check failed. |

`sender_id_verifications.py`, `did_sms_routing.py`, `did_trunk_assignment.py` and `test_readme.py` change existing account state and restore it at the end; `trunks.py`, `shared_capacity_groups.py`, `voice_in_trunk_groups.py`, `sms_trunks.py`, `sms_trunk_groups.py` and `test_readme.py` delete what they create. Both happen also when a step fails. Orders and exports cannot be deleted.

## Upload file example

```bash
# Uses bundled sample.pdf by default
DIDWW_API_KEY=your_api_key python examples/upload_file.py

# Or specify a custom file
DIDWW_API_KEY=your_api_key FILE_PATH=/path/to/file.jpeg python examples/upload_file.py
```

## Troubleshooting

If `DIDWW_API_KEY` is missing, examples fail fast with:

`DIDWW_API_KEY environment variable is required`
