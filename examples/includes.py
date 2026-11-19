"""
Includes: reads resources with their related resources included.

An included relationship reads as a full resource object (region.country.name),
or a list of them for a to-many relationship. A relationship that was not
included reads as None, a to-many one too: the API sends only its links. So
include every relationship you read. Once included, an empty relationship reads
as None (to-one) or [] (to-many). A nested path such as
did_group.stock_keeping_units also includes the relationships of an included
resource.

Usage: DIDWW_API_KEY=xxx python examples/includes.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# --- The same relationship, not included and included ---
print("=== Region without and with include=country ===")
regions = client.regions().list(QueryParams().page(number=1, size=1)).data
if regions:
    region = regions[0]
    print(f"  not included: {region.name} -> country = {region.country}")
    region = client.regions().find(region.id, QueryParams().include("country")).data
    print(f"  included:     {region.name} -> country = {region.country.name} ({region.country.iso})")

# --- Regions with included country ---
print("\n=== Regions with country ===")
params = QueryParams().include("country").page(number=1, size=3)
for region in client.regions().list(params).data:
    country = region.country
    print(f"  {region.name} ({region.iso}) - country: {country.name if country else None}")

# --- DID groups with included stock keeping units (a to-many relationship) ---
print("\n=== DID groups with SKUs ===")
params = QueryParams().include("stock_keeping_units").page(number=1, size=3)
for group in client.did_groups().list(params).data:
    skus = group.stock_keeping_units or []
    print(f"  {group.prefix} {group.area_name} - {len(skus)} SKU(s)")
    for sku in skus:
        print(f"    {sku.id}: monthly {sku.monthly_price}, setup {sku.setup_price},"
              f" {sku.channels_included_count} channels included")

# --- Available DIDs with a nested include ---
print("\n=== Available DIDs with did_group.stock_keeping_units ===")
params = QueryParams().include("did_group.stock_keeping_units").page(number=1, size=3)
for available in client.available_dids().list(params).data:
    group = available.did_group
    skus = (group.stock_keeping_units or []) if group else []
    group_name = f"{group.prefix} {group.area_name}" if group else None
    print(f"  {available.number} - group: {group_name}, {len(skus)} SKU(s)")

# --- DIDs with their Voice IN trunk ---
print("\n=== DIDs with voice_in_trunk ===")
params = QueryParams().include("voice_in_trunk").page(number=1, size=3)
for did in client.dids().list(params).data:
    trunk = did.voice_in_trunk
    # None here means the DID has no trunk: the relationship was included
    print(f"  {did.number} - trunk: {trunk.name if trunk else '(none)'}")
