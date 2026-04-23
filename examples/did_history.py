"""
DID History: list DID ownership history (2026-04-16).
Records are retained for the last 90 days only.

Server-side filters supported:
  did_number (eq), action (eq), method (eq),
  created_at_gteq, created_at_lteq

Usage: DIDWW_API_KEY=xxx python examples/did_history.py
"""
from client_factory import create_client
from didww.query_params import QueryParams

client = create_client()

# List most recent DID history events
print("=== Recent DID History ===")
events = client.did_history().list().data
print(f"Found {len(events)} events in the last 90 days")

for event in events[:10]:
    print(f"  {event.created_at}  {event.did_number:16}  {event.action:28}  via {event.method}")

# Filter by a specific DID number
if events:
    number = events[0].did_number
    print(f"\n=== History for DID {number} ===")
    params = QueryParams().filter("did_number", number)
    per_number = client.did_history().list(params).data
    for event in per_number:
        print(f"  {event.created_at}  {event.action}  via {event.method}")
