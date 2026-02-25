"""
Voice In Trunk Groups: CRUD operations with trunk relationships.
Usage: DIDWW_API_KEY=xxx python examples/voice_in_trunk_groups.py
"""
import uuid

from client_factory import create_client
from didww.enums import Codec, TransportProtocol
from didww.query_params import QueryParams
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.voice_in_trunk_group import VoiceInTrunkGroup
from didww.resources.configuration.sip import SipConfiguration

client = create_client()
suffix = uuid.uuid4().hex[:8]

# Get a POP for trunk creation
pops = client.pops().list().data
pop = pops[0]

# Create two trunks
sip_a = SipConfiguration()
sip_a.host = "sip-a.example.com"
sip_a.port = 5060
sip_a.codec_ids = [Codec.PCMU, Codec.PCMA]
sip_a.transport_protocol_id = TransportProtocol.UDP

trunk_a = VoiceInTrunk()
trunk_a.name = f"Group Trunk A {suffix}"
trunk_a.configuration = sip_a
trunk_a.pop = pop
trunk_a = client.voice_in_trunks().create(trunk_a).data
print(f"Created trunk A: {trunk_a.id}")

sip_b = SipConfiguration()
sip_b.host = "sip-b.example.com"
sip_b.port = 5060
sip_b.codec_ids = [Codec.PCMU]
sip_b.transport_protocol_id = TransportProtocol.UDP

trunk_b = VoiceInTrunk()
trunk_b.name = f"Group Trunk B {suffix}"
trunk_b.configuration = sip_b
trunk_b.pop = pop
trunk_b = client.voice_in_trunks().create(trunk_b).data
print(f"Created trunk B: {trunk_b.id}")

# Create a trunk group with both trunks
group = VoiceInTrunkGroup()
group.name = f"My Trunk Group {suffix}"
group.capacity_limit = 10
group.voice_in_trunks = [
    VoiceInTrunk.build(trunk_a.id),
    VoiceInTrunk.build(trunk_b.id),
]
group = client.voice_in_trunk_groups().create(group).data
print(f"Created trunk group: {group.id} - {group.name}")

# List trunk groups with included trunks
params = QueryParams().include("voice_in_trunks")
groups = client.voice_in_trunk_groups().list(params).data
print(f"\nAll trunk groups ({len(groups)}):")
for g in groups:
    trunks = g.voice_in_trunks or []
    print(f"  {g.name} ({len(trunks)} trunks)")

# Update group name
update = VoiceInTrunkGroup.build(group.id)
update.name = f"Updated Group {suffix}"
updated = client.voice_in_trunk_groups().update(update).data
print(f"\nUpdated name: {updated.name}")

# Cleanup: deleting the group cascades to delete assigned trunks
client.voice_in_trunk_groups().delete(group.id)
print("Deleted trunk group (cascaded to trunks)")
