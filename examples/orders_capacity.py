"""
Orders Capacity: purchase capacity by creating a capacity order item.
Usage: DIDWW_API_KEY=xxx python examples/orders_capacity.py
"""
from client_factory import create_client
from didww.resources.order import Order
from didww.resources.order_item.capacity_order_item import CapacityOrderItem

client = create_client()

# Get capacity pools
print("=== Finding Capacity Pools ===")
pools = client.capacity_pools().list().data

if not pools:
    print("No capacity pools found")
    raise SystemExit(1)

pool = pools[0]
print(f"Selected capacity pool: {pool.name}")
print(f"  Monthly price: {pool.monthly_price}")
print(f"  Metered rate: {pool.metered_rate}")

# Purchase capacity
print("\n=== Creating Capacity Order ===")
item = CapacityOrderItem()
item.capacity_pool_id = pool.id
item.qty = 1

order = Order()
order.items = [item]

created = client.orders().create(order).data
print(f"Order {created.id}")
print(f"  Status: {created.status.value}")
print(f"  Amount: {created.amount}")
print(f"  Items: {len(created.items)}")
