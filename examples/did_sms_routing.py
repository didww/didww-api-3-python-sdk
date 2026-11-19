"""
DID SMS routing: routes a DID's inbound SMS to an SMS trunk, then to an SMS
trunk group. The two are exclusive: assigning one sends the other as null in
the same PATCH, just like voice_in_trunk and voice_in_trunk_group. At the end
the DID's original SMS routing is restored, also when a step fails.

Usage: DIDWW_API_KEY=xxx python examples/did_sms_routing.py
"""
from client_factory import create_client
from didww.query_params import QueryParams
from didww.resources.did import Did
from didww.resources.sms_trunk import SmsTrunk
from didww.resources.sms_trunk_group import SmsTrunkGroup

client = create_client()

include_params = QueryParams().include("sms_trunk", "sms_trunk_group")


def print_sms_routing(did_id):
    result = client.dids().find(did_id, include_params).data
    print(f"   sms_trunk       = {result.sms_trunk.id if result.sms_trunk else 'null'}")
    print(f"   sms_trunk_group = {result.sms_trunk_group.id if result.sms_trunk_group else 'null'}")


print("=== Finding DID ===")
dids = client.dids().list(QueryParams().include("sms_trunk", "sms_trunk_group").page(number=1, size=1)).data
if not dids:
    raise SystemExit("No DIDs found. Please order a DID first.")
did = dids[0]
print(f"Using DID: {did.number} ({did.id})")

print("\n=== Finding inbound SMS trunk ===")
trunk = next((t for t in client.sms_trunks().list().data if t.allow_in), None)
if trunk is None:
    raise SystemExit("No inbound SMS trunk found. Run examples/sms_trunks.py or create one first.")
print(f"Selected SMS trunk: {trunk.name} ({trunk.id})")

print("\n=== Finding SMS trunk group ===")
groups = client.sms_trunk_groups().list(QueryParams().page(number=1, size=1)).data
group = groups[0] if groups else None
if group is not None:
    print(f"Selected SMS trunk group: {group.name} ({group.id})")
else:
    print("No SMS trunk group found; step 2 is skipped.")

# Remember the current routing to put it back at the end
original_trunk_id = did.sms_trunk.id if did.sms_trunk else None
original_group_id = did.sms_trunk_group.id if did.sms_trunk_group else None
print("\nCurrent SMS routing:")
print_sms_routing(did.id)

did_changed = False
try:
    # 1. Assign the SMS trunk (sends sms_trunk_group as null)
    print("\n=== 1. Assigning SMS trunk to DID ===")
    did_changed = True
    assign_trunk = Did.build(did.id)
    assign_trunk.sms_trunk = SmsTrunk.build(trunk.id)
    client.dids().update(assign_trunk)
    print_sms_routing(did.id)

    print(f"\n=== DIDs routed to {trunk.name} ===")
    for d in client.dids().list(QueryParams().filter("sms_trunk.id", trunk.id)).data:
        print(f"   {d.number}")

    # 2. Assign the SMS trunk group (sends sms_trunk as null)
    if group is not None:
        print("\n=== 2. Assigning SMS trunk group to DID (clears the SMS trunk) ===")
        assign_group = Did.build(did.id)
        assign_group.sms_trunk_group = SmsTrunkGroup.build(group.id)
        client.dids().update(assign_group)
        print_sms_routing(did.id)
finally:
    if did_changed:
        # 3. Restore the original routing. None unassigns only that
        # relationship, so both are set to unroute the DID's inbound SMS.
        print("\n=== 3. Restoring the DID's original SMS routing ===")
        restore = Did.build(did.id)
        if original_trunk_id is not None:
            restore.sms_trunk = SmsTrunk.build(original_trunk_id)
        elif original_group_id is not None:
            restore.sms_trunk_group = SmsTrunkGroup.build(original_group_id)
        else:
            restore.sms_trunk = None
            restore.sms_trunk_group = None
        client.dids().update(restore)
        print_sms_routing(did.id)
