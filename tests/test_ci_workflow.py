"""Tests for the GitHub Actions CI workflow (unit F-001-U-3).

The workflow lives at .github/workflows/test.yml. The spec for this unit
says it must:

  1. Exist as .github/workflows/test.yml.
  2. Run on `push` AND `pull_request` events, both scoped to `main`.
  3. Pin Python to **3.12** (not `3`, not `3.x`, not a range).
  4. Cache pip dependencies.
  5. Install test requirements (i.e. install from requirements-dev.txt /
     the project's test deps).
  6. Run `pytest -q`.
  7. Fail the PR check on any test failure (i.e. the pytest invocation
     must not swallow its non-zero exit code, e.g. via `|| true` or
     `continue-on-error: true`).

These tests parse / scan the YAML and assert each property. They never
modify the workflow file.

We deliberately use stdlib-only parsing (regex + a tiny block-indent
scanner) so that running these tests does not require adding a new test
dependency (e.g. PyYAML) to the project. The intent is that this same
test file will run unchanged inside the new CI workflow.
"""
from __future__ import annotations

import os
import re

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_PATH = os.path.join(REPO_ROOT, ".github", "workflows", "test.yml")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_workflow_text() -> str:
    assert os.path.isfile(WORKFLOW_PATH), (
        f"CI workflow not found at {WORKFLOW_PATH!r}; F-001-U-3 requires "
        f".github/workflows/test.yml"
    )
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _extract_block(text: str, header_re: str) -> str:
    """
    Return the text of the indented block under the line matching
    `header_re` (a regex with a colon-terminated key, possibly at any
    indent). Lines are returned until the next line at the same or
    smaller indent than the header. Blank lines are kept.

    Returns "" if the header is not found.
    """
    lines = text.splitlines()
    pat = re.compile(header_re)
    for i, line in enumerate(lines):
        if pat.match(line):
            header_indent = _indent_of(line)
            block = []
            for j in range(i + 1, len(lines)):
                ln = lines[j]
                if ln.strip() == "":
                    block.append(ln)
                    continue
                if _indent_of(ln) <= header_indent:
                    break
                block.append(ln)
            return "\n".join(block)
    return ""


# ---------------------------------------------------------------------------
# Existence + parseability-ish
# ---------------------------------------------------------------------------

def test_workflow_file_exists():
    assert os.path.isfile(WORKFLOW_PATH), (
        f"Expected CI workflow at {WORKFLOW_PATH}"
    )


def test_workflow_is_non_empty():
    text = _read_workflow_text()
    assert text.strip(), "Workflow file must not be empty"


def test_workflow_has_jobs_section():
    text = _read_workflow_text()
    assert re.search(r"(?m)^jobs:\s*$", text), (
        "Workflow must define a top-level `jobs:` section"
    )
    jobs_block = _extract_block(text, r"^jobs:\s*$")
    # At least one job (a line with two-space indent ending in `:`).
    assert re.search(r"(?m)^  [\w\-]+:\s*$", jobs_block), (
        "Workflow `jobs:` section must contain at least one job"
    )


# ---------------------------------------------------------------------------
# Triggers: push + pull_request, both targeting main
# ---------------------------------------------------------------------------

def _on_block(text: str) -> str:
    # Accept either bare `on:` or quoted `"on":` / `'on':`.
    for header in (r'^on:\s*$', r'^"on":\s*$', r"^'on':\s*$"):
        block = _extract_block(text, header)
        if block:
            return block
    return ""


def test_workflow_has_on_section():
    text = _read_workflow_text()
    block = _on_block(text)
    assert block.strip(), "Workflow must define an `on:` trigger section"


