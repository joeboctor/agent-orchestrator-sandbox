"""Tests for math_utils.is_palindrome (unit F-002-U-1).

The unit description requires is_palindrome(s: str) -> bool that:
- normalizes input by lowercasing and keeping only alphanumeric chars,
- then checks whether the normalized string equals its reverse.

These five examples MUST pass:
- 'A man, a plan, a canal: Panama' -> True
- 'race a car'                     -> False
- ''                               -> True
- 'a'                              -> True
- '12321'                          -> True
"""
import os
import sys

import pytest

# Make sure repo root (where math_utils.py lives) is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import math_utils  # noqa: E402


# ---------------------------------------------------------------------------
# Module-shape / contract
# ---------------------------------------------------------------------------

def test_is_palindrome_is_exposed_and_callable():
    assert hasattr(math_utils, "is_palindrome"), "math_utils.is_palindrome missing"
    assert callable(math_utils.is_palindrome)


def test_is_palindrome_has_docstring():
    doc = math_utils.is_palindrome.__doc__
    assert doc is not None and doc.strip() != "", (
        "math_utils.is_palindrome must have a non-empty docstring"
    )


# ---------------------------------------------------------------------------
# The five required examples from the unit description.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "s, expected",
    [
        ("A man, a plan, a canal: Panama", True),
        ("race a car", False),
        ("", True),
        ("a", True),
        ("12321", True),
    ],
)
def test_required_examples(s, expected):
    assert math_utils.is_palindrome(s) is expected, (
        f"is_palindrome({s!r}) expected {expected}, "
        f"got {math_utils.is_palindrome(s)!r}"
    )


# ---------------------------------------------------------------------------
# Return-type contract: must be a real bool, not just truthy.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("s", ["A man, a plan, a canal: Panama", "race a car", "", "a", "12321"])
def test_return_type_is_bool(s):
    result = math_utils.is_palindrome(s)
    assert isinstance(result, bool), (
        f"is_palindrome({s!r}) returned {type(result).__name__}, not bool"
    )


# ---------------------------------------------------------------------------
# Mixed-casing coverage (per FEATURE CONTEXT: "at least one with mixed casing").
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "s",
    [
        "RaceCar",
        "Madam",
        "No 'x' in Nixon",
        "Was it a car or a cat I saw?",
        "AbBa",
    ],
)
def test_mixed_casing_palindromes(s):
    assert math_utils.is_palindrome(s) is True, (
        f"is_palindrome({s!r}) should be True (case-insensitive palindrome)"
    )


def test_mixed_casing_non_palindrome():
    assert math_utils.is_palindrome("Hello, World!") is False


# ---------------------------------------------------------------------------
# Single-character and short inputs (boundary cases).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ch", list("abcXYZ09"))
def test_single_alphanumeric_char_is_palindrome(ch):
    assert math_utils.is_palindrome(ch) is True


def test_two_same_chars_is_palindrome():
    assert math_utils.is_palindrome("aa") is True


def test_two_different_chars_is_not_palindrome():
    assert math_utils.is_palindrome("ab") is False


# ---------------------------------------------------------------------------
# Non-alphanumeric handling.
# ---------------------------------------------------------------------------

def test_only_punctuation_is_palindrome_after_normalization():
    # After stripping non-alphanumerics, the empty string remains, which is
    # a palindrome.
    assert math_utils.is_palindrome(".,!?@#$%") is True


def test_only_whitespace_is_palindrome_after_normalization():
    assert math_utils.is_palindrome("   \t\n  ") is True


def test_punctuation_and_spaces_ignored():
    # 'Able, was I saw eLba' -> 'ablewasisawelba' which is a palindrome.
    assert math_utils.is_palindrome("Able , was I saw eLba") is True


# ---------------------------------------------------------------------------
# Pure-digit and alphanumeric mixes.
# ---------------------------------------------------------------------------

def test_digit_palindrome():
    assert math_utils.is_palindrome("12321") is True


def test_digit_non_palindrome():
    assert math_utils.is_palindrome("12345") is False


def test_alphanumeric_mix_palindrome():
    # 'a1b2b1a' lowercased & kept-as-alphanumeric reverses to itself.
    assert math_utils.is_palindrome("a1b2b1a") is True


def test_alphanumeric_mix_non_palindrome():
    assert math_utils.is_palindrome("a1b2c3") is False
