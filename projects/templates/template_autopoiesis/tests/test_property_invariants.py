"""Hypothesis-backed property invariants for template_autopoiesis."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.grammar import KNOWN_DOMAINS, parse_grammar, force_domain
from src.expand import expand
from src.materialize import materialize
from src.verify import verify_child
from src.sealing import qr_matrix


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_block(seed=42):
    return {
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


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Grammar product invariants
# ---------------------------------------------------------------------------


@given(st.integers(min_value=1, max_value=200))
def test_grammar_product_is_product_of_option_counts(seed):
    g = parse_grammar(_make_block(seed=seed))
    expected = 1
    for s in g.slots:
        expected *= len(s.options)
    assert g.product_size == expected


@given(st.integers(min_value=1, max_value=200))
def test_effective_product_le_product(seed):
    g = parse_grammar(_make_block(seed=seed))
    assert g.effective_product_size <= g.product_size


@given(st.integers(min_value=1, max_value=200))
def test_grammar_hash_stable(seed):
    g1 = parse_grammar(_make_block(seed=seed))
    g2 = parse_grammar(_make_block(seed=seed))
    assert g1.grammar_hash == g2.grammar_hash


# ---------------------------------------------------------------------------
# Expand determinism across seeds
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=10**9))
@settings(max_examples=50)
def test_expand_deterministic_any_seed(seed):
    g = parse_grammar(_make_block(seed=42))
    s1 = expand(g, seed=seed)
    s2 = expand(g, seed=seed)
    assert s1.spec_hash == s2.spec_hash


@given(st.integers(min_value=0, max_value=10**9))
@settings(max_examples=50)
def test_expand_domain_in_known_any_seed(seed):
    g = parse_grammar(_make_block(seed=42))
    spec = expand(g, seed=seed)
    assert spec.primitive_domain in KNOWN_DOMAINS


# ---------------------------------------------------------------------------
# Double materialize byte-stable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_double_materialize_byte_stable(domain, tmp_path, template_root):
    g = parse_grammar(_make_block(seed=7))
    g = force_domain(g, domain)
    spec = expand(g)
    r1 = materialize(spec, out_root=tmp_path / "a", template_root=template_root)
    r2 = materialize(spec, out_root=tmp_path / "b", template_root=template_root)
    assert r1.tree_hash == r2.tree_hash


# ---------------------------------------------------------------------------
# Verify passes clean
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_verify_passes_clean_per_domain(domain, tmp_path, template_root):
    g = parse_grammar(_make_block(seed=7))
    g = force_domain(g, domain)
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    report = verify_child(result.root)
    assert report.all_passed


# ---------------------------------------------------------------------------
# Verify fails on tamper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_verify_fails_tamper_per_domain(domain, tmp_path, template_root):
    g = parse_grammar(_make_block(seed=7))
    g = force_domain(g, domain)
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    # Tamper with analysis.py
    f = result.root / "analysis.py"
    if f.exists():
        f.write_text(f.read_text() + "\n# tampered\n")
    report = verify_child(result.root)
    assert not report.all_passed


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_verify_fails_delete_per_domain(domain, tmp_path, template_root):
    g = parse_grammar(_make_block(seed=7))
    g = force_domain(g, domain)
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    prov = json.loads((result.root / "provenance.json").read_text())
    first_file = prov["files"][0]
    (result.root / first_file).unlink(missing_ok=True)
    report = verify_child(result.root)
    assert not report.all_passed


# ---------------------------------------------------------------------------
# Honesty invariants
# ---------------------------------------------------------------------------


def test_honesty_all_evidence_pass(template_root):
    from src.honesty import build_manifest
    m = build_manifest(template_root)
    assert all(m.evidence.values()), f"Failed: {[k for k, v in m.evidence.items() if not v]}"


# ---------------------------------------------------------------------------
# QR invariants
# ---------------------------------------------------------------------------


@given(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
@settings(max_examples=20)
def test_qr_matrix_is_square(data):
    matrix = qr_matrix(data)
    n = len(matrix)
    assert n >= 5
    for row in matrix:
        assert len(row) == n


@given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
@settings(max_examples=20)
def test_qr_deterministic_property(data):
    m1 = qr_matrix(data)
    m2 = qr_matrix(data)
    assert m1 == m2
