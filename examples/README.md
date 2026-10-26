# Examples

All examples read the API key from the `DIDWW_API_KEY` environment variable.

## Prerequisites

- Python 3.9+
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

| Script | Description |
|---|---|
| [`balance.py`](balance.py) | Fetches and prints current account balance and credit. |
| [`countries.py`](countries.py) | Lists countries, demonstrates filtering, and fetches one country by ID. |
| [`did_groups.py`](did_groups.py) | Fetches DID groups with included SKUs, number type, demo flag and group details. |
| [`trunks.py`](trunks.py) | Creates SIP and PSTN trunks, prints details, then deletes them. |
| [`regions.py`](regions.py) | Lists regions, filters by country, and fetches a specific region. |
| [`voice_in_trunks.py`](voice_in_trunks.py) | Lists voice in trunks with their configurations and point of presence (`pop`). |
| [`voice_in_trunk_sip_registration.py`](voice_in_trunk_sip_registration.py) | End-to-end SIP registration flow: create with `enabled_sip_registration=True`, rename, disable by setting `host`, re-enable by toggling the flag. The SDK keeps the dependent fields (`host`, `port`, `use_did_in_ruri`) aligned with the server's validation rules automatically. |
| [`orders.py`](orders.py) | Lists orders, creates a DID order, and cancels it. |
| [`orders_available_dids.py`](orders_available_dids.py) | Orders a specific available DID using included DID group SKU. |
| [`orders_reservation_dids.py`](orders_reservation_dids.py) | Reserves a DID and then places an order from that reservation. |
| [`orders_all_item_types.py`](orders_all_item_types.py) | Creates orders with all 3 item types: by SKU, by available DID, and by reservation. |
| [`orders_capacity.py`](orders_capacity.py) | Purchases capacity by creating a capacity order item. |
| [`orders_sku.py`](orders_sku.py) | Creates a DID order with all item types: by SKU, by available DID, and by reservation. Fetches ordered DIDs. |
| [`orders_nanpa.py`](orders_nanpa.py) | Orders a DID number by NPA/NXX prefix. |
| [`upload_file.py`](upload_file.py) | Reads a file, encrypts it, and uploads it to `encrypted_files` with `upload_encrypted_file`. |
| [`identity_address_proofs.py`](identity_address_proofs.py) | Creates identity and address, encrypts and uploads files, attaches proofs to both. |
| [`voice_in_trunk_groups.py`](voice_in_trunk_groups.py) | Creates trunks and a trunk group, lists groups with includes, updates, and deletes (cascade); cleans up when a step fails. |
| [`voice_out_trunks.py`](voice_out_trunks.py) | Creates, lists, updates, and deletes a voice out trunk. Requires account configuration. |
| [`did_trunk_assignment.py`](did_trunk_assignment.py) | Demonstrates exclusive DID trunk/trunk group assignment and re-assignment, then restores the DID's original routing. |
| [`did_reservations.py`](did_reservations.py) | Creates, lists, finds, and deletes a DID reservation. |
| [`exports.py`](exports.py) | Creates a CDR export with from/to datetime range filters (UTC) and lists all exports. |
| [`capacity_pools.py`](capacity_pools.py) | Lists capacity pools with included shared capacity groups and qty-based pricings. |
| [`shared_capacity_groups.py`](shared_capacity_groups.py) | Creates and deletes a shared capacity group. |
| [`did_history.py`](did_history.py) | Lists DID ownership history events. |
| [`emergency_requirements.py`](emergency_requirements.py) | Lists emergency requirements per country/number type. |
| [`emergency_calling_services.py`](emergency_calling_services.py) | Lists emergency calling services. |
| [`emergency_verifications.py`](emergency_verifications.py) | Lists emergency verifications with address and DIDs. |
| [`emergency_requirement_validations.py`](emergency_requirement_validations.py) | Validates emergency requirements. |
| [`emergency_scenario.py`](emergency_scenario.py) | End-to-end: find DID → check requirements → validate → create verification → get service. |
| [`address_verifications.py`](address_verifications.py) | Lists address verifications with includes. |
| [`orders_emergency.py`](orders_emergency.py) | Lists recent orders, filters for emergency. |

### SMS

| Script | Description |
|---|---|
| [`sms_trunks.py`](sms_trunks.py) | Lists SMS trunks, creates and updates an HTTP IN trunk, regenerates the credentials of an HTTP OUT trunk, deletes both. |
| [`sms_trunk_groups.py`](sms_trunk_groups.py) | Creates two inbound SMS trunks, groups them by priority, lists groups, deletes the group (and its trunks). |
| [`sender_id_verifications.py`](sender_id_verifications.py) | Lists Sender ID verifications with their SMS trunks, renames an active one, then restores its name. |
| [`did_sms_routing.py`](did_sms_routing.py) | Routes a DID's inbound SMS to an SMS trunk, then to an SMS trunk group (exclusive), then restores the original routing. |
| [`exports_sms.py`](exports_sms.py) | Creates `sms_in` and `sms_out` exports with their filters and reads the columns of a completed one, downloaded in memory. |

### Prices

| Script | Description |
|---|---|
| [`prices_lookup.py`](prices_lookup.py) `[number]` | Looks up Voice IN, Voice OUT, SMS OUT (A2P, P2P, OTP) and SMS IN prices for a number with a read-scoped client. |
| [`prices_download.py`](prices_download.py) | Downloads the Voice IN price file, fetches it again with If-Modified-Since (304), reads the first rows. Directory: `didww-prices` in the user cache directory, created for the current user only. |

`sender_id_verifications.py`, `did_sms_routing.py` and `did_trunk_assignment.py` change existing account state and restore it at the end; `voice_in_trunk_groups.py`, `sms_trunks.py` and `sms_trunk_groups.py` delete what they create. Both happen also when a step fails.

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
