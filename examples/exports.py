"""
Exports: create, list, and update CDR exports (cdr_in / cdr_out).

Filter semantics on CDR exports ("YYYY-MM-DD HH:MM:SS" in UTC; "to" must not be in the future):
  from: lower bound, INCLUSIVE (time_start >= from)
  to:   upper bound, EXCLUSIVE (time_start <  to)
To cover a whole day, pass from: "2026-04-15 00:00:00", to: "2026-04-16 00:00:00".

The file URL is set once the export is completed: find the export again later
and download it (see exports_sms.py).

Usage: DIDWW_API_KEY=xxx python examples/exports.py
"""
import uuid
from datetime import datetime, timedelta, timezone

from client_factory import create_client
from didww.enums import ExportType, enum_value
from didww.resources.export import Export

client = create_client()
suffix = uuid.uuid4().hex[:8]

# Both bounds come from one UTC midnight, so "to" is never in the future
today = datetime.now(timezone.utc).date()
yesterday = today - timedelta(days=1)

# Create a CDR-In export for yesterday
export = Export()
export.export_type = ExportType.CDR_IN
export.filters = {
    "from": f"{yesterday} 00:00:00",  # inclusive
    "to": f"{today} 00:00:00",  # exclusive
}
export.external_reference_id = f"python-cdr-in-{suffix}"

created = client.exports().create(export).data
print(f"Created export: {created.id}")
print(f"  type: {enum_value(created.export_type)}")
print(f"  status: {enum_value(created.status)}")
print(f"  external_reference_id: {created.external_reference_id}")

# List exports
exports = client.exports().list().data
print(f"\nAll exports ({len(exports)}):")
for e in exports:
    print(f"  {e.id} {enum_value(e.export_type)} [{enum_value(e.status)}] ref={e.external_reference_id}")

# Update external_reference_id
update = Export.build(created.id)
update.external_reference_id = f"python-cdr-in-{suffix}-renamed"
updated = client.exports().update(update).data
print(f"\nUpdated export: {updated.id}")
print(f"  external_reference_id: {updated.external_reference_id}")
