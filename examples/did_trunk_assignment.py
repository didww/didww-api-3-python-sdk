"""
Demonstrates exclusive trunk/trunk group assignment on DIDs.
Assigning a trunk auto-nullifies the trunk group and vice versa.
At the end the DID's original voice routing and description are restored and
the created trunk and trunk group are deleted, also when a step fails.
Usage: DIDWW_API_KEY=xxx python examples/did_trunk_assignment.py
"""
import uuid

from client_factory import create_client
from didww.enums import Codec, Pop, TransportProtocol
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
    trunk = result.voice_in_trunk
    group = result.voice_in_trunk_group
    print(f"   trunk = {trunk.id if trunk else 'null'}")
    print(f"   group = {group.id if group else 'null'}")


def restore_did(did_id, trunk_id, group_id, description):
    restore = Did.build(did_id)
    if trunk_id is not None:
        restore.voice_in_trunk = VoiceInTrunk.build(trunk_id)
    elif group_id is not None:
        restore.voice_in_trunk_group = VoiceInTrunkGroup.build(group_id)
    else:
        # None unassigns only that relationship, so both are set
        restore.voice_in_trunk = None
        restore.voice_in_trunk_group = None
    restore.description = description
    client.dids().update(restore)
    print("\nRestored the DID's original routing:")
    print_did_assignment(did_id)


# Get a DID
did_params = QueryParams().include("voice_in_trunk", "voice_in_trunk_group").page(number=1, size=1)
dids = client.dids().list(did_params).data
if not dids:
    raise SystemExit("No DIDs found. Order a DID first.")
did = dids[0]
print(f"Using DID: {did.number} ({did.id})")
print(f"  Emergency enabled: {did.emergency_enabled}")

# Remember the current routing and description to put them back at the end
original_trunk_id = did.voice_in_trunk.id if did.voice_in_trunk else None
original_group_id = did.voice_in_trunk_group.id if did.voice_in_trunk_group else None
original_description = did.description

trunk_id = None
group_id = None
did_changed = False
try:
    # Create a trunk
    sip = SipConfiguration()
    sip.host = "sip.example.com"
    sip.port = 5060
    sip.codec_ids = [Codec.PCMU, Codec.PCMA]
    sip.transport_protocol_id = TransportProtocol.UDP

    trunk = VoiceInTrunk()
    trunk.name = f"Assignment Trunk {suffix}"
    trunk.configuration = sip
    trunk.pop = Pop.FRA  # optional; leave it unset to let DIDWW choose
    trunk_id = client.voice_in_trunks().create(trunk).data.id
    print(f"Created trunk: {trunk_id}")

    # Create a trunk group
    group = VoiceInTrunkGroup()
    group.name = f"Assignment Group {suffix}"
    group.capacity_limit = 10
    group_id = client.voice_in_trunk_groups().create(group).data.id
    print(f"Created trunk group: {group_id}")

    # 1. Assign trunk to DID (auto-nullifies trunk group)
    did_changed = True
    update1 = Did.build(did.id)
    update1.voice_in_trunk = VoiceInTrunk.build(trunk_id)
    client.dids().update(update1)
    print("\n1. Assigned trunk:")
    print_did_assignment(did.id)

    # 2. Assign trunk group to DID (auto-nullifies trunk)
    update2 = Did.build(did.id)
    update2.voice_in_trunk_group = VoiceInTrunkGroup.build(group_id)
    client.dids().update(update2)
    print("\n2. Assigned trunk group:")
    print_did_assignment(did.id)

    # 3. Re-assign trunk (auto-nullifies trunk group again)
    update3 = Did.build(did.id)
    update3.voice_in_trunk = VoiceInTrunk.build(trunk_id)
    client.dids().update(update3)
    print("\n3. Re-assigned trunk:")
    print_did_assignment(did.id)

    # 4. Update the description only: only changed fields are sent, so the trunk stays
    update4 = Did.build(did.id)
    update4.description = "DID with trunk assigned"
    client.dids().update(update4)
    print("\n4. Updated description only (trunk stays):")
    print_did_assignment(did.id)
finally:
    try:
        # Restore the DID first, so the created trunk and group are no longer in use
        if did_changed:
            restore_did(did.id, original_trunk_id, original_group_id, original_description)
    finally:
        try:
            if trunk_id is not None:
                client.voice_in_trunks().delete(trunk_id)
                print("Deleted trunk")
        finally:
            if group_id is not None:
                client.voice_in_trunk_groups().delete(group_id)
                print("Deleted trunk group")
