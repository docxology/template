"""Tests for sealing a child project (seal_child flow)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.grammar import KNOWN_DOMAINS, force_domain, parse_grammar
from src.expand import expand
from src.materialize import materialize
from src.sealing import build_payload, qr_matrix
from src.verify import verify_seal


def _make_grammar(domain=None):
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
    if domain:
        g = force_domain(g, domain)
    return g


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


@pytest.fixture
def child_with_seal(tmp_path, template_root):
    """A child project with a seal.json written."""
    g = _make_grammar(domain="optimization")
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)

    payload = build_payload(spec.spec_hash, result.tree_hash, spec.seed)
    matrix = qr_matrix(payload)
    seal = {
        "spec_hash": spec.spec_hash,
        "tree_hash": result.tree_hash,
        "seed": spec.seed,
        "payload": payload,
        "qr_size": len(matrix),
    }
    (result.root / "seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True))
    return result.root, spec, seal


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_seal_file_created(child_with_seal):
    child_root, _, _ = child_with_seal
    assert (child_root / "seal.json").exists()


def test_seal_parseable(child_with_seal):
    child_root, _, _ = child_with_seal
    seal = json.loads((child_root / "seal.json").read_text())
    assert "spec_hash" in seal
    assert "tree_hash" in seal
    assert "seed" in seal


def test_seal_spec_hash_matches(child_with_seal):
    child_root, spec, _ = child_with_seal
    seal = json.loads((child_root / "seal.json").read_text())
    assert seal["spec_hash"] == spec.spec_hash


def test_seal_qr_size_positive(child_with_seal):
    child_root, _, _ = child_with_seal
    seal = json.loads((child_root / "seal.json").read_text())
    assert seal["qr_size"] >= 5  # at minimum the fallback 5x5


def test_verify_seal_passes_with_seal(child_with_seal):
    child_root, _, _ = child_with_seal
    report = verify_seal(child_root)
    names = {c.name: c.passed for c in report.checks}
    assert names["seal_exists"] is True
    assert names["seal_parseable"] is True
    assert names["seal_has_spec_hash"] is True


def test_seal_payload_is_valid_json(child_with_seal):
    child_root, _, _ = child_with_seal
    seal = json.loads((child_root / "seal.json").read_text())
    payload_parsed = json.loads(seal["payload"])
    assert payload_parsed["spec_hash"] == seal["spec_hash"]


def test_seal_tree_hash_in_payload(child_with_seal):
    child_root, _, _ = child_with_seal
    seal = json.loads((child_root / "seal.json").read_text())
    payload = json.loads(seal["payload"])
    assert "tree_hash" in payload