def test_workflow_triggers_on_push_to_main():
    text = _read_workflow_text()
    on_block = _on_block(text)
    assert on_block, "Workflow must define an `on:` section"
    # Find a `push:` sub-key inside the on: block.
    push_block = _extract_block(on_block, r"^\s*push:\s*$")
    assert push_block.strip(), "Workflow must trigger on `push`"
    branches_block = _extract_block(push_block, r"^\s*branches:\s*$")
    # branches: can be a block list OR a flow list on the same line.
    flow_list_match = re.search(
        r"(?m)^\s*branches:\s*\[([^\]]+)\]\s*$", push_block
    )
    if flow_list_match:
        items = [s.strip().strip('"').strip("'")
                 for s in flow_list_match.group(1).split(",")]
        assert "main" in items, (
            f"`on.push.branches` must include 'main'; got {items!r}"
        )
    else:
        assert branches_block.strip(), (
            "`on.push.branches` must be specified and non-empty"
        )
        listed = re.findall(r"-\s*['\"]?([^'\"\s]+)['\"]?", branches_block)
        assert "main" in listed, (
            f"`on.push.branches` must include 'main'; got {listed!r}"
        )


def test_workflow_triggers_on_pull_request_to_main():
    text = _read_workflow_text()
    on_block = _on_block(text)
    assert on_block, "Workflow must define an `on:` section"
    pr_block = _extract_block(on_block, r"^\s*pull_request:\s*$")
    assert pr_block.strip(), "Workflow must trigger on `pull_request`"
    flow_list_match = re.search(
        r"(?m)^\s*branches:\s*\[([^\]]+)\]\s*$", pr_block
    )
    if flow_list_match:
        items = [s.strip().strip('"').strip("'")
                 for s in flow_list_match.group(1).split(",")]
        assert "main" in items, (
            f"`on.pull_request.branches` must include 'main'; got {items!r}"
        )
    else:
        branches_block = _extract_block(pr_block, r"^\s*branches:\s*$")
        assert branches_block.strip(), (
            "`on.pull_request.branches` must be specified and non-empty"
        )
        listed = re.findall(r"-\s*['\"]?([^'\"\s]+)['\"]?", branches_block)
        assert "main" in listed, (
            f"`on.pull_request.branches` must include 'main'; got {listed!r}"
        )


# ---------------------------------------------------------------------------
# Python 3.12 pinned via actions/setup-python
# ---------------------------------------------------------------------------

def test_setup_python_action_is_used():
    text = _read_workflow_text()
    assert re.search(r"uses:\s*actions/setup-python(?:@\S+)?", text), (
        "Workflow must use actions/setup-python to install Python"
    )


def test_python_version_is_pinned_to_3_12():
    """python-version must be exactly '3.12' (a single pinned value)."""
    text = _read_workflow_text()
    # All `python-version: X` lines in the file.
    matches = re.findall(
        r"(?m)^\s*python-version:\s*(.+?)\s*$", text
    )
    assert matches, (
        "actions/setup-python step must specify `with.python-version`"
    )
    # If the workflow defines multiple, every one must be exactly '3.12'.
    for raw in matches:
        # Reject list / matrix forms like `[3.11, 3.12]`.
        assert not raw.lstrip().startswith("["), (
            f"python-version must be a single pinned value '3.12', not a list: "
            f"{raw!r}"
        )
        value = raw.strip().strip('"').strip("'")
        assert value == "3.12", (
            f"python-version must be pinned to exactly '3.12'; got {raw!r}"
        )


# ---------------------------------------------------------------------------
# pip caching
# ---------------------------------------------------------------------------

def test_pip_dependencies_are_cached():
    """
    Pip caching can be expressed two ways:
      (a) `actions/setup-python` with `cache: pip`
      (b) an explicit `actions/cache` step keyed on pip
    Either is acceptable.
    """
    text = _read_workflow_text()

    # (a) setup-python with cache: pip
    if re.search(r"(?m)^\s*cache:\s*['\"]?pip['\"]?\s*$", text):
        return

    # (b) actions/cache referencing pip somewhere (path or key).
    if re.search(r"uses:\s*actions/cache(?:@\S+)?", text):
        # Look for any mention of `~/.cache/pip` or `pip` in a cache step's path/key.
        # This is a coarse check but covers idiomatic uses.
        if re.search(r"(?im)(~/\.cache/pip|\bpip\b)", text):
            return

    pytest.fail(
        "Workflow must cache pip dependencies (either via "
        "`actions/setup-python` with `cache: pip` or an `actions/cache` step "
        "keyed on pip), but no such configuration was found."
    )


