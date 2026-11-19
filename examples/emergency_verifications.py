"""
Emergency Verifications: list with the address and DIDs included (2026-04-16).

Usage: DIDWW_API_KEY=xxx python examples/emergency_verifications.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# List emergency verifications
print("=== Emergency Verifications ===")
params = QueryParams().include("address", "dids")
verifications = client.emergency_verifications().list(params).data
print(f"Found {len(verifications)} emergency verifications")

for ev in verifications[:5]:
    print(f"  {ev.id}  status={ev.status}  ref={ev.reference}")
    print(f"    external_reference_id: {ev.external_reference_id}")
    print(f"    reject_reasons: {ev.reject_reasons}")
    print(f"    reject_comment: {ev.reject_comment}")
