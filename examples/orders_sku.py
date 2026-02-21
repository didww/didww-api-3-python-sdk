from client_factory import create_client
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem
from didww.resources.did_reservation import DidReservation
from didww.resources.available_did import AvailableDid
from didww.query_params import QueryParams

client = create_client()

# --- Find available DIDs with their DID group and SKUs ---
params = QueryParams().include("did_group.stock_keeping_units")
available_dids = client.available_dids().list(params).data
if len(available_dids) < 2:
    print("Need at least 2 available DIDs for this example")
    exit(1)

ad1 = available_dids[0]
ad2 = available_dids[1]
sku_id_1 = ad1.did_group.stock_keeping_units[0].id
sku_id_2 = ad2.did_group.stock_keeping_units[0].id
print(f"Available DID 1: {ad1.id} ({ad1.number}) sku={sku_id_1} - for AvailableDidOrderItem")
print(f"Available DID 2: {ad2.id} ({ad2.number}) sku={sku_id_2} - for reservation")

# --- Get a separate SKU for the DidOrderItem (by quantity) ---
# Use a DID group to avoid conflicts with ad1's available DID pool
dg_params = QueryParams().include("stock_keeping_units")
did_groups = client.did_groups().list(dg_params).data
sku_for_qty = None
for group in did_groups:
    skus = group.stock_keeping_units
    if skus:
        sku_for_qty = skus[0].id
        print(f"SKU for qty order: {sku_for_qty} (group={group.id})")
        break

if not sku_for_qty:
    print("No DID group with stock keeping units found")
    exit(1)

# --- Reserve the second available DID ---
reservation = DidReservation()
reservation.description = "Reserved for order example"
reservation.available_did = AvailableDid.build(ad2.id)
reservation = client.did_reservations().create(reservation).data
print(f"Reservation: {reservation.id}")

# --- Build order with all three item types ---

# 1. DidOrderItem - order by SKU and quantity (random DID)
item_by_sku = DidOrderItem()
item_by_sku.sku_id = sku_for_qty
item_by_sku.qty = 1

# 2. AvailableDidOrderItem - order a specific available DID
item_by_available = AvailableDidOrderItem()
item_by_available.sku_id = sku_id_1
item_by_available.available_did_id = ad1.id

# 3. ReservationDidOrderItem - order a previously reserved DID
item_by_reservation = ReservationDidOrderItem()
item_by_reservation.sku_id = sku_id_2
item_by_reservation.did_reservation_id = reservation.id

order = Order()
order.items = [item_by_sku, item_by_available, item_by_reservation]
created = client.orders().create(order).data

print(f"\nOrder ID: {created.id}")
print(f"Amount: {created.amount}")
print(f"Status: {created.status}")
print(f"Created at: {created.created_at}")
print(f"Reference: {created.reference}")
print(f"Items count: {len(created.items)}")
for i, item in enumerate(created.items):
    print(f"  Item {i+1}: type={item._type}")

# --- Fetch DIDs that belong to this order ---
did_params = QueryParams().filter("order.id", created.id)
dids = client.dids().list(did_params).data
print(f"\nDIDs in order ({len(dids)}):")
for did in dids:
    print(f"  {did.id} | {did.number} | capacity_limit={did.capacity_limit}")
