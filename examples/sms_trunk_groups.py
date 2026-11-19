"""
SMS Trunk Groups: creates two inbound SMS trunks, puts them in a group, lists
groups, and deletes the group, also when a step fails.

A group spreads a DID's inbound messages over its trunks by their priority
(higher first). http_out trunks cannot join a group. Deleting a group also
deletes the trunks in it.

Usage: DIDWW_API_KEY=xxx python examples/sms_trunk_groups.py
"""
import uuid

from client_factory import create_client
from didww.enums import SmsHttpMethod
from didww.query_params import QueryParams
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_configuration import HttpInConfiguration, SmsToEmailConfiguration
from didww.resources.sms_trunk_group import SmsTrunkGroup

client = create_client()
suffix = uuid.uuid4().hex[:8]

trunk_ids = []
group_id = None
try:
    print("=== Creating SMS Trunks ===")
    http = HttpInConfiguration()
    http.url = "https://example.com/sms"
    http.http_method = SmsHttpMethod.GET  # GET takes no body type and no body
    http.query_parameters = {"text": "{SMS_TEXT}", "from": "{SMS_SRC_ADDR}"}

    primary = SmsTrunk()
    primary.name = f"Python primary {suffix}"
    primary.priority = 200
    primary.configuration = http
    primary_id = client.sms_trunks().create(primary).data.id
    trunk_ids.append(primary_id)
    print(f"Created SMS trunk: {primary_id} - {primary.name}")

    email = SmsToEmailConfiguration()
    email.send_to = "sms@example.com"
    email.subject = "Inbound SMS"
    email.message = "You have a new message."

    fallback = SmsTrunk()
    fallback.name = f"Python fallback {suffix}"
    fallback.priority = 100
    fallback.configuration = email
    fallback_id = client.sms_trunks().create(fallback).data.id
    trunk_ids.append(fallback_id)
    print(f"Created SMS trunk: {fallback_id} - {fallback.name}")

    print("\n=== Creating SMS Trunk Group ===")
    group = SmsTrunkGroup()
    group.name = f"Python SMS Group {suffix}"
    group.external_reference_id = f"python-sms-group-{suffix}"
    # The list replaces the group's membership
    group.sms_trunks = [SmsTrunk.build(primary_id), SmsTrunk.build(fallback_id)]
    created = client.sms_trunk_groups().create(group).data
    group_id = created.id
    print(f"Created SMS trunk group: {created.id} - {created.name} ({created.sms_trunks_count} trunks)")

    print("\n=== Existing SMS Trunk Groups ===")
    params = QueryParams().include("sms_trunks").page(number=1, size=5)
    for g in client.sms_trunk_groups().list(params).data:
        names = ", ".join(t.name for t in (g.sms_trunks or []))
        print(f"{g.name} ({g.sms_trunks_count} trunks) {names}")
finally:
    if group_id is not None:
        print("\n=== Deleting SMS Trunk Group (and its trunks) ===")
        client.sms_trunk_groups().delete(group_id)
        print("SMS trunk group deleted")
    else:
        # Without a group the trunks are deleted one by one
        for trunk_id in trunk_ids:
            client.sms_trunks().delete(trunk_id)
            print(f"SMS trunk deleted: {trunk_id}")
