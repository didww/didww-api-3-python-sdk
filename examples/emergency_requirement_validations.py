"""
Emergency Requirement Validations: validate emergency requirements (2026-04-16).

Picks the first available emergency requirement, address, and identity
from the account and validates whether they can be used together.

Usage: DIDWW_API_KEY=xxx python examples/emergency_requirement_validations.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.emergency_requirement_validation import EmergencyRequirementValidation
from didww.resources.emergency_requirement import EmergencyRequirement
from didww.resources.address import Address
from didww.resources.identity import Identity

client = create_client()

print("=== Emergency Requirement Validation ===")

# Pick first available requirement, address, identity
requirements = client.emergency_requirements().list(QueryParams().include("country")).data
if not requirements:
    raise SystemExit("No emergency requirements found on this account.")
requirement = requirements[0]
country = requirement.country
print(f"  Requirement: {requirement.id} (country: {country.name if country else 'N/A'})")

addresses = client.addresses().list().data
if not addresses:
    raise SystemExit("No addresses found on this account.")
address = addresses[0]
print(f"  Address: {address.id} ({address.city_name})")

identities = client.identities().list().data
if not identities:
    raise SystemExit("No identities found on this account.")
identity = identities[0]
print(f"  Identity: {identity.id} ({identity.first_name} {identity.last_name})")

# Validate
validation = EmergencyRequirementValidation()
validation.emergency_requirement = EmergencyRequirement.build(requirement.id)
validation.address = Address.build(address.id)
validation.identity = Identity.build(identity.id)

try:
    client.emergency_requirement_validations().create(validation)
    print("\nValidation passed — this combination can be used for emergency calling.")
except Exception as e:
    print(f"\nValidation failed: {e}")
    print("(This is expected if the address/identity don't match the requirement's country.)")
