"""
Emergency Requirement Validations: validate emergency requirements (2026-04-16).
Create-only resource that checks whether an address + identity combination
meets the emergency requirements for a given country/region.

Usage: DIDWW_API_KEY=xxx python examples/emergency_requirement_validations.py
"""
from client_factory import create_client
from didww.resources.emergency_requirement_validation import EmergencyRequirementValidation
from didww.resources.emergency_requirement import EmergencyRequirement
from didww.resources.address import Address
from didww.resources.identity import Identity

client = create_client()

# Create an emergency requirement validation
print("=== Emergency Requirement Validation ===")
erv = EmergencyRequirementValidation()
# Set the relationships to the resources you want to validate
# erv.emergency_requirement = EmergencyRequirement.build("<emergency-requirement-id>")
# erv.address = Address.build("<address-id>")
# erv.identity = Identity.build("<identity-id>")
# response = client.emergency_requirement_validations().create(erv)
# print(f"Validation result: {response.data}")
print("(Uncomment the code above with valid IDs to run)")
