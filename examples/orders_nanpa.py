from client_factory import create_client
from didww.resources.order import Order
from didww.resources.order_item.did_order_item import DidOrderItem
from didww.query_params import QueryParams

client = create_client()

# Step 1: find the NANPA prefix by NPA/NXX (e.g. 201-221)
params = QueryParams().filter("npanxx", "201221").page(number=1, size=1)
nanpa_prefixes = client.nanpa_prefixes().list(params).data
if not nanpa_prefixes:
    print("NANPA prefix 201-221 not found")
    exit(1)

nanpa_prefix = nanpa_prefixes[0]
print(f"NANPA prefix: {nanpa_prefix.id} NPA={nanpa_prefix.npa} NXX={nanpa_prefix.nxx}")

# Step 2: find a DID group for this prefix and load its SKUs
dg_params = QueryParams().filter("nanpa_prefix.id", nanpa_prefix.id).include("stock_keeping_units").page(number=1, size=1)
did_groups = client.did_groups().list(dg_params).data
if not did_groups or not did_groups[0].stock_keeping_units:
    print("No DID group with SKUs found for this NANPA prefix")
    exit(1)

sku = did_groups[0].stock_keeping_units[0]
print(f"DID group: {did_groups[0].id} SKU: {sku.id} (monthly={sku.monthly_price})")

# Step 3: create the order
item = DidOrderItem()
item.sku_id = sku.id
item.nanpa_prefix_id = nanpa_prefix.id
item.qty = 1

order = Order()
order.allow_back_ordering = True
order.items = [item]
created = client.orders().create(order).data

print(f"Order {created.id} amount={created.amount} status={created.status.value} ref={created.reference}")
