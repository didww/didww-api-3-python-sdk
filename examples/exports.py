"""
Exports: create, list, and update CDR exports (2026-04-16).

Filter semantics for CDR exports (cdr_in / cdr_out):
  from: ISO 8601 datetime, INCLUSIVE (time_start >= from)
  to:   ISO 8601 datetime, EXCLUSIVE (time_start <  to)

Usage: DIDWW_API_KEY=xxx python examples/exports.py
"""
from client_factory import create_client
from didww.enums import ExportType
from didww.resources.export import Export

client = create_client()

# Create an export with from/to datetime range
export = Export()
export.export_type = ExportType.CDR_IN
export.filters = {
    "did_number": "1234567890",
    "from": "2026-04-01 00:00:00",
    "to": "2026-04-15 23:59:59",
}
export.external_reference_id = "monthly-cdr-april"

created = client.exports().create(export).data
print(f"Created export: {created.id}")
print(f"  type: {created.export_type}")
print(f"  status: {created.status}")
print(f"  external_reference_id: {created.external_reference_id}")

# List exports
exports = client.exports().list().data
print(f"\nAll exports ({len(exports)}):")
for e in exports:
    print(f"  {e.id} {e.export_type} [{e.status}] ref={e.external_reference_id}")

# Update external_reference_id
update = Export()
update.id = created.id
update.external_reference_id = "renamed-cdr-april"
updated = client.exports().update(update).data
print(f"\nUpdated export: {updated.id}")
print(f"  external_reference_id: {updated.external_reference_id}")
