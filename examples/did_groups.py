from client_factory import create_client
from didww.enums import enum_value
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
    features = [enum_value(f) for f in (group.features or [])]
    print(f"  {group.id} | {group.area_name} | prefix={group.prefix}")
    # number_type is a NumberType value (local, national, mobile, toll_free, shared_cost, global)
    print(f"    number_type: {enum_value(group.number_type)}, is_demo: {group.is_demo}")
    print(f"    features: {features}")
    print(f"    allow_additional_channels: {group.allow_additional_channels}")
    print(f"    service_restrictions: {group.service_restrictions}")
