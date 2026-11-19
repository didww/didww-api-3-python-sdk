"""
Inspects Emergency orders (2026-04-16).

Emergency orders are created server-side when an EmergencyCallingService
is activated or renewed — customers cannot POST them directly.

Usage: DIDWW_API_KEY=xxx python examples/orders_emergency.py
"""
from client_factory import create_client
from didww.enums import enum_value
from didww.query_params import QueryParams
from didww.resources.order_item.emergency_order_item import EmergencyOrderItem

client = create_client()

# List recent orders, filter for emergency
print("=== Recent Orders (filtering for Emergency) ===")
params = QueryParams().sort("-created_at").page(1, 50)
orders = client.orders().list(params).data

emergency_orders = [
    o for o in orders
    if any(isinstance(i, EmergencyOrderItem) for i in o.items or [])
]
print(f"Found {len(emergency_orders)} emergency orders out of {len(orders)} total")

for o in emergency_orders[:5]:
    print(f"\nOrder: {o.id}")
    print(f"  Reference: {o.reference}")
    print(f"  Status: {enum_value(o.status)}")
    print(f"  Amount: {o.amount}")
    print(f"  Created: {o.created_at}")

# Follow the link from ECS to order
print("\n=== Emergency Calling Service -> Order ===")
params = QueryParams().include("order")
services = client.emergency_calling_services().list(params).data
if services:
    svc = services[0]
    print(f"ECS {svc.id} ({svc.name})")
    if svc.order:
        print(f"  -> Order {svc.order.id} — status: {enum_value(svc.order.status)}, amount: {svc.order.amount}")
    else:
        print("  -> No order linked yet")
else:
    print("No emergency_calling_services on this account")
