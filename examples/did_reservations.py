"""
DID Reservations: create, list, find, and delete.
Usage: DIDWW_API_KEY=xxx python examples/did_reservations.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.did_reservation import DidReservation

client = create_client()

# Get an available DID to reserve
ad_params = QueryParams().include("did_group.stock_keeping_units").page(number=1, size=1)
available_dids = client.available_dids().list(ad_params).data
if not available_dids:
    raise RuntimeError("No available DIDs found")
available_did = available_dids[0]
print(f"Reserving DID: {available_did.number}")

# Create a reservation
reservation = DidReservation()
reservation.description = "SDK example reservation"
reservation.available_did = available_did
reservation = client.did_reservations().create(reservation).data
print(f"Created reservation: {reservation.id}")
print(f"  description: {reservation.description}")
print(f"  expires at: {reservation.expire_at}")

# List reservations with includes
params = QueryParams().include("available_did")
reservations = client.did_reservations().list(params).data
print(f"\nAll reservations ({len(reservations)}):")
for r in reservations:
    number = r.available_did.number if r.available_did else "unknown"
    print(f"  {r.id} - {number}")

# Find by ID
found = client.did_reservations().find(reservation.id).data
print(f"\nFound reservation: {found.id}")

# Delete reservation
client.did_reservations().delete(reservation.id)
print("Deleted reservation")
