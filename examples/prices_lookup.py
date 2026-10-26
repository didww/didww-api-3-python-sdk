"""
Prices lookup: looks up Voice IN, Voice OUT, SMS OUT and SMS IN prices for one number.

Prices are served by separate hosts (api-vin, api-vout and api-sms); the SDK
obtains a token for each of them on first use. A read-scoped client
(scope=Scope.READ) is enough for prices. The account needs a price plan of the
service, otherwise the call fails with a DidwwPricesError of kind
PRICE_PLAN_NOT_ASSIGNED. Money is a decimal.Decimal in USD.

Usage: DIDWW_API_KEY=xxx python examples/prices_lookup.py [number]
"""
import sys

from client_factory import create_client
from didww.configuration import Scope
from didww.enums import enum_value
from didww.exceptions import DidwwPricesError, PricesErrorKind
from didww.prices import SmsInPrice, SmsOutPrice, VoiceInPrice, VoiceOutPrice

client = create_client(scope=Scope.READ)
number = sys.argv[1] if len(sys.argv) > 1 else "18005550123"


def describe(p):
    if isinstance(p, VoiceInPrice):
        return (f"{p.country} {p.destination} {p.source_type} from {p.src_country_name}:"
                f" rate {p.rate}, connection fee {p.connection_fee},"
                f" intervals {p.initial_interval}/{p.next_interval}, reject calls {p.reject_calls}")
    if isinstance(p, VoiceOutPrice):
        return (f"{enum_value(p.category)} {p.country} {p.network} {p.prefix}:"
                f" rate {p.rate}, connection fee {p.connection_fee},"
                f" increments {p.initial_increment}/{p.recurring_increment},"
                f" next rate {p.next_rate} from {p.effective_at}")
    if isinstance(p, SmsOutPrice):
        return (f"{p.country} {p.mcc_name} {p.mnc_name} (MCC {p.mcc}, MNC {p.mnc})"
                f" {p.source_prefix} -> {p.destination_prefix}: price {p.price}, reject SMS {p.reject_sms}")
    if isinstance(p, SmsInPrice):
        return f"{p.country} {p.source_prefix} -> {p.destination_prefix}: price {p.price}"
    return repr(p)


def show(title, prices, filters):
    print(f"\n=== {title} ===")
    try:
        result = prices.lookup(filters)
    except DidwwPricesError as e:
        if e.kind not in (PricesErrorKind.PRICE_PLAN_NOT_ASSIGNED, PricesErrorKind.PRICE_NOT_FOUND):
            raise
        print(f"  {e.kind.value}: {e}")
        return
    print(f"{result.total_records} matching price(s)")
    for row in result:
        print(f"  {describe(row)}")


show("Voice IN", client.voice_in_prices(), {"number": number})
show("Voice IN, calls from the US", client.voice_in_prices(), {"number": number, "src_country_iso": "US"})
show("Voice OUT", client.voice_out_prices(), {"number": number})
show("SMS OUT A2P", client.sms_out_a2p_prices(), {"dst_number": number})
show("SMS OUT P2P, whole country", client.sms_out_p2p_prices(), {"dst_country_iso": "US"})
show("SMS OUT OTP", client.sms_out_otp_prices(), {"dst_number": number, "dst_country_iso": "US"})
show("SMS IN", client.sms_in_prices(), {"dst_number": number})

# Filters are checked before any request is sent: Voice OUT takes number only.
try:
    client.voice_out_prices().lookup({"number": number, "src_country_iso": "US"})
except ValueError as e:
    print(f"\nRejected locally: {e}")
