"""
Address Verifications: create, list, and update (2026-04-16).

Usage: DIDWW_API_KEY=xxx python examples/address_verifications.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.address_verification import AddressVerification
from didww.resources.address import Address
from didww.resources.did import Did

client = create_client()

# List address verifications with included address and dids
print("=== Address Verifications ===")
params = QueryParams().include("address", "dids")
verifications = client.address_verifications().list(params).data
print(f"Found {len(verifications)} address verifications")

for av in verifications[:5]:
    print(f"  {av.id}  status={av.status}  ref={av.reference}")
    print(f"    external_reference_id: {av.external_reference_id}")
    print(f"    reject_reasons: {av.reject_reasons}")
    print(f"    reject_comment: {av.reject_comment}")
    if av.address:
        print(f"    address city: {av.address.city_name}")
    dids = av.dids or []
    print(f"    dids: {[d.number for d in dids]}")
    print()
