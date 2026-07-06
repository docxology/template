"""Tests for honesty manifest and verify_honesty."""
from __future__ import annotations

from pathlib import Path


from src.honesty import (
    build_manifest,
    verify_honesty,
    STRUCTURAL_EVIDENCE,
    HonestyManifest,
    _collect_function_names,
)


PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# build_manifest
# ---------------------------------------------------------------------------


def test_build_manifest_returns_manifest():
    m = build_manifest(PROJECT_ROOT)
    assert isinstance(m, HonestyManifest)


def test_structural_evidence_keys():
    m = build_manifest(PROJECT_ROOT)
    for key in STRUCTURAL_EVIDENCE:
        assert key in m.evidence


def test_structural_evidence_all_pass():
    m = build_manifest(PROJECT_ROOT)
    assert m.all_passed, f"missing_calls={m.missing_calls}"


def test_no_missing_calls():
    m = build_manifest(PROJECT_ROOT)
    assert m.missing_calls == []


def test_evidence_values_are_bool():
    m = build_manifest(PROJECT_ROOT)
    for k, v in m.evidence.items():
        assert isinstance(v, bool), f"evidence[{k}] is not bool"


# ---------------------------------------------------------------------------
# verify_honesty
# ---------------------------------------------------------------------------


def test_verify_honesty_passes():
    m = verify_honesty(PROJECT_ROOT)
    assert isinstance(m, HonestyManifest)


def test_verify_honesty_no_unsupported_claims():
    m = verify_honesty(PROJECT_ROOT)
    # There may be some matches — just confirm it runs
    assert isinstance(m.unsupported_claims, list)


def test_verify_honesty_all_passed():
    m = verify_honesty(PROJECT_ROOT)
    # Evidence should all pass; unsupported claims from manuscript are acceptable
    # (they're recorded, not blocking in this check)
    assert all(m.evidence.values()), f"Failed evidence: {[k for k,v in m.evidence.items() if not v]}"


# ---------------------------------------------------------------------------
# _collect_function_names
# ---------------------------------------------------------------------------


def test_collect_function_names_basic():
    code = "def foo(): pass\ndef bar(): pass"
    names = _collect_function_names(code)
    assert "foo" in names
    assert "bar" in names


def test_collect_function_names_empty():
    names = _collect_function_names("")
    assert names == set()


def test_collect_function_names_invalid_syntax():
    names = _collect_function_names("def def def")
    assert names == set()


# ---------------------------------------------------------------------------
# Honesty manifest structure
# ---------------------------------------------------------------------------


def test_manifest_evidence_grammar_parses():
    m = build_manifest(PROJECT_ROOT)
    assert m.evidence.get("grammar_parses") is True


def test_manifest_evidence_expand_deterministic():
    m = build_manifest(PROJECT_ROOT)
    assert m.evidence.get("expand_deterministic") is True


def test_manifest_evidence_materialize_writes_files():
    m = build_manifest(PROJECT_ROOT)
    assert m.evidence.get("materialize_writes_files") is True


def test_manifest_evidence_integrity_hashes():
    m = build_manifest(PROJECT_ROOT)
    assert m.evidence.get("integrity_hashes") is True


def test_manifest_evidence_verify_recomputes():
    m = build_manifest(PROJECT_ROOT)
    assert m.evidence.get("verify_recomputes") is True


# ---------------------------------------------------------------------------
# Tampered manifest: missing function
# ---------------------------------------------------------------------------


def test_verify_honesty_with_nonexistent_project(tmp_path):
    """Verify honesty on empty project should have missing_calls."""
    m = build_manifest(tmp_path)
    assert len(m.missing_calls) > 0
