# Examples

All examples read the API key from the `DIDWW_API_KEY` environment variable.

## Prerequisites

- Python 3.9+
- DIDWW API key for sandbox account

## Environment variables

- `DIDWW_API_KEY` (required): your DIDWW API key
- `FILE_PATH` (required only for `upload_file.py`): file to encrypt and upload

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
| [`trunks.py`](trunks.py) | Creates a SIP trunk with configuration, prints details, then deletes it. |
| [`orders_sku.py`](orders_sku.py) | Creates a DID order by SKU resolved from DID groups. |
| [`upload_file.py`](upload_file.py) | Reads a file, encrypts it, and uploads to `encrypted_files`. |

## Upload file example

```bash
DIDWW_API_KEY=your_api_key FILE_PATH=/path/to/file.jpeg python examples/upload_file.py
```

## Troubleshooting

If `DIDWW_API_KEY` is missing, examples fail fast with:

`DIDWW_API_KEY environment variable is required`
