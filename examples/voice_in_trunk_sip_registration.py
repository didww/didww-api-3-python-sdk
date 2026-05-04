"""End-to-end SIP registration flow on /voice_in_trunks (API 2026-04-16):
create with sip_registration enabled → rename → disable by setting `host`
→ re-enable by toggling the flag. Demonstrates how the SDK keeps the
dependent fields (`host`, `port`, `use_did_in_ruri`) aligned with the
server's validation rules. The sandbox trunk is left in place after the
script completes.

Usage: DIDWW_API_KEY=xxx python examples/voice_in_trunk_sip_registration.py
"""
import time
from client_factory import create_client
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.voice_in_trunk import VoiceInTrunk
from didww.enums import CliFormat, Codec, TransportProtocol

client = create_client()

print("=== Python SDK — SIP registration flow ===")

# 1) Create with sip_registration enabled.
print("\n[1/4] Create with sip_registration enabled...")
sip = SipConfiguration()
sip.enabled_sip_registration = True
sip.use_did_in_ruri = True
sip.cnam_lookup = False
sip.codec_ids = [Codec.PCMU, Codec.PCMA]
sip.transport_protocol_id = TransportProtocol.UDP

trunk = VoiceInTrunk()
trunk.name = f"py-sip-registration-{int(time.time())}"
trunk.priority = 1
trunk.weight = 100
trunk.cli_format = CliFormat.E164
trunk.ringing_timeout = 30
trunk.configuration = sip

created = client.voice_in_trunks().create(trunk).data
trunk_id = created.id
print(f"  id={trunk_id}")
print(f"  incoming_auth_username={created.configuration.incoming_auth_username!r}")
print(f"  incoming_auth_password={created.configuration.incoming_auth_password!r}")

# 2) Rename — single-field PATCH.
print("\n[2/4] Rename trunk...")
created.name = f"py-renamed-{int(time.time())}"
client.voice_in_trunks().update(created)
print(f"  name={created.name}")

# 3) Disable sip_registration by setting `host`.
print("\n[3/4] Disable by setting host...")
disable = SipConfiguration()
disable.host = "203.0.113.10"
update = VoiceInTrunk()
update.id = trunk_id
update.configuration = disable
client.voice_in_trunks().update(update)
fresh = client.voice_in_trunks().find(trunk_id).data
print(f"  enabled_sip_registration={fresh.configuration.enabled_sip_registration!r}")
print(f"  use_did_in_ruri={fresh.configuration.use_did_in_ruri!r}")
print(f"  host={fresh.configuration.host!r}")
print(f"  incoming_auth_username={fresh.configuration.incoming_auth_username!r}")

# 4) Re-enable sip_registration. The SDK should send host=None / port=None on
#    the wire so the server clears the values it had persisted.
print("\n[4/4] Re-enable by toggling enabled_sip_registration...")
re_enable = SipConfiguration()
re_enable.enabled_sip_registration = True
re_enable.use_did_in_ruri = True
update = VoiceInTrunk()
update.id = trunk_id
update.configuration = re_enable
try:
    client.voice_in_trunks().update(update)
    fresh = client.voice_in_trunks().find(trunk_id).data
    print(f"  enabled_sip_registration={fresh.configuration.enabled_sip_registration!r}")
    print(f"  host={fresh.configuration.host!r}")
    print(f"  incoming_auth_username={fresh.configuration.incoming_auth_username!r}")
    print(f"\n=== PASS — trunk {trunk_id} left in sandbox ===")
except Exception as e:
    print(f"  ✗ FAIL: {e}")
    print(f"\n=== FAIL at re-enable — trunk {trunk_id} left in sandbox ===")