# ---------------------------------------------------------------------------
# Install test requirements
# ---------------------------------------------------------------------------

def test_workflow_installs_test_requirements():
    """The workflow must install the project's test deps (requirements-dev.txt)."""
    text = _read_workflow_text()
    pattern = re.compile(
        r"pip\s+install\s+(?:[^&|;\n]*\s+)?-r\s+requirements-dev\.txt",
        re.IGNORECASE,
    )
    assert pattern.search(text), (
        "Workflow must install test requirements via "
        "`pip install -r requirements-dev.txt`, but no such step was found."
    )


def test_requirements_dev_file_exists_at_repo_root():
    """Sanity check: the file the workflow installs from must actually exist."""
    path = os.path.join(REPO_ROOT, "requirements-dev.txt")
    assert os.path.isfile(path), (
        "requirements-dev.txt must exist at repo root for the CI workflow to "
        "install test deps from it."
    )


# ---------------------------------------------------------------------------
# Runs `pytest -q`
# ---------------------------------------------------------------------------

def test_workflow_runs_pytest_quiet():
    """The workflow must actually invoke `pytest -q`."""
    text = _read_workflow_text()
    # Accept `pytest -q` with arbitrary extra args after `-q`, or extra args
    # before `-q` (but require the `-q` flag to be present).
    pat = re.compile(r"(?<!\w)pytest(?:\s+[^\n]*)?\s-q(?:\s|$)|(?<!\w)pytest\s+-q(?:\s|$)")
    assert pat.search(text), (
        "Workflow must run `pytest -q` in a step, but no such command was found."
    )


# ---------------------------------------------------------------------------
# Pytest failure must fail the workflow
# ---------------------------------------------------------------------------

def test_pytest_step_does_not_swallow_failures():
    """
    The pytest step must propagate failures. That means it must NOT:
      - end its command with `|| true` (or otherwise mask a non-zero exit).
      - have `continue-on-error: true` in the same step block.
    """
    text = _read_workflow_text()

    bad_masks = [
        r"pytest[^\n]*\|\|\s*true\b",
        r"pytest[^\n]*\|\|\s*exit\s+0\b",
        r"pytest[^\n]*;\s*true\b",
        r"pytest[^\n]*;\s*exit\s+0\b",
    ]
    for pat in bad_masks:
        assert not re.search(pat, text), (
            f"pytest invocation appears to mask its exit code with shell magic; "
            f"this would prevent the PR check from failing on test failure. "
            f"Offending pattern: {pat!r}"
        )

    # If any step has `continue-on-error: true`, make sure it's not the
    # pytest step. We do this by scanning each `- name:` step block.
    # Split the file into per-step chunks by lines starting with `      - `
    # (steps live under jobs.<job>.steps with 6-space indent typically).
    step_chunks = re.split(r"(?m)^\s*-\s+(?:name|run|uses|id|shell)\s*:", text)
    for chunk in step_chunks:
        if "pytest" in chunk and re.search(
            r"(?m)^\s*continue-on-error:\s*true\s*$", chunk
        ):
            pytest.fail(
                "pytest step must not set `continue-on-error: true`; it would "
                "prevent the PR check from failing on test failure."
            )


# ---------------------------------------------------------------------------
# Runner sanity
# ---------------------------------------------------------------------------

def test_at_least_one_job_specifies_runs_on():
    """GitHub requires every job to specify `runs-on:`."""
    text = _read_workflow_text()
    assert re.search(r"(?m)^\s*runs-on:\s*\S+", text), (
        "At least one job must specify a `runs-on:` runner"
    )
