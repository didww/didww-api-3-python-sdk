"""
DIDs: list DIDs and display 2026-04-16 emergency fields and identity.
Updates DID routing/capacity by assigning trunk and capacity pool.

Usage: DIDWW_API_KEY=xxx python examples/dids.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.voice_in_trunk import VoiceInTrunk

client = create_client()

# Get DIDs with 2026-04-16 emergency relationships included
print("=== Finding last ordered DID ===")
params = QueryParams().include("identity", "emergency_calling_service", "emergency_verification")
dids = client.dids().list(params).data

if not dids:
    print("No DIDs found. Please order a DID first.")
    raise SystemExit(1)

did = dids[0]
print(f"Selected DID: {did.id}")
print(f"  Number: {did.number}")
print(f"  Emergency enabled: {did.emergency_enabled}")
if did.emergency_calling_service:
    print(f"  Emergency Calling Service: {did.emergency_calling_service.id}")
if did.emergency_verification:
    print(f"  Emergency Verification:    {did.emergency_verification.id}")
if did.identity:
    print(f"  Identity: {did.identity.id}")

# Get last SIP trunk
print("\n=== Finding SIP trunk ===")
trunks = client.voice_in_trunks().list(
    QueryParams().filter("configuration.type", "sip_configurations")
).data

if not trunks:
    print("No SIP trunks found. Please create a SIP trunk first.")
    raise SystemExit(1)

trunk = trunks[0]
print(f"Selected trunk: {trunk.name}")

# Assign trunk to DID
print("\n=== Assigning trunk to DID ===")
update = Did.build(did.id)
update.voice_in_trunk = VoiceInTrunk.build(trunk.id)
client.dids().update(update)
print(f"Assigned trunk: {trunk.name}")

# Assign capacity pool
print("\n=== Assigning capacity pool ===")
capacity_pools = client.capacity_pools().list().data

if capacity_pools:
    pool = capacity_pools[0]
    update = Did.build(did.id)
    update.capacity_pool = pool
    update.capacity_limit = 5
    update.description = "Updated by Python example"
    client.dids().update(update)
    print(f"DID {did.id}")
    print(f"  description: {update.description}")
    print(f"  capacity_limit: {update.capacity_limit}")
else:
    print("No capacity pools found")
