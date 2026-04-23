"""
Orders Reservation DIDs: reserve a DID then order it.
Usage: DIDWW_API_KEY=xxx python examples/orders_reservation_dids.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.order import Order
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem
from didww.resources.did_reservation import DidReservation

client = create_client()

# Get available DIDs with included DID group and SKUs
print("=== Finding Available DIDs ===")
params = QueryParams().include("did_group.stock_keeping_units")
available_dids = client.available_dids().list(params).data

if not available_dids:
    print("No available DIDs found")
    raise SystemExit(1)

available_did = available_dids[0]
print(f"Selected available DID: {available_did.number}")

# Get SKU from the included DID group
if not available_did.did_group or not available_did.did_group.stock_keeping_units:
    print("No stock_keeping_units found in included did_group")
    raise SystemExit(1)

sku = available_did.did_group.stock_keeping_units[0]

# Reserve the selected DID
print("\n=== Reserving DID ===")
reservation = DidReservation()
reservation.description = "Reserved for order example"
reservation.available_did = available_did

reservation = client.did_reservations().create(reservation).data
print(f"Reserved: {available_did.number}")
print(f"  Reservation ID: {reservation.id}")
print(f"  Expires: {reservation.expires_at}")

# Purchase reserved DID
print("\n=== Creating Order from Reservation ===")
item = ReservationDidOrderItem()
item.did_reservation_id = reservation.id
item.sku_id = sku.id

order = Order()
order.items = [item]

created = client.orders().create(order).data
print(f"Order {created.id}")
print(f"  Status: {created.status.value}")
print(f"  Amount: {created.amount}")
print(f"  Items: {len(created.items)}")
if created.items:
    print(f"  Item type: {created.items[0]._type}")
