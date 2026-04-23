"""
Emergency Scenario: end-to-end Emergency Calling Service purchase flow (2026-04-16).

Demonstrates the full lifecycle:
0. Order an available DID with emergency feature
1. Find the newly ordered DID
2. Get emergency requirements for its country
3. Find an identity and address
4. Validate the emergency requirement
5. Create an emergency verification
6. Check verification status
7. Get the resulting emergency calling service

Usage: DIDWW_API_KEY=xxx python examples/emergency_scenario.py
"""
import time

from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.available_did import AvailableDid
from didww.resources.did import Did
from didww.resources.identity import Identity
from didww.resources.address import Address
from didww.resources.order import Order
from didww.resources.order_item.available_did_order_item import AvailableDidOrderItem
from didww.resources.emergency_requirement import EmergencyRequirement
from didww.resources.emergency_requirement_validation import EmergencyRequirementValidation
from didww.resources.emergency_verification import EmergencyVerification

client = create_client()

# --- Step 0: Order an available DID with emergency feature ---
print("=== Step 0: Order an available DID with emergency feature ===")

# Find address first to determine country
addresses = client.addresses().list(QueryParams().include("country")).data
if not addresses:
    raise SystemExit("No addresses on this account. Please create an address first.")
address = addresses[0]
address_country = address.country
print(f"  Address country: {address_country.name} ({address_country.id})")

# Find an available DID with emergency feature in that country
params = (QueryParams()
          .filter("did_group.features", "emergency")
          .filter("country.id", address_country.id)
          .include("did_group", "did_group.stock_keeping_units")
          .page(1, 1))
available_dids = client.available_dids().list(params).data
if not available_dids:
    raise SystemExit(f"No available DIDs with emergency feature in {address_country.name}.")

available_did = available_dids[0]
did_group = available_did.did_group
skus = did_group.stock_keeping_units
if not skus:
    raise SystemExit("No SKU found for this DID group.")
sku = skus[0]

print(f"  Available DID: {available_did.number}")
print(f"  DID Group: {did_group.area_name}")

# Order it
item = AvailableDidOrderItem()
item.sku_id = sku.id
item.available_did_id = available_did.id
order = Order()
order.items = [item]
response = client.orders().create(order)
created_order = response.data
print(f"  Order: {created_order.id} — {created_order.status}")

# Wait for order to complete
for _ in range(10):
    if created_order.status == "completed":
        break
    time.sleep(5)
    created_order = client.orders().find(created_order.id).data
if created_order.status != "completed":
    raise SystemExit(f"  Order did not complete (status: {created_order.status}).")
print("  Order completed")

# --- Step 1: Find the newly ordered DID ---
print("\n=== Step 1: Find the newly ordered DID ===")
params = (QueryParams()
          .filter("did_group.features", "emergency")
          .filter("emergency_enabled", "false")
          .include("did_group", "did_group.country", "did_group.did_group_type",
                   "emergency_calling_service")
          .sort("-created_at")
          .page(1, 10))
dids = client.dids().list(params).data

# Pick the first DID without an existing ECS
did = None
for d in dids:
    if not d.emergency_calling_service:
        did = d
        break
if not did:
    raise SystemExit("No available DID without an existing Emergency Calling Service.")

did_group = did.did_group
country = did_group.country
did_group_type = did_group.did_group_type

print(f"  DID: {did.number} ({did.id})")
print(f"  Country: {country.name} ({country.id})")
print(f"  DID Group Type: {did_group_type.name} ({did_group_type.id})")

# --- Step 2: Get emergency requirements ---
print("\n=== Step 2: Get emergency requirements ===")
params = (QueryParams()
          .filter("country.id", country.id)
          .filter("did_group_type.id", did_group_type.id))
requirements = client.emergency_requirements().list(params).data
if not requirements:
    raise SystemExit("No emergency requirements found for this country/did_group_type.")

requirement = requirements[0]
print(f"  Requirement: {requirement.id}")
print(f"  Identity type: {requirement.identity_type}")
print(f"  Address area level: {requirement.address_area_level}")

# --- Step 3: Find an identity and address ---
print("\n=== Step 3: Find identity and address ===")
identities = client.identities().list().data
if not identities:
    raise SystemExit("No identities available. Please create an identity first.")
identity = identities[0]
print(f"  Identity: {identity.id} ({identity.first_name} {identity.last_name})")
print(f"  Address: {address.id} ({address.city_name})")

# --- Step 4: Validate emergency requirement ---
print("\n=== Step 4: Validate emergency requirement ===")
validation = EmergencyRequirementValidation()
validation.emergency_requirement = EmergencyRequirement.build(requirement.id)
validation.address = Address.build(address.id)
validation.identity = Identity.build(identity.id)
client.emergency_requirement_validations().create(validation)
print("  Validation passed!")

# --- Step 5: Create emergency verification ---
print("\n=== Step 5: Create emergency verification ===")
verification = EmergencyVerification()
verification.callback_url = "https://example.com/callbacks/emergency"
verification.callback_method = "post"
verification.external_reference_id = f"python-scenario-{int(time.time())}"
verification.address = Address.build(address.id)
verification.dids = [Did.build(did.id)]
response = client.emergency_verifications().create(verification)
created_verification = response.data
print(f"  Created: {created_verification.id}")
print(f"  Reference: {created_verification.reference}")
print(f"  Status: {created_verification.status}")
print(f"  External Reference: {created_verification.external_reference_id}")

# --- Step 6: Check verification status ---
print("\n=== Step 6: Check verification status ===")
params = QueryParams().include("address", "emergency_calling_service", "dids")
fetched = client.emergency_verifications().find(created_verification.id, params).data
print(f"  Status: {fetched.status}")

# --- Step 7: Get emergency calling service ---
print("\n=== Step 7: Get emergency calling service ===")
ecs = fetched.emergency_calling_service
if ecs:
    print(f"  ECS: {ecs.id}")
    print(f"  Name: {ecs.name}")
    print(f"  Status: {ecs.status}")
    print(f"  Setup Price: {ecs.meta.get('setup_price')}")
    print(f"  Monthly Price: {ecs.meta.get('monthly_price')}")
else:
    print("  No ECS linked yet (verification may still be pending).")

print("\nDone!")
