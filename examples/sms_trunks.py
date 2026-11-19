"""
SMS Trunks: lists trunks, creates an HTTP IN trunk, updates its configuration,
regenerates the credentials of an HTTP OUT trunk, and deletes both trunks,
also when a step fails.

Configuration types (didww.resources.sms_trunk_configuration):
  - SmsToEmailConfiguration, HttpInConfiguration: DIDWW delivers inbound
    messages by email or HTTP
  - HttpOutConfiguration, SmppEsmeConfiguration: you connect to DIDWW; DIDWW
    generates the credentials, which are read-only
  - SmppSmscConfiguration: DIDWW binds to your SMSC

The read-only allow_in / allow_out tell which directions a trunk handles.
repr() of a configuration masks its credentials.

Usage: DIDWW_API_KEY=xxx python examples/sms_trunks.py
"""
import uuid

from client_factory import create_client
from didww.enums import SmsBodyType, SmsHttpMethod
from didww.query_params import QueryParams
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import HttpInConfiguration, HttpOutConfiguration
from didww.resources.sms_trunk_regenerate_credential import SmsTrunkRegenerateCredential

client = create_client()
suffix = uuid.uuid4().hex[:8]


def list_trunks():
    print("=== Existing SMS Trunks ===")
    params = QueryParams().include("sms_trunk_group").page(number=1, size=10)
    trunks = client.sms_trunks().list(params).data
    print(f"Found {len(trunks)} SMS trunks")
    for trunk in trunks:
        config = trunk.configuration
        print(f"{trunk.name} [{config.type if config is not None else 'none'}]")
        print(f"  ID: {trunk.id}")
        print(f"  Inbound: {trunk.allow_in}, outbound: {trunk.allow_out}")
        if trunk.sms_trunk_group:
            print(f"  Group: {trunk.sms_trunk_group.name}")
        if trunk.host:
            print(f"  Submit URL: {trunk.host}")


def http_out_round_trip():
    """Creates an HTTP OUT trunk, regenerates its credentials and deletes it.

    The generated credentials of http_out and smpp_esme trunks are rotated
    with an SmsTrunkRegenerateCredential and read back from the trunk.
    """
    print("\n=== Creating HTTP OUT Trunk and Regenerating Its Credentials ===")
    config = HttpOutConfiguration()
    config.callback_url = "https://example.com/sms/status"
    config.allowed_ips = ["203.0.113.10"]

    trunk = SmsTrunk()
    trunk.name = f"Python HTTP OUT {suffix}"
    trunk.configuration = config

    trunk_id = None
    try:
        trunk_id = client.sms_trunks().create(trunk).data.id
        print(f"Created SMS trunk: {trunk_id}")

        regenerate = SmsTrunkRegenerateCredential()
        regenerate.sms_trunk = SmsTrunk.build(trunk_id)
        client.sms_trunk_regenerate_credentials().create(regenerate)

        # The response carries no credentials: read the trunk again.
        reloaded = client.sms_trunks().find(trunk_id).data
        credentials = reloaded.configuration
        if isinstance(credentials, HttpOutConfiguration):
            # Use credentials.auth_name and credentials.auth_password to submit
            # messages to reloaded.host. Never print them; repr() masks them.
            print("Credentials regenerated:")
            print(f"  auth_name: {'present' if credentials.auth_name else 'absent'}")
            print(f"  auth_password: {'present' if credentials.auth_password else 'absent'}")
            print(f"  Submit URL: {reloaded.host}")
    finally:
        if trunk_id is not None:
            client.sms_trunks().delete(trunk_id)
            print("HTTP OUT trunk deleted")


list_trunks()

print("\n=== Creating HTTP IN Trunk ===")
config = HttpInConfiguration()
config.url = "https://example.com/sms"
# POST and PUT need a body type and a body; GET takes neither.
config.http_method = SmsHttpMethod.POST
config.body_type = SmsBodyType.JSON
# Placeholders: {SMS_TEXT}, {SMS_TEXT_BASE64_ENCODED}, {SMS_SRC_ADDR}, {SMS_DST_ADDR}, {SMS_TIME}
config.body = '{"text":"{SMS_TEXT}","from":"{SMS_SRC_ADDR}","to":"{SMS_DST_ADDR}"}'
config.validate_https_certificate = True

trunk = SmsTrunk()
trunk.name = f"Python HTTP IN {suffix}"
trunk.external_reference_id = f"python-sms-{suffix}"
trunk.configuration = config

created_id = None
try:
    created = client.sms_trunks().create(trunk).data
    created_id = created.id
    print(f"Created SMS trunk: {created.id} - {created.name}")
    print(f"  Configuration: {created.configuration!r}")

    # The configuration type cannot change; attributes left out keep their values.
    print("\n=== Updating HTTP IN Trunk ===")
    new_config = HttpInConfiguration()
    new_config.url = "https://example.com/sms-v2"
    update = SmsTrunk.build(created.id)
    update.name = f"Python HTTP IN {suffix} (v2)"
    update.configuration = new_config
    updated = client.sms_trunks().update(update).data
    if isinstance(updated.configuration, HttpInConfiguration):
        print(f"Updated: {updated.name} -> {updated.configuration.url}")

    http_out_round_trip()
finally:
    if created_id is not None:
        print("\n=== Deleting HTTP IN Trunk ===")
        client.sms_trunks().delete(created_id)
        print("SMS trunk deleted")
