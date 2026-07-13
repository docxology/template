"""Tests for emit_templates module."""

from __future__ import annotations

import py_compile
import tempfile

import pytest

from src.emit_templates import (
    TEMPLATE_PATHS,
    apply_template,
    emit_all,
    emit_file,
)
from src.grammar import KNOWN_DOMAINS, force_domain, parse_grammar
from src.expand import expand


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_grammar(domain: str = "optimization", seed: int = 42):
    block = {
        "seed": seed,
        "slots": [
            {"name": "primitive_domain", "options": list(KNOWN_DOMAINS)},
            {"name": "track", "options": ["analytical", "empirical", "hybrid"]},
            {"name": "section_set", "options": ["minimal", "standard", "extended"]},
            {"name": "figure_profile", "options": ["minimal", "full"]},
            {"name": "qr_profile", "options": ["off", "on"]},
            {"name": "integrity_profile", "options": ["sha256", "merkle"]},
        ],
        "deps": [],
    }
    g = parse_grammar(block)
    return force_domain(g, domain)


def _make_spec(domain: str = "optimization", seed: int = 42):
    return expand(_make_grammar(domain=domain, seed=seed))


# ---------------------------------------------------------------------------
# apply_template
# ---------------------------------------------------------------------------


def test_apply_template_substitutes_all_tokens():
    """apply_template replaces every @@KEY@@ present in the substitutions dict."""
    tmpl = "Hello @@NAME@@, your code is @@CODE@@."
    result = apply_template(tmpl, {"NAME": "world", "CODE": "42"})
    assert result == "Hello world, your code is 42."


def test_apply_template_leaves_unknown_tokens_as_is():
    """Unknown @@KEY@@ tokens not in substitutions are preserved unchanged."""
    tmpl = "known=@@KNOWN@@  unknown=@@UNKNOWN@@"
    result = apply_template(tmpl, {"KNOWN": "yes"})
    assert "yes" in result
    assert "@@UNKNOWN@@" in result


def test_apply_template_empty_substitutions_returns_template_unchanged():
    """An empty substitutions dict returns the template verbatim."""
    tmpl = "@@DOMAIN@@ @@SPEC_HASH@@"
    assert apply_template(tmpl, {}) == tmpl


def test_apply_template_no_placeholders():
    """A template without any @@KEY@@ tokens is returned unchanged."""
    tmpl = "plain text, no tokens"
    assert apply_template(tmpl, {"X": "y"}) == tmpl


def test_apply_template_multiple_occurrences():
    """The same @@KEY@@ appearing multiple times is replaced at every occurrence."""
    tmpl = "@@X@@ and @@X@@ again"
    result = apply_template(tmpl, {"X": "hello"})
    assert result == "hello and hello again"


# ---------------------------------------------------------------------------
# emit_file — known filenames return non-empty content
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", list(TEMPLATE_PATHS))
def test_emit_file_returns_non_empty_for_known_paths(filename):
    """emit_file returns non-empty content for every registered template path."""
    spec = _make_spec()
    content = emit_file(filename, spec)
    assert isinstance(content, str)
    assert len(content) > 0


def test_emit_file_raises_for_unknown_filename():
    """emit_file raises KeyError for an unregistered filename."""
    spec = _make_spec()
    with pytest.raises(KeyError):
        emit_file("not_a_real_file.xyz", spec)


# ---------------------------------------------------------------------------
# emit_all — structure
# ---------------------------------------------------------------------------


def test_emit_all_returns_dict_with_all_expected_paths():
    """emit_all returns a dict containing every path in TEMPLATE_PATHS."""
    spec = _make_spec()
    result = emit_all(spec)
    for path in TEMPLATE_PATHS:
        assert path in result, f"Missing path: {path}"


def test_emit_all_values_are_non_empty_strings():
    """Every value in the emit_all result is a non-empty string."""
    spec = _make_spec()
    for path, content in emit_all(spec).items():
        assert isinstance(content, str) and len(content) > 0, f"Empty content for {path}"


# ---------------------------------------------------------------------------
# emit_all — determinism
# ---------------------------------------------------------------------------


def test_emit_all_is_deterministic():
    """Calling emit_all twice with the same spec produces identical output."""
    spec = _make_spec(domain="dynamics", seed=7)
    assert emit_all(spec) == emit_all(spec)


