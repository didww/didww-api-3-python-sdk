"""Rows of the price lookups and their parsing."""

from __future__ import annotations

import dataclasses
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, Tuple, Union

from didww.enums import to_enum
from didww.exceptions import DidwwClientError


class VoiceOutPriceCategory(str, Enum):
    """The category of a Voice OUT price. An unknown value is read as a plain ``str``."""

    INTERNATIONAL = "International"
    ORIGIN_BASED = "Origin based"
    LOCAL = "Local"


@dataclasses.dataclass(frozen=True)
class VoiceInPrice:
    """A Voice IN price: one answer per source type and destination country."""

    id: str
    destination: Optional[str] = None
    country: Optional[str] = None
    src_country_name: Optional[str] = None
    source_type: Optional[str] = None
    rate: Optional[Decimal] = None
    connection_fee: Optional[Decimal] = None
    initial_interval: Optional[int] = None
    next_interval: Optional[int] = None
    reject_calls: Optional[bool] = None


@dataclasses.dataclass(frozen=True)
class VoiceOutPrice:
    """A Voice OUT price; the ``next_*`` fields and ``effective_at`` describe a scheduled change."""

    id: str
    category: Union[VoiceOutPriceCategory, str, None] = None
    country: Optional[str] = None
    network: Optional[str] = None
    prefix: Optional[str] = None
    rate: Optional[Decimal] = None
    connection_fee: Optional[Decimal] = None
    initial_increment: Optional[int] = None
    recurring_increment: Optional[int] = None
    reject_calls: Optional[bool] = None
    next_rate: Optional[Decimal] = None
    next_connection_fee: Optional[Decimal] = None
    next_initial_increment: Optional[int] = None
    next_recurring_increment: Optional[int] = None
    effective_at: Optional[datetime] = None
    comment: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class SmsOutPrice:
    """An SMS OUT price.

    The ``id`` is derived from the row content and changes with the price, so
    it does not identify a destination over time.
    """

    id: str
    source_prefix: Optional[str] = None
    destination_prefix: Optional[str] = None
    country: Optional[str] = None
    mcc: Optional[int] = None
    mcc_name: Optional[str] = None
    mnc: Optional[int] = None
    mnc_name: Optional[str] = None
    reject_sms: Optional[bool] = None
    price: Optional[Decimal] = None


@dataclasses.dataclass(frozen=True)
class SmsInPrice:
    """An SMS IN price.

    The ``id`` is derived from the row content and changes with the price, so
    it does not identify a destination over time.
    """

    id: str
    source_prefix: Optional[str] = None
    source_number_length_min: Optional[int] = None
    source_number_length_max: Optional[int] = None
    destination_prefix: Optional[str] = None
    destination_number_length_min: Optional[int] = None
    destination_number_length_max: Optional[int] = None
    country: Optional[str] = None
    price: Optional[Decimal] = None


@dataclasses.dataclass(frozen=True)
class PriceLookup:
    """The answer of a price lookup: at least one row, as no match is ``PRICE_NOT_FOUND``.

    It iterates over ``rows``; ``total_records`` is 0 when the answer does not give it.
    """

    rows: Tuple
    total_records: int = 0

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        return self.rows[index]


class _ParseError(Exception):
    pass


_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_DATETIME = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?"
    r"(?:([Zz])|([+-])([0-9]{2}):([0-9]{2}))"
)


def _str(value):
    if not isinstance(value, str):
        raise _ParseError("is not a string")
    return value


def _int(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise _ParseError("is not an integer")
    return value


def _bool(value):
    if not isinstance(value, bool):
        raise _ParseError("is not a boolean")
    return value


def _decimal(value):
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int) and not isinstance(value, bool):
        number = Decimal(value)
    elif isinstance(value, str) and _DECIMAL.fullmatch(value):
        try:
            number = Decimal(value)
        except InvalidOperation:
            raise _ParseError("is not a decimal number") from None
    else:
        raise _ParseError("is not a decimal number")
    if not number.is_finite():
        raise _ParseError("is not a decimal number")
    return number


def _datetime(value):
    m = _DATETIME.fullmatch(_str(value))
    if m is None:
        raise _ParseError("is not an RFC 3339 date-time")
    fraction = (m[7] or "")[:6].ljust(6, "0")
    try:
        if m[8]:
            tz = timezone.utc
        else:
            hours, minutes = int(m[10]), int(m[11])
            if hours > 23 or minutes > 59:
                raise ValueError
            offset = timedelta(hours=hours, minutes=minutes)
            tz = timezone(-offset if m[9] == "-" else offset)
        return datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6]),
                        int(fraction), tzinfo=tz)
    except ValueError:
        raise _ParseError("is not an RFC 3339 date-time") from None


def _category(value):
    return to_enum(VoiceOutPriceCategory, _str(value))


_FIELDS = {
    VoiceInPrice: {
        "destination": _str, "country": _str, "src_country_name": _str, "source_type": _str,
        "rate": _decimal, "connection_fee": _decimal, "initial_interval": _int, "next_interval": _int,
        "reject_calls": _bool,
    },
    VoiceOutPrice: {
        "category": _category, "country": _str, "network": _str, "prefix": _str, "rate": _decimal,
        "connection_fee": _decimal, "initial_increment": _int, "recurring_increment": _int,
        "reject_calls": _bool, "next_rate": _decimal, "next_connection_fee": _decimal,
        "next_initial_increment": _int, "next_recurring_increment": _int, "effective_at": _datetime,
        "comment": _str,
    },
    SmsOutPrice: {
        "source_prefix": _str, "destination_prefix": _str, "country": _str, "mcc": _int,
        "mcc_name": _str, "mnc": _int, "mnc_name": _str, "reject_sms": _bool, "price": _decimal,
    },
    SmsInPrice: {
        "source_prefix": _str, "source_number_length_min": _int, "source_number_length_max": _int,
        "destination_prefix": _str, "destination_number_length_min": _int,
        "destination_number_length_max": _int, "country": _str, "price": _decimal,
    },
}


def _fail(reason):
    return DidwwClientError(f"Failed to parse price lookup: {reason}")


def parse_lookup(document, row_class):
    """Builds a ``PriceLookup`` of ``row_class`` rows from a parsed JSON:API document."""
    if not isinstance(document, dict):
        raise _fail("the answer is not a JSON:API document")
    data = document.get("data")
    if data is None or data == []:
        raise _fail("the answer holds no prices")
    if not isinstance(data, list):
        raise _fail("data is not an array")
    rows = tuple(_row(item, row_class, i) for i, item in enumerate(data))
    return PriceLookup(rows, _total_records(document.get("meta")))


def _row(item, row_class, index):
    if not isinstance(item, dict):
        raise _fail(f"data[{index}] is not a resource object")
    row_id = item.get("id")
    if not isinstance(row_id, str) or not row_id:
        raise _fail(f"data[{index}] has no id")
    attributes = item.get("attributes")
    if attributes is None:
        attributes = {}
    if not isinstance(attributes, dict):
        raise _fail(f"data[{index}].attributes is not an object")
    values = {}
    for name, convert in _FIELDS[row_class].items():
        value = attributes.get(name)
        if value is None:
            continue
        try:
            values[name] = convert(value)
        except _ParseError as e:
            raise _fail(f"data[{index}].attributes.{name} {e}") from None
    return row_class(id=row_id, **values)


def _total_records(meta):
    if meta is None:
        return 0
    if not isinstance(meta, dict):
        raise _fail("meta is not an object")
    total = meta.get("total_records")
    if total is None:
        return 0
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise _fail("meta.total_records is not a non-negative integer")
    return total
