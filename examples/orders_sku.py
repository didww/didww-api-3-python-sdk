from client_factory import create_client
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.query_params import QueryParams

client = create_client()

# Find a DID group with stock keeping units
params = QueryParams().include("stock_keeping_units")
did_groups = client.did_groups().list(params).data
if not did_groups:
    print("No DID groups found")
    exit(1)

group = did_groups[0]
# sku_id would come from the included stock_keeping_units relationship
# For this example we use a placeholder
sku_id = "82460535-2b3f-4278-8c8d-62f3da0d9fa6"

# Create order item
item = DidOrderItem()
item.sku_id = sku_id
item.qty = 2

# Create order
order = Order()
order.items = [item]
created = client.orders().create(order).data

print(f"Order ID: {created.id}")
print(f"Amount: {created.amount}")
print(f"Status: {created.status}")
print(f"Created at: {created.created_at}")
print(f"Description: {created.description}")
print(f"Reference: {created.reference}")
print(f"Items count: {len(created.items)}")
