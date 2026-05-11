"""Tests for unit F-001-U-4: Coverage + 100% threshold.

The unit spec requires:

  1. ``pytest-cov`` is in the test dependencies (``requirements-dev.txt``).
  2. ``pyproject.toml`` has ``[tool.pytest.ini_options]`` whose ``addopts``
     enables coverage with ``--cov=math_utils`` and ``--cov-fail-under=100``.
  3. ``pyproject.toml`` has a ``[tool.coverage.*]`` section (run/report).
  4. ``.github/workflows/test.yml`` invokes the coverage-enabled ``pytest``
     so CI fails when coverage drops below 100%.
  5. The 100% gate actually works end-to-end: a project that drops below
     100% coverage must cause ``pytest`` to exit non-zero with a coverage
     failure message.

These tests are pure-static for (1)-(4) and run an isolated subprocess in
``tmp_path`` for (5), so they never touch the real repo's working tree.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover - CI uses Python 3.12
    tomllib = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "test.yml"


# ---------------------------------------------------------------------------
# 1. pytest-cov is listed as a test dep
# ---------------------------------------------------------------------------

def test_requirements_dev_contains_pytest_cov():
    assert REQUIREMENTS_DEV.is_file(), (
        f"requirements-dev.txt must exist at {REQUIREMENTS_DEV}"
    )
    lines = REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines()
    # Accept any pin form: `pytest-cov`, `pytest-cov==X`, `pytest-cov>=X`, etc.
    pat = re.compile(
        r"^\s*pytest-cov(?:\s*[<>=!~].*)?\s*(?:#.*)?$",
        re.IGNORECASE,
    )
    matches = [ln for ln in lines if pat.match(ln)]
    assert matches, (
        "requirements-dev.txt must list pytest-cov so the coverage gate "
        f"can be installed in CI; current contents: {lines!r}"
    )


# ---------------------------------------------------------------------------
# 2 & 3. pyproject.toml wires the coverage gate
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pyproject_data():
    assert PYPROJECT.is_file(), f"pyproject.toml not found at {PYPROJECT}"
    if tomllib is None:
        pytest.skip("tomllib is not available (need Python 3.11+)")
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)


def _addopts_string(pyproject) -> str:
    addopts = (
        pyproject.get("tool", {})
        .get("pytest", {})
        .get("ini_options", {})
        .get("addopts", "")
    )
    if isinstance(addopts, list):
        addopts = " ".join(str(x) for x in addopts)
    return addopts


def test_pyproject_has_pytest_ini_options(pyproject_data):
    tool = pyproject_data.get("tool", {})
    assert "pytest" in tool and "ini_options" in tool.get("pytest", {}), (
        "pyproject.toml must define [tool.pytest.ini_options]"
    )


def test_pytest_addopts_enables_cov_for_math_utils(pyproject_data):
    addopts = _addopts_string(pyproject_data)
    assert addopts.strip(), (
        "[tool.pytest.ini_options].addopts must be configured for the "
        "coverage gate"
    )
    # Specifically `--cov=math_utils` (or `--cov math_utils`).
    assert re.search(r"--cov[\s=]+math_utils\b", addopts), (
        f"addopts must specify `--cov=math_utils`; got: {addopts!r}"
    )


def test_pytest_addopts_enforces_100_percent_threshold(pyproject_data):
    addopts = _addopts_string(pyproject_data)
    m = re.search(r"--cov-fail-under[\s=]+(\d+)", addopts)
    assert m, (
        "addopts must include `--cov-fail-under=100` so the 100% gate is "
        f"applied automatically; got: {addopts!r}"
    )
    threshold = int(m.group(1))
    assert threshold == 100, (
        f"--cov-fail-under must be 100 (per F-001-U-4); got {threshold}"
    )


def test_pyproject_has_tool_coverage_section(pyproject_data):
    coverage_cfg = pyproject_data.get("tool", {}).get("coverage")
    assert coverage_cfg, (
        "pyproject.toml must contain a [tool.coverage.*] section "
        "(e.g. [tool.coverage.run] and/or [tool.coverage.report])"
    )
    assert ("run" in coverage_cfg) or ("report" in coverage_cfg), (
        "pyproject.toml [tool.coverage] must define [tool.coverage.run] "
        "and/or [tool.coverage.report]"
    )


# ---------------------------------------------------------------------------
# 4. CI workflow runs a coverage-enabled pytest
# ---------------------------------------------------------------------------

def test_workflow_runs_coverage_enabled_pytest(pyproject_data):
    """
    The coverage gate is active in CI iff one of:
      (a) The workflow runs ``pytest`` and pyproject.toml's
          ``[tool.pytest.ini_options].addopts`` already supplies
          ``--cov=math_utils --cov-fail-under=100``.
      (b) The workflow passes those flags explicitly on the pytest CLI.
    Either is acceptable; the unit spec says "CI fails when coverage drops
    below 100%".
    """
    assert WORKFLOW.is_file(), f"CI workflow not found at {WORKFLOW}"
    text = WORKFLOW.read_text(encoding="utf-8")

    # Must invoke pytest at all.
    assert re.search(r"(?<!\w)pytest(?:\s|$)", text), (
        "Workflow must invoke `pytest`"
    )

    addopts = _addopts_string(pyproject_data)
    has_addopts_gate = (
        re.search(r"--cov[\s=]+math_utils\b", addopts) is not None
        and re.search(r"--cov-fail-under[\s=]+100\b", addopts) is not None
    )
    has_cli_gate = (
        re.search(r"pytest[^\n]*--cov[\s=]+math_utils\b", text) is not None
        and re.search(r"pytest[^\n]*--cov-fail-under[\s=]+100\b", text) is not None
    )
    assert has_addopts_gate or has_cli_gate, (
        "CI workflow must run a coverage-enabled pytest invocation. Either "
        "configure --cov=math_utils --cov-fail-under=100 via "
        "[tool.pytest.ini_options].addopts in pyproject.toml (so plain "
        "`pytest` enforces the gate), or pass those flags on the workflow's "
        "pytest command line."
    )


def test_workflow_does_not_mask_pytest_failure_in_coverage_step():
    """The pytest step must not swallow non-zero exit codes."""
    text = WORKFLOW.read_text(encoding="utf-8")

    masking_patterns = [
        r"pytest[^\n]*\|\|\s*true\b",
        r"pytest[^\n]*\|\|\s*exit\s+0\b",
        r"pytest[^\n]*;\s*true\b",
        r"pytest[^\n]*;\s*exit\s+0\b",
    ]
    for pat in masking_patterns:
        assert not re.search(pat, text), (
            "pytest invocation appears to mask its exit code with shell "
            "magic; that would prevent the coverage gate from failing CI. "
            f"Offending pattern: {pat!r}"
        )

    # No `continue-on-error: true` near a pytest invocation either.
    step_chunks = re.split(
        r"(?m)^\s*-\s+(?:name|run|uses|id|shell)\s*:", text
    )
    for chunk in step_chunks:
        if "pytest" in chunk and re.search(
            r"(?m)^\s*continue-on-error:\s*true\s*$", chunk
        ):
            pytest.fail(
                "pytest step must not set `continue-on-error: true`; that "
                "would prevent the coverage gate from failing CI."
            )


# ---------------------------------------------------------------------------
# 5. End-to-end: 100% gate actually fires when coverage drops below 100%
# ---------------------------------------------------------------------------

_MINI_MODULE = textwrap.dedent(
    '''\
    """Tiny stand-in for math_utils, used by the F-001-U-4 gate tests."""


    def add(a, b):
        """Return a + b."""
        return a + b


    def div(a, b):
        """Return a / b; raises ZeroDivisionError if b == 0."""
        if b == 0:
            raise ZeroDivisionError("division by zero")
        return a / b
    '''
)

_MINI_PYPROJECT = textwrap.dedent(
    '''\
    [tool.pytest.ini_options]
    addopts = "--cov=math_utils --cov-report=term-missing --cov-fail-under=100"
    testpaths = ["tests"]

    [tool.coverage.run]
    branch = true
    source = ["math_utils"]

    [tool.coverage.report]
    fail_under = 100
    show_missing = true
    '''
)

_MINI_TESTS_FULL = textwrap.dedent(
    '''\
    import os
    import sys

    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )
    import math_utils  # noqa: E402

    import pytest


    def test_add():
        assert math_utils.add(1, 2) == 3


    def test_div_ok():
        assert math_utils.div(6, 2) == 3


    def test_div_zero():
        with pytest.raises(ZeroDivisionError):
            math_utils.div(1, 0)
    '''
)

_MINI_TESTS_PARTIAL = textwrap.dedent(
    '''\
    import os
    import sys

    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )
    import math_utils  # noqa: E402


    def test_add_only():
        # Intentionally does not exercise div() so coverage drops below 100%.
        assert math_utils.add(1, 2) == 3
    '''
)


def _make_mini_project(root: Path, *, cover_all: bool) -> None:
    (root / "math_utils.py").write_text(_MINI_MODULE, encoding="utf-8")
    (root / "pyproject.toml").write_text(_MINI_PYPROJECT, encoding="utf-8")
    tests_dir = root / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    body = _MINI_TESTS_FULL if cover_all else _MINI_TESTS_PARTIAL
    (tests_dir / "test_mini.py").write_text(body, encoding="utf-8")


def _run_pytest_in(cwd: Path) -> subprocess.CompletedProcess:
    # Use the same interpreter so we inherit the installed pytest/pytest-cov.
    # Strip COV_CORE_* / COVERAGE_* env vars from the outer pytest-cov so the
    # nested process owns its own coverage data file.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("COV_CORE", "COVERAGE_"))}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )


def test_coverage_gate_passes_when_fully_covered(tmp_path):
    """Happy path: fully-covered project passes the 100% gate."""
    _make_mini_project(tmp_path, cover_all=True)
    proc = _run_pytest_in(tmp_path)
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        "Expected pytest to succeed on a fully-covered project, but it "
        f"exited {proc.returncode}.\nSTDOUT:\n{proc.stdout}\n"
        f"STDERR:\n{proc.stderr}"
    )
    assert (
        "100%" in combined
        or "Required test coverage of 100% reached" in combined
    ), (
        "Expected coverage output to confirm 100% coverage on a fully "
        f"covered project.\nOutput:\n{combined}"
    )


def test_coverage_gate_fails_when_below_100_percent(tmp_path):
    """Error case: dropping below 100% must fail the gate."""
    _make_mini_project(tmp_path, cover_all=False)
    proc = _run_pytest_in(tmp_path)
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, (
        "Expected pytest to FAIL on an under-covered project because "
        "--cov-fail-under=100 is configured, but it succeeded.\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    lower = combined.lower()
    # pytest-cov emits something like:
    #   FAIL Required test coverage of 100% not reached. Total coverage: X%
    assert "coverage" in lower and "100" in lower, (
        "Expected a coverage-failure message mentioning the 100% threshold.\n"
        f"Output:\n{combined}"
    )



