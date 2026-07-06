"""Tests for materialize module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.grammar import KNOWN_DOMAINS, force_domain, parse_grammar
from src.expand import expand
from src.materialize import (
    PROVENANCE_SCHEMA_VERSION,
    MaterializeResult,
    child_name,
    materialize,
    _rewrite_kernel_imports,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_grammar(domain=None, seed=42):
    block = {
        "seed": seed,
        "slots": [
            {"name": "primitive_domain", "options": list(KNOWN_DOMAINS)},
            {"name": "dep_mode", "options": ["template", "vendor"]},
            {"name": "figure_profile", "options": ["minimal", "full"]},
            {"name": "qr_profile", "options": ["off", "on"]},
            {"name": "integrity_profile", "options": ["sha256", "merkle"]},
        ],
        "deps": [],
    }
    g = parse_grammar(block)
    if domain:
        g = force_domain(g, domain)
    return g


@pytest.fixture(params=list(KNOWN_DOMAINS))
def spec_for_domain(request, tmp_path):
    domain = request.param
    g = _make_grammar(domain=domain)
    return expand(g), domain


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# child_name
# ---------------------------------------------------------------------------


def test_child_name_starts_with_child(spec_for_domain):
    spec, _ = spec_for_domain
    assert child_name(spec).startswith("child_")


def test_child_name_includes_domain(spec_for_domain):
    spec, domain = spec_for_domain
    assert domain in child_name(spec)


def test_child_name_includes_hash(spec_for_domain):
    spec, _ = spec_for_domain
    assert spec.spec_hash in child_name(spec)


# ---------------------------------------------------------------------------
# _rewrite_kernel_imports
# ---------------------------------------------------------------------------


def test_rewrite_kernel_imports_from_src():
    code = "from src.primitives import foo"
    result = _rewrite_kernel_imports(code)
    assert "from primitives import foo" in result


def test_rewrite_kernel_imports_from_dot():
    code = "from .primitives import bar"
    result = _rewrite_kernel_imports(code)
    assert "from primitives import bar" in result


def test_rewrite_kernel_imports_no_change():
    code = "import math\nfrom os import path"
    assert _rewrite_kernel_imports(code) == code


# ---------------------------------------------------------------------------
# materialize
# ---------------------------------------------------------------------------


def test_materialize_returns_result(tmp_path, template_root):
    g = _make_grammar(domain="optimization")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert isinstance(result, MaterializeResult)


def test_materialize_creates_directory(tmp_path, template_root):
    g = _make_grammar(domain="dynamics")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert result.root.is_dir()


def test_materialize_name_matches_child_name(tmp_path, template_root):
    g = _make_grammar(domain="statistics")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert result.name == child_name(spec)


def test_materialize_provenance_exists(tmp_path, template_root):
    g = _make_grammar(domain="signal")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert result.provenance_path.exists()


def test_materialize_provenance_parseable(tmp_path, template_root):
    g = _make_grammar(domain="graph")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    prov = json.loads(result.provenance_path.read_text())
    assert prov["schema_version"] == PROVENANCE_SCHEMA_VERSION


def test_materialize_provenance_spec_hash(tmp_path, template_root):
    g = _make_grammar(domain="optimization")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    prov = json.loads(result.provenance_path.read_text())
    assert prov["spec"]["selections"]["primitive_domain"] == "optimization"


def test_materialize_tree_hash_recorded(tmp_path, template_root):
    g = _make_grammar(domain="dynamics")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert len(result.tree_hash) == 64


def test_materialize_tree_hash_stable(tmp_path, template_root):
    g = _make_grammar(domain="statistics", seed=7)
    spec = expand(g)
    r1 = materialize(spec, out_root=tmp_path / "a", template_root=template_root)
    r2 = materialize(spec, out_root=tmp_path / "b", template_root=template_root)
    assert r1.tree_hash == r2.tree_hash


def test_materialize_files_written(tmp_path, template_root):
    g = _make_grammar(domain="signal")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert len(result.files) > 0


def test_materialize_pyproject_exists(tmp_path, template_root):
    g = _make_grammar(domain="graph")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert (result.root / "pyproject.toml").exists()


def test_materialize_analysis_py_exists(tmp_path, template_root):
    g = _make_grammar(domain="optimization")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert (result.root / "analysis.py").exists()


def test_materialize_primitives_init_exists(tmp_path, template_root):
    g = _make_grammar(domain="dynamics")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert (result.root / "primitives" / "__init__.py").exists()


def test_materialize_manuscript_abstract_exists(tmp_path, template_root):
    g = _make_grammar(domain="statistics")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert (result.root / "manuscript" / "00_abstract.md").exists()


def test_materialize_clean_removes_old(tmp_path, template_root):
    g = _make_grammar(domain="signal")
    spec = expand(g)
    r1 = materialize(spec, out_root=tmp_path, template_root=template_root)
    # Create a stray file
    stray = r1.root / "stray.txt"
    stray.write_text("stray")
    assert stray.exists()
    # Clean materialize removes it
    r2 = materialize(spec, out_root=tmp_path, template_root=template_root, clean=True)
    assert not (r2.root / "stray.txt").exists()


def test_materialize_all_domains(tmp_path, template_root):
    for domain in KNOWN_DOMAINS:
        g = _make_grammar(domain=domain)
        spec = expand(g)
        result = materialize(spec, out_root=tmp_path / domain, template_root=template_root)
        assert result.root.is_dir()
        prov = json.loads(result.provenance_path.read_text())
        assert prov["spec"]["selections"]["primitive_domain"] == domain
