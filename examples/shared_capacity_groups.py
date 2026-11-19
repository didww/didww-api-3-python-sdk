"""
Shared Capacity Groups: creates a group in a capacity pool, lists the groups,
updates the new one and deletes it, also when a step fails.

Usage: DIDWW_API_KEY=xxx python examples/shared_capacity_groups.py
"""
import uuid

from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.capacity_pool import CapacityPool
from didww.resources.shared_capacity_group import SharedCapacityGroup

client = create_client()
suffix = uuid.uuid4().hex[:8]

# Get a capacity pool
pools = client.capacity_pools().list().data
if not pools:
    raise SystemExit("No capacity pools found")
pool = pools[0]
print(f"Capacity pool: {pool.name} ({pool.id})")

# Create a shared capacity group
group = SharedCapacityGroup()
group.name = f"My Channel Group {suffix}"
group.metered_channels_count = 10
group.shared_channels_count = 1
group.external_reference_id = f"python-scg-{suffix}"
group.capacity_pool = CapacityPool.build(pool.id)

created = client.shared_capacity_groups().create(group).data
try:
    print(f"\nCreated: {created.id}")
    print(f"  name: {created.name}")
    print(f"  metered: {created.metered_channels_count}")
    print(f"  shared: {created.shared_channels_count}")
    print(f"  external_reference_id: {created.external_reference_id}")

    # List shared capacity groups with their capacity pool
    params = QueryParams().include("capacity_pool")
    groups = client.shared_capacity_groups().list(params).data
    print(f"\nShared capacity groups ({len(groups)}):")
    for g in groups:
        pool_name = g.capacity_pool.name if g.capacity_pool else "unknown"
        print(f"  {g.name} shared={g.shared_channels_count} metered={g.metered_channels_count} pool={pool_name}")

    # Update: only the fields set here are sent
    update = SharedCapacityGroup.build(created.id)
    update.name = f"My Channel Group {suffix} (updated)"
    update.metered_channels_count = 5
    updated = client.shared_capacity_groups().update(update).data
    print(f"\nUpdated: {updated.name}, metered={updated.metered_channels_count}")
finally:
    client.shared_capacity_groups().delete(created.id)
    print("Deleted shared capacity group")
