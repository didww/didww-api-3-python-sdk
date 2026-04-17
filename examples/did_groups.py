from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# Fetch DID groups with included stock keeping units
params = (
    QueryParams()
    .include("stock_keeping_units")
    .filter("area_name", "Beverly Hills")
)
did_groups = client.did_groups().list(params).data
for group in did_groups:
    features = [f.value if hasattr(f, 'value') else str(f) for f in (group.features or [])]
    print(f"  {group.id} | {group.area_name} | prefix={group.prefix}")
    print(f"    features: {features}")
    print(f"    allow_additional_channels: {group.allow_additional_channels}")
    print(f"    service_restrictions: {group.service_restrictions}")
