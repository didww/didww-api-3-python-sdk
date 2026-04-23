"""
Orders All Item Types: order with all 3 item types:
1. DidOrderItem - order by SKU and quantity (random DID)
2. AvailableDidOrderItem - order a specific available DID
3. ReservationDidOrderItem - order a previously reserved DID

Then fetches the ordered DIDs.

Usage: DIDWW_API_KEY=xxx python examples/orders_all_item_types.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem
from didww.resources.did_reservation import DidReservation

client = create_client()

# Find available DIDs with their DID group and SKUs
print("=== Finding Available DIDs ===")
params = QueryParams().include("did_group.stock_keeping_units")
available_dids = client.available_dids().list(params).data

if len(available_dids) < 2:
    print("Need at least 2 available DIDs for this example")
    raise SystemExit(1)

ad1 = available_dids[0]
ad2 = available_dids[1]
print(f"Available DID 1: {ad1.number}")
print(f"Available DID 2: {ad2.number}")

# Helper to get SKU from available DID
def get_sku(available_did):
    if not available_did.did_group or not available_did.did_group.stock_keeping_units:
        raise RuntimeError(f"No stock_keeping_units for available DID {available_did.id}")
    return available_did.did_group.stock_keeping_units[0]

sku1 = get_sku(ad1)
sku2 = get_sku(ad2)
print(f"SKU 1: {sku1.id}")
print(f"SKU 2: {sku2.id}")

# Get a SKU for the DidOrderItem (by quantity)
print("\n=== Finding SKU for quantity order ===")
dg_params = QueryParams().include("stock_keeping_units")
did_groups = client.did_groups().list(dg_params).data

sku_for_qty = None
for dg in did_groups:
    if dg.stock_keeping_units:
        sku_for_qty = dg.stock_keeping_units[0]
        print(f"SKU for qty order: {sku_for_qty.id}")
        break

if not sku_for_qty:
    print("No DID group with stock_keeping_units found")
    raise SystemExit(1)

# Reserve the second available DID
print("\n=== Reserving DID ===")
reservation = DidReservation()
reservation.description = "Reserved for all-item-types example"
reservation.available_did = ad2
reservation = client.did_reservations().create(reservation).data
print(f"Reservation: {reservation.id}")

# Build order with all three item types
print("\n=== Creating Orders with All Item Types ===")

# 1. DidOrderItem - order by SKU and quantity (random DID)
item_by_sku = DidOrderItem()
item_by_sku.sku_id = sku_for_qty.id
item_by_sku.qty = 1

# 2. AvailableDidOrderItem - order a specific available DID
item_by_available = AvailableDidOrderItem()
item_by_available.sku_id = sku1.id
item_by_available.available_did_id = ad1.id

# 3. ReservationDidOrderItem - order a previously reserved DID
item_by_reservation = ReservationDidOrderItem()
item_by_reservation.sku_id = sku2.id
item_by_reservation.did_reservation_id = reservation.id

# Note: each order must contain items of the SAME type only,
# so we create separate orders for each item type.
orders_created = []

# Order 1: By SKU
order1 = Order()
order1.items = [item_by_sku]
created1 = client.orders().create(order1).data
print(f"\nOrder by SKU: {created1.id}")
print(f"  Amount: {created1.amount}, Status: {created1.status.value}")
orders_created.append(created1)

# Order 2: By Available DID
order2 = Order()
order2.items = [item_by_available]
created2 = client.orders().create(order2).data
print(f"Order by Available DID: {created2.id}")
print(f"  Amount: {created2.amount}, Status: {created2.status.value}")
orders_created.append(created2)

# Order 3: By Reservation
order3 = Order()
order3.items = [item_by_reservation]
created3 = client.orders().create(order3).data
print(f"Order by Reservation: {created3.id}")
print(f"  Amount: {created3.amount}, Status: {created3.status.value}")
orders_created.append(created3)

# Fetch DIDs from all orders
print("\n=== DIDs Ordered ===")
total_dids = 0
for idx, order in enumerate(orders_created):
    did_params = QueryParams().filter("order.id", order.id)
    dids = client.dids().list(did_params).data
    print(f"Order {idx + 1} ({order.id}): {len(dids)} DID(s)")
    for did in dids:
        print(f"  - {did.number}")
    total_dids += len(dids)

print(f"\n=== Summary ===")
print("All three order item types demonstrated:")
print("  1. DidOrderItem(sku_id, qty) - order by SKU")
print("  2. AvailableDidOrderItem(available_did_id, sku_id) - order available DID")
print("  3. ReservationDidOrderItem(did_reservation_id, sku_id) - order reserved DID")
print(f"Total DIDs ordered: {total_dids}")
