# Examples

All examples read the API key from the `DIDWW_API_KEY` environment variable.

## Prerequisites

- Python 3.9+
- DIDWW API key for sandbox account

## Environment variables

- `DIDWW_API_KEY` (required): your DIDWW API key
- `FILE_PATH` (optional for `upload_file.py`): file to encrypt and upload. Defaults to `sample.pdf`

## Install

```bash
pip install -e ..
```

## Run an example

```bash
DIDWW_API_KEY=your_api_key python examples/balance.py
```

## Available examples

| Script | Description |
|---|---|
| [`balance.py`](balance.py) | Fetches and prints current account balance and credit. |
| [`countries.py`](countries.py) | Lists countries, demonstrates filtering, and fetches one country by ID. |
| [`did_groups.py`](did_groups.py) | Fetches DID groups with included SKUs and shows group details. |
| [`trunks.py`](trunks.py) | Creates SIP and PSTN trunks, prints details, then deletes them. |
| [`regions.py`](regions.py) | Lists regions, filters by country, and fetches a specific region. |
| [`voice_in_trunks.py`](voice_in_trunks.py) | Lists voice in trunks with their configurations and POP details. |
| [`orders.py`](orders.py) | Lists orders, creates a DID order, and cancels it. |
| [`orders_available_dids.py`](orders_available_dids.py) | Orders a specific available DID using included DID group SKU. |
| [`orders_reservation_dids.py`](orders_reservation_dids.py) | Reserves a DID and then places an order from that reservation. |
| [`orders_all_item_types.py`](orders_all_item_types.py) | Creates orders with all 3 item types: by SKU, by available DID, and by reservation. |
| [`orders_capacity.py`](orders_capacity.py) | Purchases capacity by creating a capacity order item. |
| [`orders_sku.py`](orders_sku.py) | Creates a DID order with all item types: by SKU, by available DID, and by reservation. Fetches ordered DIDs. |
| [`orders_nanpa.py`](orders_nanpa.py) | Orders a DID number by NPA/NXX prefix. |
| [`upload_file.py`](upload_file.py) | Reads a file, encrypts it, and uploads to `encrypted_files`. |
| [`identity_address_proofs.py`](identity_address_proofs.py) | Creates identity and address, encrypts and uploads files, attaches proofs to both. |
| [`voice_in_trunk_groups.py`](voice_in_trunk_groups.py) | Creates trunks and a trunk group, lists groups with includes, updates, and deletes (cascade). |
| [`voice_out_trunks.py`](voice_out_trunks.py) | Creates, lists, updates, and deletes a voice out trunk. Requires account configuration. |
| [`did_trunk_assignment.py`](did_trunk_assignment.py) | Demonstrates exclusive DID trunk/trunk group assignment and re-assignment. |
| [`did_reservations.py`](did_reservations.py) | Creates, lists, finds, and deletes a DID reservation. |
| [`exports.py`](exports.py) | Creates a CDR export with from/to filters and lists all exports. |
| [`capacity_pools.py`](capacity_pools.py) | Lists capacity pools with included shared capacity groups and qty-based pricings. |
| [`shared_capacity_groups.py`](shared_capacity_groups.py) | Creates and deletes a shared capacity group. |
| [`did_history.py`](did_history.py) | Lists DID ownership history events (2026-04-16). |
| [`emergency_requirements.py`](emergency_requirements.py) | Lists emergency requirements with country includes (2026-04-16). |
| [`emergency_calling_services.py`](emergency_calling_services.py) | Lists emergency calling services (2026-04-16). |
| [`emergency_verifications.py`](emergency_verifications.py) | Lists emergency verifications with address and DIDs (2026-04-16). |
| [`emergency_requirement_validations.py`](emergency_requirement_validations.py) | Validates emergency requirements (2026-04-16). |
| [`emergency_scenario.py`](emergency_scenario.py) | End-to-end: find DID → check requirements → validate → create verification → get service. |
| [`address_verifications.py`](address_verifications.py) | Lists address verifications with includes (2026-04-16). |
| [`orders_emergency.py`](orders_emergency.py) |  List recent orders, filter for emergency (2026-04-16). |

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
