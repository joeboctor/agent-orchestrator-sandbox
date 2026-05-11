"""Simple arithmetic helpers: add, sub, mul, div, factorial."""


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


def factorial(n: int) -> int:
    """Return n! recursively; raises ValueError for negative n."""
    if n < 0:
        raise ValueError("factorial is undefined for negative integers")
    if n == 0:
        return 1
    if n == 1:
        return n
    return n * factorial(n - 1)
