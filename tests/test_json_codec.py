import decimal
import json
from decimal import Decimal

import pytest

from didww import _json
from didww.enums import CallbackMethod


class TestLoads:
    def test_fractions_become_exact_decimals(self):
        doc = _json.loads(b'{"rate": 0.0045, "fee": 1.10, "big": 1e400}')
        assert doc["rate"] == Decimal("0.0045")
        assert str(doc["fee"]) == "1.10"
        assert isinstance(doc["big"], Decimal)

    def test_integers_stay_int(self):
        doc = _json.loads('{"n": 12345678901234567890}')
        assert doc["n"] == 12345678901234567890
        assert isinstance(doc["n"], int)

    @pytest.mark.parametrize("text", ["NaN", "Infinity", "-Infinity", '{"x": NaN}'])
    def test_non_finite_constants_rejected(self, text):
        with pytest.raises(ValueError):
            _json.loads(text)

    @pytest.mark.parametrize("text", ["1e99999999999999999999", '{"x": -1.5e-99999999999999999999}'])
    def test_numbers_out_of_decimal_range_raise_value_error(self, text):
        with pytest.raises(ValueError) as exc:
            _json.loads(text)
        assert type(exc.value) is ValueError
        assert "9999" not in str(exc.value)
        assert exc.value.__context__ is None or exc.value.__suppress_context__

    @pytest.mark.parametrize("text", ["1e99999999999999999999", '{"x": -1.5e-99999999999999999999}'])
    def test_numbers_out_of_decimal_range_raise_without_the_invalid_operation_trap(self, text):
        with decimal.localcontext() as ctx:
            ctx.traps[decimal.InvalidOperation] = False
            with pytest.raises(ValueError):
                _json.loads(text)
            assert not ctx.flags[decimal.InvalidOperation]

    def test_invalid_utf8_raises_value_error(self):
        with pytest.raises(ValueError):
            _json.loads(b'{"a": "\xff"}')


class TestDumps:
    def test_decimal_written_exactly(self):
        assert _json.dumps({"price": Decimal("1.10")}) == b'{"price":1.10}'
        assert _json.dumps([Decimal("1E+2"), Decimal("-0"), Decimal("0.000001")]) == b"[1E+2,-0,0.000001]"

    def test_output_is_valid_json(self):
        doc = {"a": [1, 2.5, Decimal("3.333"), None, True, False], "b": {"c": "dé\n\"q\""}}
        assert json.loads(_json.dumps(doc), parse_float=Decimal) == {
            "a": [1, Decimal("2.5"), Decimal("3.333"), None, True, False],
            "b": {"c": "dé\n\"q\""},
        }

    def test_enums_written_as_values(self):
        assert _json.dumps({"m": CallbackMethod.POST}) == b'{"m":"post"}'
        assert _json.dumps({CallbackMethod.GET: 1}) == b'{"get":1}'

    def test_bool_is_not_written_as_int(self):
        assert _json.dumps([True, False, 0, 1]) == b"[true,false,0,1]"

    def test_tuples_and_dict_subclasses(self):
        class Sub(dict):
            pass

        assert _json.dumps(Sub(a=(1, 2))) == b'{"a":[1,2]}'

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), Decimal("NaN"), Decimal("-Infinity")])
    def test_non_finite_numbers_rejected(self, value):
        with pytest.raises(ValueError):
            _json.dumps({"x": value})

    def test_unknown_types_rejected(self):
        with pytest.raises(TypeError):
            _json.dumps({"x": object()})
        with pytest.raises(TypeError):
            _json.dumps({1: "x"})
