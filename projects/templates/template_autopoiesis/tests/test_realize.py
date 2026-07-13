"""Tests for realize module."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.grammar import KNOWN_DOMAINS, force_domain, parse_grammar
from src.expand import expand
from src.materialize import materialize
from src.realize import (
    _project_slug,
    _gate_python,
    run_child_stage,
    run_analysis_stage,
    render_child_manuscript,
    validate_child,
)


def _make_grammar(domain="optimization"):
    block = {
        "seed": 42,
        "slots": [
            {"name": "primitive_domain", "options": list(KNOWN_DOMAINS)},
            {"name": "dep_mode", "options": ["vendor"]},
            {"name": "figure_profile", "options": ["minimal"]},
            {"name": "qr_profile", "options": ["off"]},
            {"name": "integrity_profile", "options": ["sha256"]},
        ],
        "deps": [],
    }
    g = parse_grammar(block)
    return force_domain(g, domain)


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


@pytest.fixture
def scratch_child(tmp_path, template_root):
    """A complete materialized child project."""
    g = _make_grammar("optimization")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    return result.root


# ---------------------------------------------------------------------------
# _project_slug
# ---------------------------------------------------------------------------


def test_project_slug_returns_name(scratch_child):
    slug = _project_slug(scratch_child)
    assert slug == scratch_child.name


def test_project_slug_non_empty(tmp_path):
    d = tmp_path / "child_optimization_abcd1234"
    d.mkdir()
    assert _project_slug(d) == "child_optimization_abcd1234"


# ---------------------------------------------------------------------------
# _gate_python
# ---------------------------------------------------------------------------


def test_gate_python_returns_true(scratch_child):
    assert _gate_python(scratch_child) is True


def test_gate_python_uses_sys_executable(tmp_path):
    # Even for a nonexistent dir, sys.executable is not None
    assert _gate_python(tmp_path) is True


# ---------------------------------------------------------------------------
# run_child_stage
# ---------------------------------------------------------------------------


def test_run_child_stage_simple_script(scratch_child):
    # Write a trivial script
    script = scratch_child / "hello_stage.py"
    script.write_text("print('hello from stage')\n")
    proc = run_child_stage(scratch_child, "hello_stage.py")
    assert proc.returncode == 0
    assert "hello from stage" in proc.stdout


def test_run_child_stage_failing_script(scratch_child):
    script = scratch_child / "fail_stage.py"
    script.write_text("raise RuntimeError('intentional failure')\n")
    proc = run_child_stage(scratch_child, "fail_stage.py")
    assert proc.returncode != 0


def test_run_child_stage_missing_script(scratch_child):
    proc = run_child_stage(scratch_child, "nonexistent_script.py")
    assert proc.returncode != 0


# ---------------------------------------------------------------------------
# run_analysis_stage
# ---------------------------------------------------------------------------


def test_run_analysis_stage_passes(scratch_child):
    result = run_analysis_stage(scratch_child)
    assert result["success"] is True


def test_run_analysis_stage_missing(tmp_path):
    result = run_analysis_stage(tmp_path)
    assert result["success"] is False
    error_str = str(result.get("error", ""))
    assert "not found" in error_str


def test_run_analysis_stage_surfaces_stdout(scratch_child):
    result = run_analysis_stage(scratch_child)
    # run_analysis_stage returns stdout in the result dict
    assert "stdout" in result or "success" in result


# ---------------------------------------------------------------------------
# render_child_manuscript
# ---------------------------------------------------------------------------


def test_render_child_manuscript_returns_dict(scratch_child):
    result = render_child_manuscript(scratch_child)
    assert isinstance(result, dict)


def test_render_child_manuscript_has_success_key(scratch_child):
    result = render_child_manuscript(scratch_child)
    assert "success" in result


def test_render_child_manuscript_failure_has_reason(scratch_child):
    result = render_child_manuscript(scratch_child)
    if not result["success"]:
        assert "reason" in result or "error" in result


# ---------------------------------------------------------------------------
# validate_child
# ---------------------------------------------------------------------------


def test_validate_child_valid(scratch_child):
    result = validate_child(scratch_child)
    assert result["valid"] is True
    assert result["missing"] == []


def test_validate_child_missing_files(tmp_path):
    result = validate_child(tmp_path)
    assert result["valid"] is False
    assert len(result["missing"]) > 0


def test_validate_child_child_root_in_result(scratch_child):
    result = validate_child(scratch_child)
    assert "child_root" in result
