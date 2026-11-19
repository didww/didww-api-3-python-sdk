"""
Orders All Item Types: ONE order with the three DID item variants:
1. DidOrderItem - by SKU and quantity (DIDWW picks the number)
2. AvailableDidOrderItem - a specific available DID
3. ReservationDidOrderItem - a previously reserved DID

All three are did_order_items on the wire, so they fit in one order. A
CapacityOrderItem cannot share an order with DID items (the API answers
"items - should have same type"): buy capacity in an order of its own, see
orders_capacity.py.

Then fetches the ordered DIDs.

Usage: DIDWW_API_KEY=xxx python examples/orders_all_item_types.py
"""
from client_factory import create_client
from didww.enums import enum_value
from didww.query_params import QueryParams
from didww.resources.available_did import AvailableDid
from didww.resources.did_reservation import DidReservation
from didww.resources.order import Order
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.resources.order_item.reservation_did_order_item import ReservationDidOrderItem

client = create_client()


def first_sku(available_did):
    did_group = available_did.did_group
    if not did_group or not did_group.stock_keeping_units:
        raise SystemExit(f"No stock keeping units for available DID {available_did.id}")
    return did_group.stock_keeping_units[0]


# --- Find two available DIDs with their DID group and SKUs ---
print("=== Finding Available DIDs ===")
params = QueryParams().include("did_group.stock_keeping_units").page(number=1, size=50)
available_dids = client.available_dids().list(params).data
if len(available_dids) < 3:
    raise SystemExit("Need at least 3 available DIDs for this example")

ad1 = available_dids[0]
ad2 = available_dids[1]
sku1 = first_sku(ad1)
sku2 = first_sku(ad2)
print(f"Available DID 1: {ad1.number} sku={sku1.id} - for AvailableDidOrderItem")
print(f"Available DID 2: {ad2.number} sku={sku2.id} - for ReservationDidOrderItem")

# --- Find a SKU for the order by quantity ---
# From the DID group of another available DID, so that the group has numbers in stock;
# a group other than those of DIDs 1 and 2 keeps DIDWW from picking one of them
print("\n=== Finding SKU for Quantity Order ===")
others = [a for a in available_dids[2:] if a.did_group and a.did_group.stock_keeping_units]
used_groups = {ad1.did_group.id, ad2.did_group.id}
source = next((a for a in others if a.did_group.id not in used_groups), others[0] if others else None)
if source is None:
    raise SystemExit("No other available DID with stock keeping units found")
group = source.did_group
sku_for_qty = group.stock_keeping_units[0]
print(f"SKU for qty order: {sku_for_qty.id} (group={group.id})")

# --- Reserve the second available DID ---
print("\n=== Reserving DID ===")
reservation = DidReservation()
reservation.description = "Reserved for all-item-types example"
reservation.available_did = AvailableDid.build(ad2.id)
reservation = client.did_reservations().create(reservation).data
print(f"Reservation: {reservation.id} (expires at {reservation.expires_at})")

# --- One order with the three DID item variants ---
print("\n=== Creating Order with All DID Item Types ===")

# 1. By SKU and quantity
item_by_sku = DidOrderItem()
item_by_sku.sku_id = sku_for_qty.id
item_by_sku.qty = 1

# 2. A specific available DID
item_by_available = AvailableDidOrderItem()
item_by_available.sku_id = sku1.id
item_by_available.available_did_id = ad1.id

# 3. A reserved DID
item_by_reservation = ReservationDidOrderItem()
item_by_reservation.sku_id = sku2.id
item_by_reservation.did_reservation_id = reservation.id

order = Order()
order.items = [item_by_sku, item_by_available, item_by_reservation]
order.external_reference_id = "python-sdk-all-item-types"
created = client.orders().create(order).data

print(f"Order ID: {created.id}")
print(f"  Amount: {created.amount}")
print(f"  Status: {enum_value(created.status)}")
print(f"  Reference: {created.reference}")
print(f"  External reference ID: {created.external_reference_id}")
print(f"  Items: {len(created.items)}")
for i, item in enumerate(created.items, start=1):
    print(f"    Item {i}: type={item._type}")

# --- Fetch the DIDs of the order ---
did_params = QueryParams().filter("order.id", created.id)
dids = client.dids().list(did_params).data
print(f"\nDIDs in order ({len(dids)}):")
for did in dids:
    print(f"  {did.id} | {did.number}")
