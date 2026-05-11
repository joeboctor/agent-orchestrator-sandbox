"""Tests for unit F-001-U-5: type hints + strict mypy config on math_utils.

These tests assert the *intended* behavior of unit F-001-U-5:

* Every public function in ``math_utils`` (``add``, ``sub``, ``mul``, ``div``)
  carries explicit type annotations on both parameters and on its return.
* Parameter annotations accept ``int | float`` (i.e. either ``int`` or
  ``float`` is allowed for ``a`` and ``b``).
* Return annotations are "appropriate": ``int | float`` for the closed
  arithmetic ops, and either ``int | float`` or just ``float`` for ``div``
  (Python's true division always yields ``float``).
* ``pyproject.toml`` contains a ``[tool.mypy]`` section with ``strict = true``.
* Running ``mypy`` against ``math_utils.py`` with the project's config
  succeeds with zero errors (this is what would gate a PR in CI).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import typing
from pathlib import Path

import pytest

# Make sure repo root (where math_utils.py / pyproject.toml live) is importable
# and discoverable for subprocess calls.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import math_utils  # noqa: E402


FUNCS = ("add", "sub", "mul", "div")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _accepts(annotation: object, t: type) -> bool:
    """Does ``annotation`` accept values of type ``t``?

    Handles a bare type (``int``), a ``typing.Union[int, float]``, and
    PEP 604 unions (``int | float``) uniformly.
    """
    if annotation is t:
        return True
    origin = typing.get_origin(annotation)
    # Both ``typing.Union[...]`` and PEP 604 ``X | Y`` expose their members
    # via ``typing.get_args``.
    if origin is typing.Union or origin is type(int | float):  # noqa: E721
        return t in typing.get_args(annotation)
    # Some Python versions expose PEP 604 unions with ``types.UnionType`` as
    # the origin; fall back to checking args directly.
    args = typing.get_args(annotation)
    if args:
        return t in args
    return False


# ---------------------------------------------------------------------------
# Type-hint presence + shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", FUNCS)
def test_function_has_annotations_for_a_b_and_return(name: str) -> None:
    fn = getattr(math_utils, name)
    hints = typing.get_type_hints(fn)
    for key in ("a", "b", "return"):
        assert key in hints, (
            f"math_utils.{name} is missing a type annotation for {key!r}; "
            f"got {hints!r}"
        )


@pytest.mark.parametrize("name", FUNCS)
def test_parameters_accept_int_and_float(name: str) -> None:
    """Parameters ``a`` and ``b`` must accept BOTH ``int`` and ``float``."""
    fn = getattr(math_utils, name)
    hints = typing.get_type_hints(fn)
    for param in ("a", "b"):
        ann = hints[param]
        assert _accepts(ann, int), (
            f"math_utils.{name} parameter {param!r} should accept int; got {ann!r}"
        )
        assert _accepts(ann, float), (
            f"math_utils.{name} parameter {param!r} should accept float; got {ann!r}"
        )


@pytest.mark.parametrize("name", ("add", "sub", "mul"))
def test_return_type_is_int_or_float_for_closed_ops(name: str) -> None:
    """add/sub/mul preserve numeric type: return ``int | float``."""
    fn = getattr(math_utils, name)
    ret = typing.get_type_hints(fn)["return"]
    assert _accepts(ret, int), (
        f"math_utils.{name} return should accept int; got {ret!r}"
    )
    assert _accepts(ret, float), (
        f"math_utils.{name} return should accept float; got {ret!r}"
    )


def test_div_return_type_is_float_compatible() -> None:
    """``div`` must declare a return type that includes ``float``.

    Either ``float`` alone or ``int | float`` is acceptable: Python's true
    division always produces a ``float``, so a narrower ``float`` annotation
    is correct and a wider ``int | float`` is also fine.
    """
    ret = typing.get_type_hints(math_utils.div)["return"]
    assert ret is float or _accepts(ret, float), (
        f"math_utils.div return annotation must include float; got {ret!r}"
    )


# ---------------------------------------------------------------------------
# pyproject.toml [tool.mypy] config
# ---------------------------------------------------------------------------


def _load_pyproject() -> dict:
    try:
        import tomllib  # py311+
    except ModuleNotFoundError:  # pragma: no cover - py310 fallback
        import tomli as tomllib  # type: ignore[no-redef]
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def test_pyproject_has_tool_mypy_section() -> None:
    cfg = _load_pyproject()
    assert "tool" in cfg and "mypy" in cfg["tool"], (
        "pyproject.toml must have a [tool.mypy] section for unit F-001-U-5"
    )


def test_pyproject_mypy_strict_is_true() -> None:
    cfg = _load_pyproject()
    mypy_cfg = cfg.get("tool", {}).get("mypy", {})
    assert mypy_cfg.get("strict") is True, (
        f"[tool.mypy] must set strict = true; got {mypy_cfg!r}"
    )


# ---------------------------------------------------------------------------
# mypy actually passes on math_utils.py (this is what CI is supposed to gate)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    shutil.which("mypy") is None,
    reason="mypy is not installed in this environment",
)
def test_mypy_strict_passes_on_math_utils() -> None:
    """Running mypy with the project's config must report zero errors.

    This mirrors the check the CI job is intended to run: if it fails,
    a PR introducing a type error should be blocked.
    """
    result = subprocess.run(
        ["mypy", "math_utils.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, (
        "mypy reported type errors on math_utils.py "
        f"(returncode={result.returncode}):\n{combined}"
    )
    assert "Success" in combined or "no issues found" in combined, (
        f"Unexpected mypy output:\n{combined}"
    )


@pytest.mark.skipif(
    shutil.which("mypy") is None,
    reason="mypy is not installed in this environment",
)
def test_mypy_explicit_strict_flag_passes_on_math_utils() -> None:
    """Belt-and-braces: even if the config were ignored, --strict must pass."""
    result = subprocess.run(
        ["mypy", "--strict", "math_utils.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, (
        "mypy --strict reported errors on math_utils.py "
        f"(returncode={result.returncode}):\n{combined}"
    )


# ---------------------------------------------------------------------------
# Sanity: type hints didn't break runtime behavior contracted by F-001-U-1
# ---------------------------------------------------------------------------


def test_runtime_behavior_unbroken_after_typing() -> None:
    """Smoke check that the type-hint pass didn't regress any function."""
    assert math_utils.add(2, 3) == 5
    assert math_utils.sub(10, 4) == 6
    assert math_utils.mul(-3, 4) == -12
    assert math_utils.div(10, 2) == 5
    with pytest.raises(ZeroDivisionError):
        math_utils.div(1, 0)
