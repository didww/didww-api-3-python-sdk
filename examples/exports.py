"""
Exports: create and list CDR exports.
Usage: DIDWW_API_KEY=xxx python examples/exports.py
"""
from client_factory import create_client
from didww.enums import ExportType
from didww.resources.export import Export

client = create_client()

# Create an export
export = Export()
export.export_type = ExportType.CDR_IN
export.filters = {"year": 2025, "month": 1}

created = client.exports().create(export).data
print(f"Created export: {created.id}")
print(f"  type: {created.export_type}")
print(f"  status: {created.status}")

# List exports
exports = client.exports().list().data
print(f"\nAll exports ({len(exports)}):")
for e in exports:
    print(f"  {e.id} {e.export_type} [{e.status}]")
