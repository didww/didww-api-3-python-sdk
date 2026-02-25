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
| [`orders_sku.py`](orders_sku.py) | Creates a DID order with all item types: by SKU, by available DID, and by reservation. Fetches ordered DIDs. |
| [`upload_file.py`](upload_file.py) | Reads a file, encrypts it, and uploads to `encrypted_files`. |
| [`identity_address_proofs.py`](identity_address_proofs.py) | Creates identity and address, encrypts and uploads files, attaches proofs to both. |
| [`voice_in_trunk_groups.py`](voice_in_trunk_groups.py) | Creates trunks and a trunk group, lists groups with includes, updates, and deletes (cascade). |
| [`voice_out_trunks.py`](voice_out_trunks.py) | Creates, lists, updates, and deletes a voice out trunk. Requires account configuration. |
| [`did_trunk_assignment.py`](did_trunk_assignment.py) | Demonstrates exclusive DID trunk/trunk group assignment and re-assignment. |
| [`did_reservations.py`](did_reservations.py) | Creates, lists, finds, and deletes a DID reservation. |
| [`exports.py`](exports.py) | Creates a CDR export and lists all exports. |
| [`capacity_pools.py`](capacity_pools.py) | Lists capacity pools with included shared capacity groups and qty-based pricings. |
| [`shared_capacity_groups.py`](shared_capacity_groups.py) | Creates and deletes a shared capacity group. |

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
