"""Independent tests for factorial(n) — unit F-001-U-1.

These tests reflect the intended behavior described in the unit spec:

    Implement factorial(n) in math_utils.py:
      - returns 1 for n == 0
      - returns n for n == 1
      - n * factorial(n - 1) for n > 1
      - raises ValueError for negative inputs

Required cases per the spec: 0, 1, 5, 10, and -3 (must raise ValueError).
Additional edge/contract cases are included for robustness.
"""
import math
import os
import sys

import pytest

# Make sure repo root (where math_utils.py lives) is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math_utils  # noqa: E402


# ---------------------------------------------------------------------------
# Module exposes factorial
# ---------------------------------------------------------------------------

def test_factorial_is_exposed_and_callable():
    assert hasattr(math_utils, "factorial"), "math_utils is missing factorial"
    assert callable(math_utils.factorial), "math_utils.factorial is not callable"


# ---------------------------------------------------------------------------
# Required cases from the unit description
# ---------------------------------------------------------------------------

def test_factorial_of_zero_returns_one():
    # 0! is defined as 1 (the empty product).
    assert math_utils.factorial(0) == 1


def test_factorial_of_one_returns_one():
    # Spec: "returns n for n == 1" — for n == 1 that is 1.
    assert math_utils.factorial(1) == 1


def test_factorial_of_five_returns_120():
    # 5! = 5 * 4 * 3 * 2 * 1 = 120
    assert math_utils.factorial(5) == 120


def test_factorial_of_ten_returns_3_628_800():
    # 10! = 3,628,800
    assert math_utils.factorial(10) == 3_628_800


def test_factorial_of_negative_three_raises_value_error():
    with pytest.raises(ValueError):
        math_utils.factorial(-3)


# ---------------------------------------------------------------------------
# Additional spec-derived properties
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n, expected", [
    (2, 2),
    (3, 6),
    (4, 24),
    (6, 720),
    (7, 5040),
])
def test_factorial_known_small_values(n, expected):
    assert math_utils.factorial(n) == expected


@pytest.mark.parametrize("n", [2, 3, 5, 8, 12])
def test_factorial_recursive_relation(n):
    """Spec: for n > 1, factorial(n) == n * factorial(n-1)."""
    assert math_utils.factorial(n) == n * math_utils.factorial(n - 1)


@pytest.mark.parametrize("n", list(range(0, 11)))
def test_factorial_matches_stdlib_math_factorial(n):
    """For non-negative n, results must agree with math.factorial."""
    assert math_utils.factorial(n) == math.factorial(n)


def test_factorial_return_type_is_int():
    # The recursive definition over ints should always yield an int.
    assert isinstance(math_utils.factorial(0), int)
    assert isinstance(math_utils.factorial(1), int)
    assert isinstance(math_utils.factorial(5), int)


@pytest.mark.parametrize("n", [-1, -2, -3, -10, -100])
def test_factorial_any_negative_raises_value_error(n):
    """Spec: ValueError for *any* negative input, not just -3."""
    with pytest.raises(ValueError):
        math_utils.factorial(n)


def test_factorial_negative_does_not_raise_other_error_types():
    """Make sure a negative input raises ValueError specifically (not e.g.
    RecursionError from accidentally recursing on n-1 forever)."""
    # If the guard were missing, recursing on -3 -> -4 -> ... would blow the
    # stack with RecursionError; the spec demands ValueError instead.
    with pytest.raises(ValueError):
        math_utils.factorial(-5)


def test_factorial_does_not_accept_negative_silently():
    """Negative inputs must NOT return a value (e.g. 1) — they must raise."""
    raised = False
    try:
        math_utils.factorial(-1)
    except ValueError:
        raised = True
    assert raised, "factorial(-1) must raise ValueError, not return a value"
