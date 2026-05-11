"""Property-based tests for math_utils (unit F-001-U-2).

These tests are intentionally separate from the example-based tests in
``test_math_utils.py`` so the original cases remain untouched. They use
Hypothesis to assert algebraic properties of ``add``, ``sub``, ``mul`` and
``div`` over bounded integer and float ranges.
"""
import math
import os
import sys

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

# Make sure repo root (where math_utils.py lives) is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math_utils  # noqa: E402


# ---------------------------------------------------------------------------
# Strategies (bounded ranges keep tests fast and avoid float-overflow noise)
# ---------------------------------------------------------------------------

ints = st.integers(min_value=-10_000, max_value=10_000)
nonzero_ints = ints.filter(lambda x: x != 0)

# Floats: finite, bounded, no NaN/inf so equality reasoning stays meaningful.
floats = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
)
# For non-zero floats we exclude a small neighbourhood of 0 to keep the
# round-trip division test numerically well-behaved.
nonzero_floats = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
).filter(lambda x: abs(x) > 1e-6)


# ---------------------------------------------------------------------------
# Commutativity: add(a, b) == add(b, a); mul(a, b) == mul(b, a)
# ---------------------------------------------------------------------------

@given(a=ints, b=ints)
def test_add_is_commutative_ints(a, b):
    assert math_utils.add(a, b) == math_utils.add(b, a)


@given(a=floats, b=floats)
def test_add_is_commutative_floats(a, b):
    assert math_utils.add(a, b) == math_utils.add(b, a)


@given(a=ints, b=ints)
def test_mul_is_commutative_ints(a, b):
    assert math_utils.mul(a, b) == math_utils.mul(b, a)


@given(a=floats, b=floats)
def test_mul_is_commutative_floats(a, b):
    assert math_utils.mul(a, b) == math_utils.mul(b, a)


# ---------------------------------------------------------------------------
# Identity: add(a, 0) == a; mul(a, 1) == a
# ---------------------------------------------------------------------------

@given(a=ints)
def test_add_identity_zero_ints(a):
    assert math_utils.add(a, 0) == a
    assert math_utils.add(0, a) == a


@given(a=floats)
def test_add_identity_zero_floats(a):
    assert math_utils.add(a, 0) == a
    assert math_utils.add(0, a) == a


@given(a=ints)
def test_mul_identity_one_ints(a):
    assert math_utils.mul(a, 1) == a
    assert math_utils.mul(1, a) == a


@given(a=floats)
def test_mul_identity_one_floats(a):
    assert math_utils.mul(a, 1) == a
    assert math_utils.mul(1, a) == a


# ---------------------------------------------------------------------------
# Additive inverse: sub(add(a, b), b) == a
# ---------------------------------------------------------------------------

@given(a=ints, b=ints)
def test_add_then_sub_is_identity_ints(a, b):
    assert math_utils.sub(math_utils.add(a, b), b) == a


@given(a=floats, b=floats)
def test_add_then_sub_is_identity_floats(a, b):
    # Floating-point addition/subtraction is not exact; use isclose with a
    # relative tolerance scaled to typical operand magnitude.
    result = math_utils.sub(math_utils.add(a, b), b)
    assert math.isclose(result, a, rel_tol=1e-9, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Zero annihilation: mul(a, 0) == 0
# ---------------------------------------------------------------------------

@given(a=ints)
def test_mul_by_zero_is_zero_ints(a):
    assert math_utils.mul(a, 0) == 0
    assert math_utils.mul(0, a) == 0


@given(a=floats)
def test_mul_by_zero_is_zero_floats(a):
    assert math_utils.mul(a, 0) == 0
    assert math_utils.mul(0, a) == 0


# ---------------------------------------------------------------------------
# Round-trip for div: div(mul(a, b), b) == a when b != 0
# ---------------------------------------------------------------------------

@given(a=ints, b=nonzero_ints)
def test_div_round_trip_ints(a, b):
    # mul of ints is exact; div in Python yields a float, so compare via
    # math.isclose to absorb the int->float conversion.
    result = math_utils.div(math_utils.mul(a, b), b)
    assert math.isclose(result, a, rel_tol=1e-9, abs_tol=1e-9)


@given(a=floats, b=nonzero_floats)
def test_div_round_trip_floats(a, b):
    product = math_utils.mul(a, b)
    # Skip cases where the intermediate product is non-finite (extreme inputs
    # near the edges of the bounded range can overflow when multiplied).
    assume(math.isfinite(product))
    result = math_utils.div(product, b)
    assert math.isclose(result, a, rel_tol=1e-9, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# div by zero always raises, regardless of numerator
# ---------------------------------------------------------------------------

@given(a=ints)
def test_div_by_zero_always_raises_ints(a):
    with pytest.raises(ZeroDivisionError):
        math_utils.div(a, 0)


@given(a=floats)
def test_div_by_zero_always_raises_floats(a):
    with pytest.raises(ZeroDivisionError):
        math_utils.div(a, 0)
