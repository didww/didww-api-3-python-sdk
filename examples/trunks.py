import uuid

from client_factory import create_client
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.configuration.pstn import PstnConfiguration
from didww.exceptions import DidwwApiError

client = create_client()
suffix = uuid.uuid4().hex[:8]

# --- Create SIP trunk ---
sip = SipConfiguration()
sip.username = "username"
sip.host = "216.58.215.110"
sip.port = 5060
sip.codec_ids = [9, 10]
sip.transport_protocol_id = 1

trunk = VoiceInTrunk()
trunk.name = f"My New SIP Trunk {suffix}"
trunk.configuration = sip
trunk.ringing_timeout = 30

try:
    created = client.voice_in_trunks().create(trunk).data
    print(f"Created SIP trunk: {created.id}")
    print(f"  Name: {created.name}")
    print(f"  Config type: {created.configuration._type}")
    print(f"  Created at: {created.created_at}")
    print(f"  Ringing timeout: {created.ringing_timeout}")

    client.voice_in_trunks().delete(created.id)
    print(f"  Deleted trunk {created.id}")
except DidwwApiError as e:
    print(f"API error (HTTP {e.status_code}): {e}")

# --- Create PSTN trunk ---
pstn = PstnConfiguration()
pstn.dst = "12125551234"

trunk = VoiceInTrunk()
trunk.name = f"My New PSTN Trunk {suffix}"
trunk.configuration = pstn
trunk.ringing_timeout = 30

try:
    created = client.voice_in_trunks().create(trunk).data
    print(f"\nCreated PSTN trunk: {created.id}")
    print(f"  Name: {created.name}")
    print(f"  Config type: {created.configuration._type}")
    print(f"  DST: {created.configuration.dst}")
    print(f"  Created at: {created.created_at}")
    print(f"  Ringing timeout: {created.ringing_timeout}")

    client.voice_in_trunks().delete(created.id)
    print(f"  Deleted trunk {created.id}")
except DidwwApiError as e:
    print(f"API error (HTTP {e.status_code}): {e}")
