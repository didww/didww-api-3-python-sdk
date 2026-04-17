"""
Orders with Emergency Order Items (2026-04-16).
Demonstrates creating an order that includes an emergency calling service.

Usage: DIDWW_API_KEY=xxx python examples/orders_emergency.py
"""
from client_factory import create_client
from didww.resources.order import Order
from didww.resources.order_item.emergency_order_item import EmergencyOrderItem

client = create_client()

# Create an order with an emergency order item
print("=== Creating Emergency Order ===")
item = EmergencyOrderItem()
item.qty = 1
# Replace with a real emergency_calling_service_id
# item.emergency_calling_service_id = "<emergency-calling-service-id>"

order = Order()
order.allow_back_ordering = True
order.items = [item]
order.external_reference_id = "emergency-order-001"

# Uncomment to create:
# created = client.orders().create(order).data
# print(f"Created order: {created.id}")
# print(f"  status: {created.status}")
# print(f"  external_reference_id: {created.external_reference_id}")
# for i, oi in enumerate(created.items):
#     print(f"  item {i}: type={type(oi).__name__}")
print("(Uncomment the code above with valid IDs to run)")
