"""
Voice Out Trunks: CRUD operations.
Note: Voice Out Trunks and some OnCliMismatchAction values (e.g. REPLACE_CLI, RANDOMIZE_CLI)
require additional account configuration. Contact DIDWW support to enable.
Usage: DIDWW_API_KEY=xxx python examples/voice_out_trunks.py
"""
import uuid

from client_factory import create_client
from didww.enums import DefaultDstAction, OnCliMismatchAction
from didww.resources.voice_out_trunk import VoiceOutTrunk

client = create_client()
suffix = uuid.uuid4().hex[:8]

# Create a voice out trunk
trunk = VoiceOutTrunk()
trunk.name = f"My Outbound Trunk {suffix}"
trunk.allowed_sip_ips = ["0.0.0.0/0"]
trunk.default_dst_action = DefaultDstAction.ALLOW_ALL
trunk.on_cli_mismatch_action = OnCliMismatchAction.REJECT_CALL
created = client.voice_out_trunks().create(trunk).data
print(f"Created voice out trunk: {created.id}")
print(f"  name: {created.name}")
print(f"  username: {created.username}")
print(f"  password: {created.password}")
print(f"  status: {created.status}")

# List voice out trunks
trunks = client.voice_out_trunks().list().data
print(f"\nAll voice out trunks ({len(trunks)}):")
for t in trunks:
    print(f"  {t.name} ({t.status})")

# Update
update = VoiceOutTrunk.build(created.id)
update.name = "Updated Outbound Trunk"
update.allowed_sip_ips = ["10.0.0.0/8"]
updated = client.voice_out_trunks().update(update).data
print(f"\nUpdated name: {updated.name}")

# Delete
client.voice_out_trunks().delete(created.id)
print("Deleted voice out trunk")
