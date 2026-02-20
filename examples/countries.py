from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# Fetch countries collection with filter
params = QueryParams().filter("prefix", "1").sort("name")
countries = client.countries().list(params).data
for country in countries:
    print(f"  {country.id} | {country.name} | prefix={country.prefix} | iso={country.iso}")

# Fetch the specific country
us_uuid = "1f6fc2bd-f081-4202-9b1a-d9cb88d942b9"
country = client.countries().find(us_uuid).data
print(f"\nFetched country: {country.name} ({country.iso}), prefix={country.prefix}")
