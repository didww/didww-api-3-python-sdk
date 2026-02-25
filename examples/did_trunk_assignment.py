"""
Demonstrates exclusive trunk/trunk group assignment on DIDs.
Assigning a trunk auto-nullifies the trunk group and vice versa.
Usage: DIDWW_API_KEY=xxx python examples/did_trunk_assignment.py
"""
import uuid

from client_factory import create_client
from didww.enums import Codec, TransportProtocol
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup
from didww.resources.configuration.sip import SipConfiguration

client = create_client()
suffix = uuid.uuid4().hex[:8]

include_params = QueryParams().include("voice_in_trunk", "voice_in_trunk_group")


def print_did_assignment(did_id):
    result = client.dids().find(did_id, include_params).data
    trunk_id = result._relationship_id("voice_in_trunk")
    group_id = result._relationship_id("voice_in_trunk_group")
    print(f"   trunk = {trunk_id or 'null'}")
    print(f"   group = {group_id or 'null'}")


# Get a DID
did_params = QueryParams().include("voice_in_trunk", "voice_in_trunk_group").page(number=1, size=1)
dids = client.dids().list(did_params).data
if not dids:
    raise RuntimeError("No DIDs found. Order a DID first.")
did = dids[0]
print(f"Using DID: {did.number} ({did.id})")

# Get a POP
pop = client.pops().list().data[0]

# Create a trunk
sip = SipConfiguration()
sip.host = "sip.example.com"
sip.port = 5060
sip.codec_ids = [Codec.PCMU, Codec.PCMA]
sip.transport_protocol_id = TransportProtocol.UDP

trunk = VoiceInTrunk()
trunk.name = f"Assignment Trunk {suffix}"
trunk.configuration = sip
trunk.pop = pop
trunk = client.voice_in_trunks().create(trunk).data
print(f"Created trunk: {trunk.id}")

# Create a trunk group
group = VoiceInTrunkGroup()
group.name = f"Assignment Group {suffix}"
group.capacity_limit = 10
group = client.voice_in_trunk_groups().create(group).data
print(f"Created trunk group: {group.id}")

try:
    # 1. Assign trunk to DID (auto-nullifies trunk group)
    update1 = Did.build(did.id)
    update1.voice_in_trunk = VoiceInTrunk.build(trunk.id)
    client.dids().update(update1)
    print("\n1. Assigned trunk:")
    print_did_assignment(did.id)

    # 2. Assign trunk group to DID (auto-nullifies trunk)
    update2 = Did.build(did.id)
    update2.voice_in_trunk_group = VoiceInTrunkGroup.build(group.id)
    client.dids().update(update2)
    print("\n2. Assigned trunk group:")
    print_did_assignment(did.id)

    # 3. Re-assign trunk (auto-nullifies trunk group again)
    update3 = Did.build(did.id)
    update3.voice_in_trunk = VoiceInTrunk.build(trunk.id)
    client.dids().update(update3)
    print("\n3. Re-assigned trunk:")
    print_did_assignment(did.id)

    # 4. Update description only (trunk stays assigned)
    update4 = Did.build(did.id)
    update4.description = "DID with trunk assigned"
    client.dids().update(update4)
    print("\n4. Updated description only (trunk stays):")
    print_did_assignment(did.id)
finally:
    # Cleanup: reassign DID to group (frees trunk), delete trunk, then group
    try:
        cleanup = Did.build(did.id)
        cleanup.voice_in_trunk_group = VoiceInTrunkGroup.build(group.id)
        client.dids().update(cleanup)
    except Exception:
        pass
    try:
        client.voice_in_trunks().delete(trunk.id)
        print("\nDeleted trunk")
    except Exception as e:
        print(f"\nTrunk cleanup: {e}")
    try:
        client.voice_in_trunk_groups().delete(group.id)
        print("Deleted trunk group")
    except Exception as e:
        print(f"Trunk group still assigned to DID (expected): {e}")
