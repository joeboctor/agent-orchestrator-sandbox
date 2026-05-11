"""Simple arithmetic helpers: add, sub, mul, div, and is_palindrome."""


def add(a: int | float, b: int | float) -> int | float:
    """Return the sum of a and b."""
    return a + b


def sub(a: int | float, b: int | float) -> int | float:
    """Return the difference a - b."""
    return a - b


def mul(a: int | float, b: int | float) -> int | float:
    """Return the product of a and b."""
    return a * b


def div(a: int | float, b: int | float) -> float:
    """Return the quotient a / b; raises ZeroDivisionError if b == 0."""
    if b == 0:
        raise ZeroDivisionError("division by zero: 'b' must be non-zero")
    return a / b


def is_palindrome(s: str) -> bool:
    """Return True if s is a palindrome (case-insensitive, alphanumerics only)."""
    normalized = [ch for ch in s.lower() if ch.isalnum()]
    return normalized == normalized[::-1]
