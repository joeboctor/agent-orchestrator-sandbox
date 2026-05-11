"""Independent verification tests for unit F-001-U-2.

These are written by the tester from scratch (NOT the coder) to verify the
intended behavior described in the unit spec:

  - hypothesis is declared as a test dependency
  - tests/test_math_utils_properties.py exists with property-based tests
    asserting:
        * commutativity of add and mul
        * identity   (add(a, 0) == a, mul(a, 1) == a)
        * inverse    (sub(add(a, b), b) == a)
        * zero       (mul(a, 0) == 0)
        * round-trip (div(mul(a, b), b) == a for b != 0)
  - bounded integer/float ranges are used
  - existing example-based tests in tests/test_math_utils.py are untouched

The algebraic properties themselves are also re-verified here with our own,
independently authored Hypothesis strategies. If the coder's properties file
was wrong, these would still catch real implementation bugs.
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

# Make repo root (where math_utils.py lives) importable.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import math_utils  # noqa: E402


# ---------------------------------------------------------------------------
# Spec / file-layout checks
# ---------------------------------------------------------------------------

def test_hypothesis_listed_in_dev_requirements():
    """Unit spec: 'Add hypothesis to test deps.'"""
    req_file = REPO_ROOT / "requirements-dev.txt"
    assert req_file.exists(), "requirements-dev.txt missing at repo root"
    contents = req_file.read_text().lower()
    assert "hypothesis" in contents, (
        f"'hypothesis' must be declared in requirements-dev.txt; got:\n{contents!r}"
    )


def test_properties_test_file_exists_at_expected_path():
    """Unit spec: 'Create tests/test_math_utils_properties.py'."""
    p = REPO_ROOT / "tests" / "test_math_utils_properties.py"
    assert p.exists(), f"Expected property tests file at {p}, but it is missing"
    text = p.read_text()
    # The spec calls these out by name -- the file must reference them at
    # minimum so we can see all categories are addressed.
    for token in ("add", "sub", "mul", "div"):
        assert token in text, f"property tests should reference math_utils.{token}"
    # Must actually be using Hypothesis (the unit is *property*-based testing).
    assert "hypothesis" in text.lower(), (
        "property tests file must import/use the hypothesis library"
    )
    assert "@given" in text, "property tests must use @given decorators"


def test_existing_example_tests_file_untouched_and_present():
    """Unit spec: 'Keep existing example-based tests untouched.'

    We can't easily prove untouched without git, but we can assert the file
    is still present and still defines its core test functions.
    """
    p = REPO_ROOT / "tests" / "test_math_utils.py"
    assert p.exists(), "tests/test_math_utils.py disappeared!"
    text = p.read_text()
    # A few representative test names that must still be there.
    for name in (
        "test_add_positives",
        "test_sub_positives",
        "test_mul_positives",
        "test_div_positives",
        "test_div_by_zero_raises_zero_division_error",
    ):
        assert f"def {name}" in text, (
            f"Example-based test {name!r} appears to have been removed/changed"
        )


# ---------------------------------------------------------------------------
# Independent property re-verification
#
# Use small bounded ranges (per spec: "Use integers/floats with bounded
# ranges") and conservative tolerances so float reasoning stays meaningful.
# ---------------------------------------------------------------------------

# Bounded strategies authored independently of the coder's file.
small_ints = st.integers(min_value=-1000, max_value=1000)
nonzero_small_ints = small_ints.filter(lambda x: x != 0)

bounded_floats = st.floats(
    min_value=-1e4,
    max_value=1e4,
    allow_nan=False,
    allow_infinity=False,
)
nonzero_bounded_floats = bounded_floats.filter(lambda x: abs(x) > 1e-3)


# ---- Commutativity --------------------------------------------------------

@given(a=small_ints, b=small_ints)
def test_property_add_commutative_int(a, b):
    assert math_utils.add(a, b) == math_utils.add(b, a)


@given(a=small_ints, b=small_ints)
def test_property_mul_commutative_int(a, b):
    assert math_utils.mul(a, b) == math_utils.mul(b, a)


@given(a=bounded_floats, b=bounded_floats)
def test_property_add_commutative_float(a, b):
    # Float + is commutative bitwise in IEEE-754 (NaN excluded above).
    assert math_utils.add(a, b) == math_utils.add(b, a)


@given(a=bounded_floats, b=bounded_floats)
def test_property_mul_commutative_float(a, b):
    assert math_utils.mul(a, b) == math_utils.mul(b, a)


# ---- Identity -------------------------------------------------------------

@given(a=small_ints)
def test_property_add_identity_int(a):
    assert math_utils.add(a, 0) == a
    assert math_utils.add(0, a) == a


@given(a=small_ints)
def test_property_mul_identity_int(a):
    assert math_utils.mul(a, 1) == a
    assert math_utils.mul(1, a) == a


@given(a=bounded_floats)
def test_property_add_identity_float(a):
    assert math_utils.add(a, 0) == a
    assert math_utils.add(0, a) == a


@given(a=bounded_floats)
def test_property_mul_identity_float(a):
    assert math_utils.mul(a, 1) == a
    assert math_utils.mul(1, a) == a


# ---- Additive inverse: sub(add(a, b), b) == a ----------------------------

@given(a=small_ints, b=small_ints)
def test_property_add_then_sub_inverse_int(a, b):
    assert math_utils.sub(math_utils.add(a, b), b) == a


@given(a=bounded_floats, b=bounded_floats)
def test_property_add_then_sub_inverse_float(a, b):
    result = math_utils.sub(math_utils.add(a, b), b)
    # FP round-off: allow a tolerance scaled to magnitudes involved.
    assert math.isclose(result, a, rel_tol=1e-9, abs_tol=1e-6)


# ---- Zero annihilation: mul(a, 0) == 0 ------------------------------------

@given(a=small_ints)
def test_property_mul_by_zero_int(a):
    assert math_utils.mul(a, 0) == 0
    assert math_utils.mul(0, a) == 0


@given(a=bounded_floats)
def test_property_mul_by_zero_float(a):
    # For finite a, 0.0 * a == 0.0 (possibly -0.0); both compare == 0.
    assert math_utils.mul(a, 0) == 0
    assert math_utils.mul(0, a) == 0


# ---- Division round-trip: div(mul(a, b), b) == a when b != 0 -------------

@given(a=small_ints, b=nonzero_small_ints)
def test_property_div_round_trip_int(a, b):
    # math_utils.div uses true division (float result), so compare with
    # isclose to absorb int->float coercion.
    result = math_utils.div(math_utils.mul(a, b), b)
    assert math.isclose(result, a, rel_tol=1e-9, abs_tol=1e-9)


@given(a=bounded_floats, b=nonzero_bounded_floats)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_property_div_round_trip_float(a, b):
    product = math_utils.mul(a, b)
    assume(math.isfinite(product))
    result = math_utils.div(product, b)
    # Tolerance scaled to |a| for robustness in the bounded float range.
    assert math.isclose(result, a, rel_tol=1e-9, abs_tol=1e-6)


# ---- Division by zero always raises (error case from feature spec) -------

@given(a=small_ints)
def test_property_div_by_zero_always_raises_int(a):
    with pytest.raises(ZeroDivisionError):
        math_utils.div(a, 0)


@given(a=bounded_floats)
def test_property_div_by_zero_always_raises_float(a):
    with pytest.raises(ZeroDivisionError):
        math_utils.div(a, 0)
