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
    print(f"  {group.id} | {group.area_name} | prefix={group.prefix}")
