"""
Voice Out Trunks: CRUD operations using 2026-04-16 polymorphic authentication_method.
Note: Voice Out Trunks and some OnCliMismatchAction values (e.g. REPLACE_CLI, RANDOMIZE_CLI)
require additional account configuration. Contact DIDWW support to enable.
Usage: DIDWW_API_KEY=xxx python examples/voice_out_trunks.py
"""
import uuid

from client_factory import create_client
from didww.enums import DefaultDstAction, IceMode, OnCliMismatchAction, VoiceOutCodec, enum_value, enum_value_list
from didww.resources.voice_out_trunk import VoiceOutTrunk
from didww.resources.authentication_method import (
    IpOnlyAuthenticationMethod,
    CredentialsAndIpAuthenticationMethod,
)

client = create_client()
suffix = uuid.uuid4().hex[:8]

# List voice out trunks
trunks = client.voice_out_trunks().list().data
print(f"Found {len(trunks)} voice out trunks")
for t in trunks[:5]:
    print(f"  {t.name} ({t.status})")
    print(f"    ID: {t.id}")
    auth = t.authentication_method
    print(f"    Auth type: {auth.type if auth else None}")
    if isinstance(auth, CredentialsAndIpAuthenticationMethod):
        print(f"    Username: {auth.username}")
    elif isinstance(auth, IpOnlyAuthenticationMethod):
        print(f"    Allowed SIP IPs: {auth.allowed_sip_ips}")
    print(f"    External Reference ID: {t.external_reference_id}")
    print(f"    Emergency Enable All: {t.emergency_enable_all}")
    print(f"    RTP Timeout: {t.rtp_timeout}")
    print(f"    Codecs: {enum_value_list(t.codecs)}")
    print(f"    ICE: {enum_value(t.ice_mode)}, RTCP mux: {enum_value(t.rtcp_mux_mode)},"
          f" RTCP feedback: {enum_value(t.rtcp_feedback_mode)}")
    print()

# Create a voice out trunk with credentials_and_ip authentication
# Note: ip_only authentication can only be configured by DIDWW staff.
print("=== Creating Voice Out Trunk (credentials_and_ip) ===")
trunk = VoiceOutTrunk()
trunk.name = f"My Outbound Trunk {suffix}"
trunk.authentication_method = CredentialsAndIpAuthenticationMethod(
    allowed_sip_ips=["203.0.113.0/24"],
    tech_prefix="",
)
trunk.default_dst_action = DefaultDstAction.ALLOW_ALL
trunk.on_cli_mismatch_action = OnCliMismatchAction.REJECT_CALL
trunk.external_reference_id = f"python-example-{suffix}"
trunk.rtp_timeout = 60
# Codec names in priority order, the first is the highest; left out, the server picks them
trunk.codecs = [VoiceOutCodec.OPUS, VoiceOutCodec.PCMA, VoiceOutCodec.TELEPHONE_EVENT]
trunk.ice_mode = IceMode.INITIATE
created = client.voice_out_trunks().create(trunk).data
print(f"Created voice out trunk: {created.id}")
print(f"  Name: {created.name}")
auth = created.authentication_method
print(f"  Auth type: {auth.type if auth else None}")
if isinstance(auth, CredentialsAndIpAuthenticationMethod):
    print(f"  Username: {auth.username}")
print(f"  Status: {created.status}")
print(f"  External Reference: {created.external_reference_id}")
print(f"  Codecs: {enum_value_list(created.codecs)}, ICE: {enum_value(created.ice_mode)}")

# Update - change name and tech_prefix
print("\n=== Updating Voice Out Trunk ===")
update = VoiceOutTrunk.build(created.id)
update.name = f"Updated Outbound Trunk {suffix}"
update.authentication_method = CredentialsAndIpAuthenticationMethod(
    allowed_sip_ips=["203.0.113.0/24"],
    tech_prefix="9",
)
updated = client.voice_out_trunks().update(update).data
print(f"Updated name: {updated.name}")
auth = updated.authentication_method
print(f"  New auth type: {auth.type if auth else None}")
if isinstance(auth, CredentialsAndIpAuthenticationMethod):
    print(f"  Username: {auth.username}")

# Delete
print("\n=== Deleting Voice Out Trunk ===")
client.voice_out_trunks().delete(created.id)
print("Deleted voice out trunk")
