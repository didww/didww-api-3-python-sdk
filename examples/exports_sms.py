"""
SMS exports: creates sms_out and sms_in exports for yesterday and reads the
columns of a completed SMS-Out export, downloaded in memory.

Filters on SMS exports (Export.filters, a dict):
  - "from", "to" (required): "YYYY-MM-DD HH:MM:SS" in UTC; from inclusive,
    to exclusive and not in the future
  - "source_address_eq" / "source_address_cont", "destination_address_eq" /
    "destination_address_cont", "status", "sms_id"
  - "sms_trunk.id": one id or a list of ids
  - sms_in only: "trunk_type", one or a list of ExportTrunkType values (.value)
  - sms_out only: "service_type" ("a2p" or "p2p"), "sender_id_verification.id"

Usage: DIDWW_API_KEY=xxx python examples/exports_sms.py
"""
import io
import uuid
from datetime import datetime, timedelta, timezone

from client_factory import create_client
from didww.enums import ExportStatus, ExportTrunkType, ExportType, enum_value
from didww.exceptions import DidwwApiError
from didww.query_params import QueryParams
from didww.resources.export import Export

client = create_client()
suffix = uuid.uuid4().hex[:8]

# Both bounds come from one UTC midnight, so "to" is never in the future
today = datetime.now(timezone.utc).date()
date_from = f"{today - timedelta(days=1)} 00:00:00"  # inclusive
date_to = f"{today} 00:00:00"  # exclusive


def create(export_type, filters, external_reference_id):
    export = Export()
    export.export_type = export_type
    export.filters = filters
    export.external_reference_id = external_reference_id
    try:
        created = client.exports().create(export).data
    except DidwwApiError as e:
        print(f"Error creating {export_type.value} export: {e}")
        return
    # The file URL is set once the export is completed: find the export again later to download it.
    print(f"Created {export_type.value} export: {created.id} (status: {enum_value(created.status)})")


print("=== Creating SMS-Out Export (A2P, yesterday) ===")
create(ExportType.SMS_OUT, {"from": date_from, "to": date_to, "service_type": "a2p"},
       f"python-sms-out-{suffix}")

print("\n=== Creating SMS-In Export (HTTP IN and email trunks, yesterday) ===")
in_filters = {
    "from": date_from,
    "to": date_to,
    "trunk_type": [ExportTrunkType.HTTP_IN.value, ExportTrunkType.EMAIL.value],
}
# "sms_trunk.id" takes one id or a list of ids
trunk_ids = [t.id for t in client.sms_trunks().list(QueryParams().page(number=1, size=2)).data]
if trunk_ids:
    in_filters["sms_trunk.id"] = trunk_ids
create(ExportType.SMS_IN, in_filters, f"python-sms-in-{suffix}")

print("\n=== Completed SMS-Out exports ===")
params = (QueryParams()
          .filter("export_type", ExportType.SMS_OUT.value)
          .filter("status", ExportStatus.COMPLETED.value))
completed = client.exports().list(params).data
print(f"Found {len(completed)} completed SMS-Out exports")

if completed and completed[0].url:
    # The export file is a gzip-compressed CSV; download it decompressed into
    # memory and read its header line.
    export = completed[0]
    csv_data = io.BytesIO()
    client.download_and_decompress_export(export.url, csv_data)
    csv_data.seek(0)
    header = csv_data.readline().decode("utf-8-sig").rstrip("\r\n")
    print(f"Export {export.id} ({enum_value(export.export_type)}) columns: {header}")
