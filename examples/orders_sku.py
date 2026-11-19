"""
Orders by SKU: orders DIDs of a DID group by SKU and quantity. The item is a
DidOrderItem with sku_id and qty only, so DIDWW picks the numbers. Then lists
the DIDs of the order.

To order a specific number see orders_available_dids.py and
orders_reservation_dids.py; orders_all_item_types.py puts every DID item
variant in one order.

Usage: DIDWW_API_KEY=xxx python examples/orders_sku.py
"""
from client_factory import create_client
from didww.enums import enum_value
from didww.query_params import QueryParams
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem

client = create_client()

# Find a DID group with its SKUs
print("=== Finding SKU ===")
params = QueryParams().include("stock_keeping_units").page(number=1, size=10)
did_groups = client.did_groups().list(params).data
group = next((g for g in did_groups if g.stock_keeping_units), None)
if group is None:
    raise SystemExit("No DID group with stock keeping units found")

sku = group.stock_keeping_units[0]
print(f"DID group: {group.id} ({group.area_name}, prefix {group.prefix})")
print(f"SKU: {sku.id} (monthly {sku.monthly_price}, {sku.channels_included_count} channels included)")

# Order two DIDs of that SKU
print("\n=== Creating Order by SKU ===")
item = DidOrderItem()
item.sku_id = sku.id
item.qty = 2

order = Order()
order.items = [item]
created = client.orders().create(order).data

print(f"Order ID: {created.id}")
print(f"  Amount: {created.amount}")
print(f"  Status: {enum_value(created.status)}")
print(f"  Reference: {created.reference}")
print(f"  Created at: {created.created_at}")
for ordered in created.items:
    print(f"  Item: type={ordered._type} sku={ordered.sku_id} qty={ordered.qty}"
          f" nrc={ordered.nrc} mrc={ordered.mrc}")

# Fetch the DIDs that belong to this order
did_params = QueryParams().filter("order.id", created.id)
dids = client.dids().list(did_params).data
print(f"\nDIDs in order ({len(dids)}):")
for did in dids:
    print(f"  {did.id} | {did.number}")
