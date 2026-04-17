"""
Emergency Requirements: list and inspect emergency requirements (2026-04-16).
Read-only resource. Emergency requirements define what documentation is needed
for emergency calling services in specific countries/regions.

Usage: DIDWW_API_KEY=xxx python examples/emergency_requirements.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# List emergency requirements
print("=== Emergency Requirements ===")
params = QueryParams().include("country")
requirements = client.emergency_requirements().list(params).data
print(f"Found {len(requirements)} emergency requirements")

for req in requirements[:10]:
    country = req.country
    country_name = country.name if country else "N/A"
    print(f"  {req.id}  country={country_name}")
