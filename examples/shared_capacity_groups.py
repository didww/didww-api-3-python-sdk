"""
Shared Capacity Groups: create and delete.
Usage: DIDWW_API_KEY=xxx python examples/shared_capacity_groups.py
"""
import uuid

from client_factory import create_client
from didww.resources.capacity_pool import CapacityPool
from didww.resources.shared_capacity_group import SharedCapacityGroup

client = create_client()
suffix = uuid.uuid4().hex[:8]

# Get a capacity pool
pool = client.capacity_pools().list().data[0]

# Create a shared capacity group
group = SharedCapacityGroup()
group.name = f"My Channel Group {suffix}"
group.metered_channels_count = 10
group.shared_channels_count = 1
group.capacity_pool = CapacityPool.build(pool.id)

created = client.shared_capacity_groups().create(group).data
print(f"Created: {created.id}")
print(f"  name: {created.name}")
print(f"  metered: {created.metered_channels_count}")
print(f"  shared: {created.shared_channels_count}")

# Delete
client.shared_capacity_groups().delete(created.id)
print("Deleted shared capacity group")