def test_emit_all_different_specs_produce_different_output():
    """Two specs with different domains produce different emit_all output."""
    spec_a = _make_spec(domain="optimization", seed=42)
    spec_b = _make_spec(domain="signal", seed=99)
    assert emit_all(spec_a) != emit_all(spec_b)


# ---------------------------------------------------------------------------
# emit_all — domain propagation
# ---------------------------------------------------------------------------


def test_emit_all_uses_correct_domain_in_analysis_py():
    """analysis.py content includes the spec's primitive_domain."""
    spec = _make_spec(domain="graph")
    files = emit_all(spec)
    assert "graph" in files["analysis.py"]


def test_emit_all_uses_correct_domain_in_all_templates():
    """The spec's domain appears in every rendered file."""
    domain = "statistics"
    spec = _make_spec(domain=domain)
    files = emit_all(spec)
    for path, content in files.items():
        assert domain in content, f"Domain '{domain}' missing from {path}"


# ---------------------------------------------------------------------------
# emit_all — spec_hash propagation
# ---------------------------------------------------------------------------


def test_emit_all_includes_spec_hash_in_analysis_py():
    """analysis.py rendered content contains the spec_hash."""
    spec = _make_spec(domain="dynamics", seed=5)
    files = emit_all(spec)
    assert spec.spec_hash in files["analysis.py"]


def test_emit_all_includes_spec_hash_in_abstract():
    """Manuscript abstract rendered content contains the spec_hash."""
    spec = _make_spec(domain="optimization", seed=3)
    files = emit_all(spec)
    assert spec.spec_hash in files["manuscript/00_abstract.md"]


# ---------------------------------------------------------------------------
# Python syntax validity
# ---------------------------------------------------------------------------


def test_analysis_py_template_is_syntactically_valid_python():
    """Rendered analysis.py must compile without SyntaxError."""
    spec = _make_spec(domain="signal")
    content = emit_file("analysis.py", spec)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(content)
        tmp = f.name
    py_compile.compile(tmp, doraise=True)  # raises py_compile.PyCompileError on failure


def test_test_analysis_py_template_is_syntactically_valid_python():
    """Rendered tests/test_analysis.py must compile without SyntaxError."""
    spec = _make_spec(domain="graph")
    content = emit_file("tests/test_analysis.py", spec)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(content)
        tmp = f.name
    py_compile.compile(tmp, doraise=True)


# ---------------------------------------------------------------------------
# pyproject.toml — domain in project name
# ---------------------------------------------------------------------------


def test_pyproject_toml_contains_domain_in_project_name():
    """Rendered pyproject.toml has the domain in the [project] name field."""
    spec = _make_spec(domain="dynamics")
    content = emit_file("pyproject.toml", spec)
    assert 'name = "child_dynamics"' in content


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_pyproject_toml_domain_parametrized(domain):
    """pyproject.toml project name contains the domain for every known domain."""
    spec = _make_spec(domain=domain)
    content = emit_file("pyproject.toml", spec)
    assert f'name = "child_{domain}"' in content


# ---------------------------------------------------------------------------
# Grammar hash propagation
# ---------------------------------------------------------------------------


def test_emit_all_includes_grammar_hash_in_analysis_py():
    """analysis.py rendered content contains the grammar_hash."""
    spec = _make_spec(domain="optimization", seed=11)
    files = emit_all(spec)
    assert spec.grammar_hash in files["analysis.py"]


# ---------------------------------------------------------------------------
# TEMPLATE_PATHS completeness
# ---------------------------------------------------------------------------


def test_template_paths_includes_all_expected_keys():
    """TEMPLATE_PATHS must include all required child project files."""
    expected = {
        "analysis.py",
        "tests/test_analysis.py",
        "pyproject.toml",
        "manuscript/00_abstract.md",
        "manuscript/01_introduction.md",
        "manuscript/03_results.md",
        "manuscript/06_limitations.md",
    }
    assert expected.issubset(set(TEMPLATE_PATHS))


# ---------------------------------------------------------------------------
# emit_all vs emit_file consistency
# ---------------------------------------------------------------------------


def test_emit_all_and_emit_file_agree():
    """emit_all and emit_file produce identical content for the same spec."""
    spec = _make_spec(domain="statistics", seed=99)
    bulk = emit_all(spec)
    for path in TEMPLATE_PATHS:
        assert bulk[path] == emit_file(path, spec), f"Mismatch for {path}"
