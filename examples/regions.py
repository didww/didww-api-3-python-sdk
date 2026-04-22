"""
Regions: list regions, filter by country, and fetch a specific region.
Usage: DIDWW_API_KEY=xxx python examples/regions.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# Find a country to filter regions
print("=== Finding country ===")
params = QueryParams().filter("iso", "US")
countries = client.countries().list(params).data
if not countries:
    print("Country not found")
    raise SystemExit(1)

country = countries[0]
print(f"Selected country: {country.name}")

# Fetch regions filtered by country with included country relationship
print(f"\n=== Regions for {country.name} ===")
params = QueryParams().filter("country.id", country.id).include("country")
regions = client.regions().list(params).data

print(f"Found {len(regions)} regions")
for region in regions[:5]:
    print(f"  {region.id} - {region.name} ({region.iso})")

# Fetch a specific region
if regions:
    print("\n=== Specific Region ===")
    found = client.regions().find(regions[-1].id).data
    print(f"Found: {found.name} ({found.iso})")
