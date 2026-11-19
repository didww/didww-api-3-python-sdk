"""JSON for the SDK: exact numbers in both directions, independent of simplejson."""

import json
import math
from decimal import Context, Decimal, DecimalException, InvalidOperation, localcontext
from enum import Enum

# Numbers are parsed under this context, so a caller's context that does not
# trap InvalidOperation cannot turn an out-of-range number into NaN.
_PARSE_CONTEXT = Context(traps=[InvalidOperation])


def _reject_constant(name):
    raise ValueError(f"{name} is not valid JSON")


def loads(data):
    """Parses a JSON document; fractional numbers become ``decimal.Decimal``.

    Any invalid document, a number out of the ``Decimal`` range included, raises ``ValueError``.
    """
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8")
    try:
        with localcontext(_PARSE_CONTEXT):
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
    scalar = _encode_scalar(obj)
    if scalar is not None:
        out.append(scalar)
    elif isinstance(obj, dict):
        _encode_object(obj, out)
    elif isinstance(obj, (list, tuple)):
        _encode_array(obj, out)
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _encode_scalar(obj):
    """The JSON text of a scalar, or None when ``obj`` is not one."""
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return json.dumps(str(obj))
    if isinstance(obj, int):
        return int.__repr__(obj)
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Out of range float values are not JSON compliant")
        return float.__repr__(obj)
    if isinstance(obj, Decimal):
        if not obj.is_finite():
            raise ValueError("Non-finite Decimal values are not JSON compliant")
        return str(obj)
    return None


def _encode_object(obj, out):
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


def _encode_array(obj, out):
    out.append("[")
    for i, value in enumerate(obj):
        if i:
            out.append(",")
        _encode(value, out)
    out.append("]")
