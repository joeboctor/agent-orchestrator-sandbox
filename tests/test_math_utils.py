"""Unit tests for math_utils.add (F-001-U-1)."""

import os
import sys

import pytest

# Ensure repo root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from math_utils import add  # noqa: E402


class TestAddPositives:
    def test_two_positive_integers(self):
        assert add(2, 3) == 5

    def test_larger_positive_integers(self):
        assert add(100, 250) == 350

    def test_one_and_one(self):
        assert add(1, 1) == 2


class TestAddNegatives:
    def test_two_negative_integers(self):
        assert add(-2, -3) == -5

    def test_negative_and_positive(self):
        assert add(-5, 3) == -2

    def test_positive_and_negative_cancel(self):
        assert add(7, -7) == 0


class TestAddZero:
    def test_zero_plus_zero(self):
        assert add(0, 0) == 0

    def test_zero_plus_positive(self):
        assert add(0, 5) == 5

    def test_positive_plus_zero(self):
        assert add(5, 0) == 5

    def test_zero_plus_negative(self):
        assert add(0, -5) == -5


class TestAddFloats:
    def test_two_floats(self):
        assert add(1.5, 2.5) == pytest.approx(4.0)

    def test_int_plus_float(self):
        assert add(1, 2.5) == pytest.approx(3.5)

    def test_negative_floats(self):
        assert add(-1.5, -2.5) == pytest.approx(-4.0)

    def test_float_precision(self):
        # Classic floating point case — use approx
        assert add(0.1, 0.2) == pytest.approx(0.3)


class TestAddDocstring:
    def test_add_has_docstring(self):
        assert add.__doc__ is not None
        assert add.__doc__.strip() != ""

    def test_add_docstring_is_one_line(self):
        doc = add.__doc__.strip()
        # A "one-line docstring" should not contain newlines after stripping
        assert "\n" not in doc
