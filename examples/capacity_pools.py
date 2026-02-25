"""
Capacity Pools: list with included shared capacity groups and qty-based pricings.
Usage: DIDWW_API_KEY=xxx python examples/capacity_pools.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# List capacity pools with includes
params = QueryParams().include("shared_capacity_groups", "qty_based_pricings")
pools = client.capacity_pools().list(params).data
print(f"Capacity pools ({len(pools)}):")

for pool in pools:
    print(f"\n  {pool.name}")
    print(f"    total channels: {pool.total_channels_count}")
    print(f"    assigned channels: {pool.assigned_channels_count}")
    print(f"    renew date: {pool.renew_date}")

    # Shared capacity groups (included)
    groups = pool.shared_capacity_groups or []
    if groups:
        print(f"    shared capacity groups ({len(groups)}):")
        for g in groups:
            print(f"      {g.name} shared={g.shared_channels_count} metered={g.metered_channels_count}")

    # Qty-based pricings (included)
    pricings = pool.qty_based_pricings or []
    if pricings:
        print(f"    qty-based pricings ({len(pricings)}):")
        for p in pricings:
            print(f"      qty={p.qty} setup={p.setup_price} monthly={p.monthly_price}")
