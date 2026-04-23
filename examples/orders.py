"""
Orders: list orders, create and cancel a DID order.
Usage: DIDWW_API_KEY=xxx python examples/orders.py
"""
import uuid

from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem

client = create_client()

# List orders
print("=== Existing Orders ===")
orders = client.orders().list().data
print(f"Found {len(orders)} orders")

for order in orders[:3]:
    items_desc = ", ".join(item._type for item in order.items) if order.items else ""
    print(f"Order {order.id}: {order.status.value} (${order.amount})")
    if items_desc:
        print(f"  Items: {items_desc}")
    if order.external_reference_id:
        print(f"  External reference: {order.external_reference_id}")

# Create an order with DID order items
print("\n=== Creating DID Order ===")
params = QueryParams().include("stock_keeping_units")
did_groups = client.did_groups().list(params).data

sku_id = None
for dg in did_groups:
    if dg.stock_keeping_units:
        sku_id = dg.stock_keeping_units[0].id
        break

if not sku_id:
    print("No DID group with stock_keeping_units found")
    raise SystemExit(1)

item = DidOrderItem()
item.sku_id = sku_id
item.qty = 1

suffix = uuid.uuid4().hex[:8]
order = Order()
order.allow_back_ordering = False
order.items = [item]
order.external_reference_id = f"python-order-{suffix}"

created = client.orders().create(order).data
print(f"Created order: {created.id} - {created.status.value}")
print(f"  Amount: {created.amount}")
print(f"  Reference: {created.reference}")
print(f"  External reference: {created.external_reference_id}")

# Cancel order (delete it)
print("\n=== Cancelling Order ===")
client.orders().delete(created.id)
print("Order canceled")
