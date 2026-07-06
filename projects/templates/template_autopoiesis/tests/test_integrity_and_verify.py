"""Tests for integrity hashing and verify module."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.integrity import sha256_text, sha256_bytes, tree_hash_from_content_hashes, merkle_root, tree_hash
from src.grammar import KNOWN_DOMAINS, force_domain, parse_grammar
from src.expand import expand
from src.materialize import materialize
from src.verify import verify_child, verify_child_full, verify_seal


# ---------------------------------------------------------------------------
# sha256_text
# ---------------------------------------------------------------------------


def test_sha256_text_returns_64_chars():
    h = sha256_text("hello")
    assert len(h) == 64


def test_sha256_text_deterministic():
    assert sha256_text("abc") == sha256_text("abc")


def test_sha256_text_different_inputs():
    assert sha256_text("abc") != sha256_text("def")


def test_sha256_text_empty():
    h = sha256_text("")
    assert len(h) == 64


# ---------------------------------------------------------------------------
# sha256_bytes
# ---------------------------------------------------------------------------


def test_sha256_bytes_returns_64_chars():
    h = sha256_bytes(b"hello")
    assert len(h) == 64


def test_sha256_bytes_deterministic():
    assert sha256_bytes(b"data") == sha256_bytes(b"data")


def test_sha256_bytes_different():
    assert sha256_bytes(b"a") != sha256_bytes(b"b")


# ---------------------------------------------------------------------------
# tree_hash_from_content_hashes
# ---------------------------------------------------------------------------


def test_tree_hash_stable_order_independent():
    d1 = {"b.txt": sha256_text("b"), "a.txt": sha256_text("a")}
    d2 = {"a.txt": sha256_text("a"), "b.txt": sha256_text("b")}
    assert tree_hash_from_content_hashes(d1) == tree_hash_from_content_hashes(d2)


def test_tree_hash_changes_on_content_change():
    d1 = {"a.txt": sha256_text("content1")}
    d2 = {"a.txt": sha256_text("content2")}
    assert tree_hash_from_content_hashes(d1) != tree_hash_from_content_hashes(d2)


def test_tree_hash_changes_on_new_file():
    d1 = {"a.txt": sha256_text("c")}
    d2 = {"a.txt": sha256_text("c"), "b.txt": sha256_text("d")}
    assert tree_hash_from_content_hashes(d1) != tree_hash_from_content_hashes(d2)


def test_tree_hash_alias():
    d = {"x": "abc"}
    assert tree_hash(d) == tree_hash_from_content_hashes(d)


# ---------------------------------------------------------------------------
# merkle_root
# ---------------------------------------------------------------------------


def test_merkle_root_empty():
    h = merkle_root([])
    assert len(h) == 64


def test_merkle_root_single():
    h = sha256_text("leaf")
    assert merkle_root([h]) == h


def test_merkle_root_two_leaves():
    h1 = sha256_text("a")
    h2 = sha256_text("b")
    expected = sha256_text(h1 + h2)
    assert merkle_root([h1, h2]) == expected


def test_merkle_root_odd_leaves():
    h1 = sha256_text("a")
    h2 = sha256_text("b")
    h3 = sha256_text("c")
    # h3 paired with itself at odd level
    result = merkle_root([h1, h2, h3])
    assert len(result) == 64


def test_merkle_root_deterministic():
    hashes = [sha256_text(str(i)) for i in range(8)]
    assert merkle_root(hashes) == merkle_root(hashes)


def test_merkle_root_order_sensitive():
    h1 = sha256_text("a")
    h2 = sha256_text("b")
    assert merkle_root([h1, h2]) != merkle_root([h2, h1])


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


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


@pytest.fixture
def clean_child(tmp_path, template_root):
    """A freshly materialized child for a fixed domain."""
    g = _make_grammar(domain="optimization")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    return result.root


# ---------------------------------------------------------------------------
# verify_child on clean child
# ---------------------------------------------------------------------------


def test_verify_child_passes_clean(clean_child):
    report = verify_child(clean_child)
    assert report.all_passed, [c for c in report.checks if not c.passed]


def test_verify_child_provenance_exists(clean_child):
    report = verify_child(clean_child)
    names = {c.name: c.passed for c in report.checks}
    assert names["provenance_exists"] is True


def test_verify_child_tree_hash_matches(clean_child):
    report = verify_child(clean_child)
    names = {c.name: c.passed for c in report.checks}
    assert names["tree_hash_matches"] is True


# ---------------------------------------------------------------------------
# verify_child fails on tampered file
# ---------------------------------------------------------------------------


def test_verify_fails_on_tampered_file(clean_child):
    # Tamper with analysis.py
    analysis = clean_child / "analysis.py"
    if analysis.exists():
        analysis.write_text(analysis.read_text() + "\n# tampered\n")
    report = verify_child(clean_child)
    assert not report.all_passed


def test_verify_fails_on_missing_file(clean_child):
    prov = json.loads((clean_child / "provenance.json").read_text())
    # Delete the first listed file
    first_file = prov["files"][0]
    (clean_child / first_file).unlink(missing_ok=True)
    report = verify_child(clean_child)
    assert not report.all_passed


def test_verify_fails_missing_provenance(tmp_path):
    # No provenance.json at all
    report = verify_child(tmp_path)
    assert not report.all_passed
    names = {c.name for c in report.checks if not c.passed}
    assert "provenance_exists" in names


# ---------------------------------------------------------------------------
# verify_child_full
# ---------------------------------------------------------------------------


def test_verify_child_full_passes_clean(clean_child):
    report = verify_child_full(clean_child)
    # schema_version_correct should also pass
    names = {c.name: c.passed for c in report.checks}
    assert names.get("schema_version_correct") is True


# ---------------------------------------------------------------------------
# verify_seal
# ---------------------------------------------------------------------------


def test_verify_seal_missing(tmp_path):
    report = verify_seal(tmp_path)
    names = {c.name: c.passed for c in report.checks}
    assert names["seal_exists"] is False


def test_verify_seal_with_seal_json(tmp_path):
    seal = {"spec_hash": "abc123", "tree_hash": "def456", "seed": 42}
    (tmp_path / "seal.json").write_text(json.dumps(seal))
    report = verify_seal(tmp_path)
    names = {c.name: c.passed for c in report.checks}
    assert names["seal_exists"] is True
    assert names["seal_parseable"] is True
    assert names["seal_has_spec_hash"] is True


# ---------------------------------------------------------------------------
# verify_child with malformed provenance.json — lines 32-34
# ---------------------------------------------------------------------------


def test_verify_child_malformed_provenance(tmp_path):
    """verify_child with garbage JSON in provenance.json hits the except branch."""
    prov_path = tmp_path / "provenance.json"
    prov_path.write_text("{this is not valid json!!!")  # malformed
    report = verify_child(tmp_path)
    assert not report.all_passed
    names = {c.name: c.passed for c in report.checks}
    assert names["provenance_exists"] is True
    assert names["provenance_parseable"] is False


# ---------------------------------------------------------------------------
# verify_seal with malformed seal.json — line 87
# ---------------------------------------------------------------------------


def test_verify_seal_malformed_seal_json(tmp_path):
    """verify_seal with garbage JSON in seal.json hits the seal_parseable=False branch."""
    seal_path = tmp_path / "seal.json"
    seal_path.write_text("{not valid json at all")
    report = verify_seal(tmp_path)
    names = {c.name: c.passed for c in report.checks}
    assert names["seal_exists"] is True
    assert names["seal_parseable"] is False


def test_verify_seal_with_spec_hash(tmp_path):
    """verify_seal with a seal.json that has spec_hash hits the positive branch."""
    seal = {"spec_hash": "deadbeef" * 8}
    (tmp_path / "seal.json").write_text(json.dumps(seal))
    report = verify_seal(tmp_path)
    names = {c.name: c.passed for c in report.checks}
    assert names["seal_exists"] is True
    assert names["seal_parseable"] is True
    assert names["seal_has_spec_hash"] is True


def test_verify_seal_without_spec_hash(tmp_path):
    """verify_seal with a seal.json missing spec_hash hits the negative branch."""
    seal = {"tree_hash": "abc", "seed": 0}
    (tmp_path / "seal.json").write_text(json.dumps(seal))
    report = verify_seal(tmp_path)
    names = {c.name: c.passed for c in report.checks}
    assert names["seal_exists"] is True
    assert names["seal_parseable"] is True
    assert names["seal_has_spec_hash"] is False


# ---------------------------------------------------------------------------
# verify_child_full — missing provenance triggers the except branch at 114-122
# ---------------------------------------------------------------------------


def test_verify_child_full_missing_provenance(tmp_path):
    """verify_child_full with no provenance.json: prov_path.exists() is False, skip schema check."""
    report = verify_child_full(tmp_path)
    assert not report.all_passed
    names = {c.name for c in report.checks if not c.passed}
    assert "provenance_exists" in names
    # schema_version_correct should NOT be in checks (provenance doesn't exist)
    all_names = {c.name for c in report.checks}
    assert "schema_version_correct" not in all_names


def test_verify_child_full_malformed_provenance_skips_schema(tmp_path):
    """verify_child_full with malformed provenance skips schema check (except branch)."""
    prov_path = tmp_path / "provenance.json"
    prov_path.write_text("{broken json!")
    report = verify_child_full(tmp_path)
    # The except in verify_child_full means schema_version_correct is skipped (pass)
    all_names = {c.name for c in report.checks}
    assert "schema_version_correct" not in all_names
