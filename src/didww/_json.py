"""JSON for the SDK: exact numbers in both directions, independent of simplejson."""

import json
import math
from decimal import Decimal, DecimalException
from enum import Enum


def _reject_constant(name):
    raise ValueError(f"{name} is not valid JSON")


def loads(data):
    """Parses a JSON document; fractional numbers become ``decimal.Decimal``.

    Any invalid document, a number out of the ``Decimal`` range included, raises ``ValueError``.
    """
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8")
    try:
        return json.loads(data, parse_float=Decimal, parse_constant=_reject_constant)
    except DecimalException:
        raise ValueError("a JSON number is out of range") from None


def dumps(obj):
    """Serializes ``obj`` to compact JSON bytes.

    ``Decimal`` values are written exactly, ``Enum`` members as their value;
    NaN and infinities are rejected.
    """
    parts = []
    _encode(obj, parts)
    return "".join(parts).encode("utf-8")


def _encode(obj, out):
    if isinstance(obj, Enum):
        obj = obj.value
    if obj is None:
        out.append("null")
    elif obj is True:
        out.append("true")
    elif obj is False:
        out.append("false")
    elif isinstance(obj, str):
        out.append(json.dumps(str(obj)))
    elif isinstance(obj, int):
        out.append(int.__repr__(obj))
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Out of range float values are not JSON compliant")
        out.append(float.__repr__(obj))
    elif isinstance(obj, Decimal):
        if not obj.is_finite():
            raise ValueError("Non-finite Decimal values are not JSON compliant")
        out.append(str(obj))
    elif isinstance(obj, dict):
        out.append("{")
        first = True
        for key, value in obj.items():
            if isinstance(key, Enum):
                key = key.value
            if not isinstance(key, str):
                raise TypeError(f"keys must be str, not {type(key).__name__}")
            if not first:
                out.append(",")
            first = False
            out.append(json.dumps(str(key)))
            out.append(":")
            _encode(value, out)
        out.append("}")
    elif isinstance(obj, (list, tuple)):
        out.append("[")
        for i, value in enumerate(obj):
            if i:
                out.append(",")
            _encode(value, out)
        out.append("]")
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
