"""
Voice In Trunks: list trunks and display their configurations.
Usage: DIDWW_API_KEY=xxx python examples/voice_in_trunks.py
"""
from client_factory import create_client
from didww.enums import enum_value, enum_value_list
from didww.query_params import QueryParams
from didww.resources.configuration.sip import SipConfiguration

client = create_client()

# List voice in trunks with included relationships
print("=== Existing Trunks ===")
params = QueryParams().include("voice_in_trunk_group")
trunks = client.voice_in_trunks().list(params).data

print(f"Found {len(trunks)} trunks")
for trunk in trunks[:10]:
    config_type = trunk.configuration._type if trunk.configuration else "unknown"
    print(f"{trunk.name} [{config_type}]")
    print(f"  ID: {trunk.id}")
    print(f"  Priority: {trunk.priority}")
    print(f"  Weight: {trunk.weight}")
    print(f"  CLI Format: {enum_value(trunk.cli_format)}")
    print(f"  Ringing Timeout: {trunk.ringing_timeout}")
    # pop is an attribute (a Pop value); None lets DIDWW choose
    print(f"  POP: {enum_value(trunk.pop) or 'chosen by DIDWW'}")
    if isinstance(trunk.configuration, SipConfiguration):
        sip = trunk.configuration
        # Codec names in priority order, the first is the highest
        print(f"  Codecs: {enum_value_list(sip.codecs)}")
        print(f"  ICE: {enum_value(sip.ice_mode)}, RTCP mux: {enum_value(sip.rtcp_mux_mode)},"
              f" RTCP feedback: {enum_value(sip.rtcp_feedback_mode)}")
    print()

# Find a specific trunk by ID
if trunks:
    print("\n=== Specific Trunk Details ===")
    specific = client.voice_in_trunks().find(trunks[0].id).data
    print(f"Trunk: {specific.name}")
    print(f"  ID: {specific.id}")
    print(f"  Description: {specific.description}")
    print(f"  Created at: {specific.created_at}")
