"""Tests for math_utils module (unit F-001-U-1)."""
import os
import sys

import pytest

# Make sure repo root (where math_utils.py lives) is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math_utils  # noqa: E402


# ---------------------------------------------------------------------------
# Module-shape / contract tests
# ---------------------------------------------------------------------------

def test_module_exposes_four_functions():
    for name in ("add", "sub", "mul", "div"):
        assert hasattr(math_utils, name), f"math_utils missing function {name!r}"
        assert callable(getattr(math_utils, name)), f"math_utils.{name} is not callable"


@pytest.mark.parametrize("name", ["add", "sub", "mul", "div"])
def test_each_function_has_a_docstring(name):
    fn = getattr(math_utils, name)
    assert fn.__doc__ is not None and fn.__doc__.strip() != "", (
        f"math_utils.{name} is missing a docstring"
    )
    # Docstring should be a single line per the spec.
    first = fn.__doc__.strip()
    assert "\n" not in first, f"math_utils.{name} docstring should be one line"


# ---------------------------------------------------------------------------
# add(a, b)
# ---------------------------------------------------------------------------

def test_add_positives():
    assert math_utils.add(2, 3) == 5


def test_add_negatives():
    assert math_utils.add(-4, -6) == -10


def test_add_with_zero():
    assert math_utils.add(0, 0) == 0
    assert math_utils.add(7, 0) == 7
    assert math_utils.add(0, -3) == -3


def test_add_mixed_sign():
    assert math_utils.add(-5, 9) == 4


def test_add_floats():
    assert math_utils.add(1.5, 2.25) == pytest.approx(3.75)


# ---------------------------------------------------------------------------
# sub(a, b)
# ---------------------------------------------------------------------------

def test_sub_positives():
    assert math_utils.sub(10, 4) == 6


def test_sub_negatives():
    assert math_utils.sub(-5, -3) == -2


def test_sub_with_zero():
    assert math_utils.sub(0, 0) == 0
    assert math_utils.sub(5, 0) == 5
    assert math_utils.sub(0, 5) == -5


def test_sub_yields_negative():
    assert math_utils.sub(3, 10) == -7


# ---------------------------------------------------------------------------
# mul(a, b)
# ---------------------------------------------------------------------------

def test_mul_positives():
    assert math_utils.mul(3, 4) == 12


def test_mul_negatives():
    assert math_utils.mul(-2, -5) == 10


def test_mul_mixed_sign():
    assert math_utils.mul(-3, 4) == -12


def test_mul_with_zero():
    assert math_utils.mul(0, 0) == 0
    assert math_utils.mul(7, 0) == 0
    assert math_utils.mul(0, -9) == 0


# ---------------------------------------------------------------------------
# div(a, b)
# ---------------------------------------------------------------------------

def test_div_positives():
    assert math_utils.div(10, 2) == 5


def test_div_negatives():
    assert math_utils.div(-9, -3) == 3


def test_div_mixed_sign():
    assert math_utils.div(-8, 2) == -4


def test_div_numerator_zero_is_allowed():
    # Only b == 0 should raise; a == 0 is a normal division.
    assert math_utils.div(0, 5) == 0


def test_div_by_zero_raises_zero_division_error():
    with pytest.raises(ZeroDivisionError):
        math_utils.div(1, 0)


def test_div_by_zero_message_is_clear():
    """The error message should clearly indicate division by zero."""
    with pytest.raises(ZeroDivisionError) as excinfo:
        math_utils.div(42, 0)
    msg = str(excinfo.value)
    assert msg.strip() != "", "ZeroDivisionError must carry a non-empty message"
    # 'zero' should appear in some form to make it clear.
    assert "zero" in msg.lower(), (
        f"ZeroDivisionError message should mention 'zero'; got: {msg!r}"
    )


def test_div_by_zero_with_zero_numerator_still_raises():
    # 0 / 0 should also raise ZeroDivisionError per the spec ("b == 0").
    with pytest.raises(ZeroDivisionError):
        math_utils.div(0, 0)


# ---------------------------------------------------------------------------
# factorial(n)
# ---------------------------------------------------------------------------

def test_factorial_zero():
    # 0! is defined as 1.
    assert math_utils.factorial(0) == 1


def test_factorial_one():
    # 1! == 1 (the spec says "n for n=1", which for n=1 is also 1).
    assert math_utils.factorial(1) == 1


def test_factorial_five():
    assert math_utils.factorial(5) == 120


def test_factorial_ten():
    assert math_utils.factorial(10) == 3_628_800


def test_factorial_negative_raises_value_error():
    with pytest.raises(ValueError):
        math_utils.factorial(-3)
