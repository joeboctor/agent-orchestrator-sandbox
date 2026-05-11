"""Simple arithmetic helpers: add, sub, mul, div."""


def add(a, b):
    """Return the sum of a and b."""
    return a + b


def sub(a, b):
    """Return the difference a - b."""
    return a - b


def mul(a, b):
    """Return the product of a and b."""
    return a * b


def div(a, b):
    """Return the quotient a / b; raises ZeroDivisionError if b == 0."""
    if b == 0:
        raise ZeroDivisionError("division by zero: 'b' must be non-zero")
    return a / b
