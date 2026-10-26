"""HTTP header values of the prices services: IMF-fixdate and Content-Disposition."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Optional
from urllib.parse import unquote_to_bytes

_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_IMF_FIXDATE = re.compile(
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([0-9]{2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r" ([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) GMT"
)
_PARAM = re.compile(r';[ \t]*([^\s=;]+)[ \t]*=[ \t]*("(?:[^"\\]|\\.)*"?|[^;]*)')
_EXTENDED = re.compile(r"([A-Za-z0-9!#$%&+^_`{}~-]+)'[^']*'([\x21-\x7e]*)")
_CHARSETS = {"utf-8": "utf-8", "iso-8859-1": "latin-1"}


def check_aware(value, name="if_modified_since"):
    """Raises unless ``value`` is None or a timezone-aware ``datetime``."""
    if value is None:
        return
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime or None")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        value.astimezone(timezone.utc)
    except OverflowError:
        raise ValueError(f"{name} is out of range") from None


def format_http_date(value: datetime) -> str:
    """``value`` as an IMF-fixdate in GMT, in whole seconds."""
    return format_datetime(value.astimezone(timezone.utc).replace(microsecond=0), usegmt=True)


def parse_http_date(value: Optional[str]) -> Optional[datetime]:
    """An IMF-fixdate as an aware UTC ``datetime``; None for anything else, a wrong weekday included."""
    if not value:
        return None
    m = _IMF_FIXDATE.fullmatch(value.strip(" \t"))
    if m is None:
        return None
    try:
        parsed = datetime(int(m[4]), _MONTHS.index(m[3]) + 1, int(m[2]),
                          int(m[5]), int(m[6]), int(m[7]), tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed if _DAYS[parsed.weekday()] == m[1] else None


def content_disposition_filename(value: Optional[str]) -> Optional[str]:
    """The file name of a Content-Disposition: ``filename*`` (UTF-8 or ISO-8859-1) when valid, else ``filename``."""
    if not value:
        return None
    plain = extended = None
    for m in _PARAM.finditer(value):
        name = m[1].lower()
        raw = m[2].strip(" \t")
        if raw.startswith('"'):
            raw = re.sub(r"\\(.)", r"\1", raw[1:-1] if len(raw) > 1 and raw.endswith('"') else raw[1:])
        if name == "filename" and plain is None:
            plain = raw
        elif name == "filename*" and extended is None:
            extended = _decode_extended(raw)
    name = extended if extended is not None else plain
    return name or None


def _decode_extended(value):
    m = _EXTENDED.fullmatch(value)
    if m is None:
        return None
    charset = _CHARSETS.get(m[1].lower())
    if charset is None:
        return None
    encoded = m[2]
    if re.search(r"%(?![0-9A-Fa-f]{2})", encoded):
        return None
    try:
        return unquote_to_bytes(encoded).decode(charset)
    except UnicodeDecodeError:
        return None
