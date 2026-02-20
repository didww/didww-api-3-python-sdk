from client_factory import create_client
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.resources.configuration.sip import SipConfiguration
from didww.exceptions import DidwwApiError

client = create_client()

# Create SIP configuration
sip = SipConfiguration()
sip.username = "username"
sip.host = "216.58.215.110"
sip.port = 5060
sip.codec_ids = [9, 10]
sip.transport_protocol_id = 1

# Create trunk
trunk = VoiceInTrunk()
trunk.name = "My New SIP Trunk"
trunk.configuration = sip
trunk.ringing_timeout = 30

try:
    created = client.voice_in_trunks().create(trunk).data
    print(f"Created trunk: {created.id}")
    print(f"  Name: {created.name}")
    print(f"  Created at: {created.created_at}")
    print(f"  Ringing timeout: {created.ringing_timeout}")

    # Delete the trunk
    client.voice_in_trunks().delete(created.id)
    print(f"  Deleted trunk {created.id}")
except DidwwApiError as e:
    print(f"API error (HTTP {e.status_code}): {e}")
