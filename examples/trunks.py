"""
Voice IN trunks: lists trunks with their trunk group, finds one, then creates
a SIP trunk and a PSTN trunk, updates both and deletes both, also when a step
fails.

Usage: DIDWW_API_KEY=xxx python examples/trunks.py
"""
import uuid
from contextlib import ExitStack

from client_factory import create_client
from didww.enums import (
    CliFormat,
    Codec,
    IceMode,
    Pop,
    ReroutingDisconnectCode,
    TransportProtocol,
    enum_value,
    enum_value_list,
)
from didww.query_params import QueryParams
from didww.resources.configuration.pstn import PstnConfiguration
from didww.resources.configuration.sip import SipConfiguration
from didww.resources.voice_in_trunk import VoiceInTrunk

client = create_client()
suffix = uuid.uuid4().hex[:8]


def print_configuration(config):
    if isinstance(config, SipConfiguration):
        # Codec names in priority order, the first is the highest
        print(f"  Codecs: {enum_value_list(config.codecs)}")
        print(f"  ICE: {enum_value(config.ice_mode)}, RTCP mux: {enum_value(config.rtcp_mux_mode)},"
              f" RTCP feedback: {enum_value(config.rtcp_feedback_mode)}")
    elif isinstance(config, PstnConfiguration):
        print(f"  DST: {config.dst}")


def delete_trunk(trunk_id):
    client.voice_in_trunks().delete(trunk_id)
    print(f"Deleted trunk {trunk_id}")


# --- List trunks with their trunk group ---
print("=== Existing Trunks ===")
params = QueryParams().include("voice_in_trunk_group").page(number=1, size=10)
trunks = client.voice_in_trunks().list(params).data
print(f"Found {len(trunks)} trunks")
for trunk in trunks:
    config = trunk.configuration
    print(f"{trunk.name} [{config._type if config else 'unknown'}]")
    print(f"  ID: {trunk.id}")
    print(f"  Priority: {trunk.priority}, weight: {trunk.weight}")
    print(f"  CLI format: {enum_value(trunk.cli_format)}, ringing timeout: {trunk.ringing_timeout}")
    # pop is an attribute (a Pop value); None lets DIDWW choose
    print(f"  POP: {enum_value(trunk.pop) or 'chosen by DIDWW'}")
    group = trunk.voice_in_trunk_group
    print(f"  Trunk group: {group.name if group else 'none'}")
    print_configuration(config)

# --- Find one trunk by ID ---
if trunks:
    print("\n=== Trunk Details ===")
    found = client.voice_in_trunks().find(trunks[0].id).data
    print(f"Trunk: {found.name} ({found.id})")
    print(f"  Description: {found.description}")
    print(f"  Created at: {found.created_at}")

# The ExitStack deletes every trunk created in it, also when a step or another deletion fails
with ExitStack() as cleanup:
    # --- Create a SIP trunk ---
    print("\n=== Creating SIP Trunk ===")
    sip = SipConfiguration()
    sip.username = "username"
    sip.host = "203.0.113.110"
    sip.port = 5060
    sip.codecs = [Codec.PCMU, Codec.PCMA, Codec.TELEPHONE_EVENT]  # priority order, the first is the highest
    sip.ice_mode = IceMode.ACCEPT
    sip.transport_protocol_id = TransportProtocol.UDP
    sip.rerouting_disconnect_code_ids = [
        ReroutingDisconnectCode.SIP_480_TEMPORARILY_UNAVAILABLE,
        ReroutingDisconnectCode.SIP_503_SERVICE_UNAVAILABLE,
    ]

    trunk = VoiceInTrunk()
    trunk.name = f"My SIP Trunk {suffix}"
    trunk.priority = 1
    trunk.weight = 100
    trunk.cli_format = CliFormat.E164
    trunk.ringing_timeout = 30
    trunk.capacity_limit = 10
    trunk.pop = Pop.FRA  # optional; leave it unset to let DIDWW choose
    trunk.configuration = sip

    sip_trunk = client.voice_in_trunks().create(trunk).data
    cleanup.callback(delete_trunk, sip_trunk.id)
    print(f"Created SIP trunk: {sip_trunk.id}")
    print(f"  Name: {sip_trunk.name}")
    print(f"  POP: {enum_value(sip_trunk.pop)}")
    print(f"  Ringing timeout: {sip_trunk.ringing_timeout}")
    print_configuration(sip_trunk.configuration)

    # --- Create a PSTN trunk ---
    print("\n=== Creating PSTN Trunk ===")
    pstn = PstnConfiguration()
    pstn.dst = "12125551234"

    trunk = VoiceInTrunk()
    trunk.name = f"My PSTN Trunk {suffix}"
    trunk.ringing_timeout = 30
    trunk.configuration = pstn

    pstn_trunk = client.voice_in_trunks().create(trunk).data
    cleanup.callback(delete_trunk, pstn_trunk.id)
    print(f"Created PSTN trunk: {pstn_trunk.id}")
    print(f"  Name: {pstn_trunk.name}")
    print_configuration(pstn_trunk.configuration)

    # --- Update the SIP trunk: only the fields set here are sent ---
    print("\n=== Updating SIP Trunk ===")
    new_codecs = SipConfiguration()
    new_codecs.codecs = [Codec.G729, Codec.PCMA]
    update = VoiceInTrunk.build(sip_trunk.id)
    update.description = "Updated description"
    update.ringing_timeout = 25
    update.configuration = new_codecs
    updated = client.voice_in_trunks().update(update).data
    print(f"Description: {updated.description}")
    print(f"  Ringing timeout: {updated.ringing_timeout}")
    print_configuration(updated.configuration)

    # --- Update the PSTN trunk ---
    print("\n=== Updating PSTN Trunk ===")
    new_dst = PstnConfiguration()
    new_dst.dst = "12125554321"
    update = VoiceInTrunk.build(pstn_trunk.id)
    update.name = f"My PSTN Trunk {suffix} (updated)"
    update.configuration = new_dst
    updated = client.voice_in_trunks().update(update).data
    print(f"Name: {updated.name}")
    print_configuration(updated.configuration)

    print("\n=== Deleting Trunks ===")
