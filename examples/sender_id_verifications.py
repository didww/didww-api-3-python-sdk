"""
Sender ID Verifications: lists verifications with their SMS trunks, renames an
active one and restores its original name, also when a step fails.

A verification is created and reviewed outside the API; only its name and its
SMS trunk can be changed, and a closed one cannot be changed at all. Only
http_out, smpp_esme and smpp_smsc trunks are accepted as its SMS trunk.

Usage: DIDWW_API_KEY=xxx python examples/sender_id_verifications.py
"""
from client_factory import create_client
from didww.enums import SenderIdVerificationStatus, enum_value
from didww.query_params import QueryParams
from didww.resources.sender_id_verification import SenderIdVerification

client = create_client()


def print_verification(v):
    routed_through = v.sms_trunk.name if v.sms_trunk else "no SMS trunk"
    sender_ids = ", ".join(v.sender_ids or [])
    print(f"{v.reference} {v.name} ({enum_value(v.sender_type)}, {enum_value(v.status)}):"
          f" {sender_ids} via {routed_through}")
    if v.is_changes_required:
        reasons = "; ".join(v.reject_reasons or [])
        print(f"  changes required: {reasons} {v.reject_comment or ''}")
    # Prices are decimal strings; the renew date is "YYYY-MM-DD", None once closed
    print(f"  setup price: {v.meta.get('setup_price')}, monthly price: {v.meta.get('monthly_price')},"
          f" renews: {v.renew_date}")


print("=== Sender ID Verifications ===")
verifications = client.sender_id_verifications().list(QueryParams().include("sms_trunk")).data
for v in verifications:
    print_verification(v)

verification = next((v for v in verifications if v.is_active), None)
if verification is None:
    raise SystemExit("No active Sender ID verification")

original_name = verification.name

print(f"\n=== Renaming {verification.reference} ===")
try:
    rename = SenderIdVerification.build(verification.id)
    rename.name = f"{original_name} (renamed)"
    print(f"Name: {client.sender_id_verifications().update(rename).data.name}")
finally:
    restore = SenderIdVerification.build(verification.id)
    restore.name = original_name
    client.sender_id_verifications().update(restore)
    print(f"Name restored: {original_name}")

# Routing through an SMS trunk that sends messages works the same way; None
# unassigns the trunk, which stops outbound messages until one is assigned again:
#
#   route = SenderIdVerification.build(verification.id)
#   route.sms_trunk = SmsTrunk.build(sending_trunk_id)
#   client.sender_id_verifications().update(route)

print("\nActive verifications by SMS trunk:")
if verification.sms_trunk:
    params = (QueryParams()
              .filter("status", SenderIdVerificationStatus.ACTIVE.value)
              .filter("sms_trunk.id", verification.sms_trunk.id))
    for v in client.sender_id_verifications().list(params).data:
        print(f"  {v.reference} {v.name} via {verification.sms_trunk.name}")
else:
    print(f"  {verification.reference} has no SMS trunk")
