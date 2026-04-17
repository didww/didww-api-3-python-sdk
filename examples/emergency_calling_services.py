"""
Emergency Calling Services: list and delete (2026-04-16).
Emergency calling services are created via the emergency verification flow,
not directly.

Usage: DIDWW_API_KEY=xxx python examples/emergency_calling_services.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# List emergency calling services
print("=== Emergency Calling Services ===")
params = QueryParams().include("country")
services = client.emergency_calling_services().list(params).data
print(f"Found {len(services)} emergency calling services")

for svc in services[:10]:
    country = svc.country
    country_name = country.name if country else "N/A"
    print(f"  {svc.id}  status={svc.status}  country={country_name}")
