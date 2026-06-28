"""Tests for src.evidence — evidence registry and claim-ledger alignment."""

from __future__ import annotations

import json
from pathlib import Path

from config import load_gold_refinement_config
from evidence import (
    EvidenceEntry,
    EvidenceRegistry,
    build_evidence_registry,
    check_claim_ledger_alignment,
    write_evidence_registry,
)


class TestBuildEvidenceRegistry:
    def test_registry_has_entries(self):
        project_root = Path(__file__).resolve().parent.parent
        cfg = load_gold_refinement_config(project_root)
        registry = build_evidence_registry(cfg, project_root)
        assert registry.total_claims > 0
        assert registry.total_claims == len(cfg.contribution_claims)

    def test_all_claims_supported(self):
        """All contribution claims should have valid evidence sources."""
        project_root = Path(__file__).resolve().parent.parent
        cfg = load_gold_refinement_config(project_root)
        registry = build_evidence_registry(cfg, project_root)
        assert registry.is_passing, f"Unsupported claims: {[e.claim_name for e in registry.entries if not e.supported]}"

    def test_support_rate(self):
        project_root = Path(__file__).resolve().parent.parent
        cfg = load_gold_refinement_config(project_root)
        registry = build_evidence_registry(cfg, project_root)
        assert 0.0 <= registry.support_rate <= 1.0

    def test_evidence_entry_dict(self):
        entry = EvidenceEntry(
            claim_name="test",
            claim_statement="test claim",
            evidence_source="src/refinery.py",
            boundary="local",
            supported=True,
        )
        d = entry.as_dict()
        assert d["claim_name"] == "test"
        assert d["supported"] is True


class TestWriteEvidenceRegistry:
    def test_write_json(self, tmp_path):
        registry = EvidenceRegistry(
            entries=[
                EvidenceEntry("c1", "stmt", "src/x.py", "local", True),
                EvidenceEntry("c2", "stmt", "src/y.py", "local", False, "File not found"),
            ],
            total_claims=2,
            supported_claims=1,
            unsupported_claims=1,
        )
        out = write_evidence_registry(registry, tmp_path / "evidence.json")
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["total_claims"] == 2
        assert data["supported_claims"] == 1
        assert data["is_passing"] is False
        assert len(data["entries"]) == 2


class TestClaimLedgerAlignment:
    def test_alignment_passes(self):
        """Config contribution_claims should align with claim_ledger.yaml."""
        project_root = Path(__file__).resolve().parent.parent
        cfg = load_gold_refinement_config(project_root)
        ledger_path = project_root / "data" / "claim_ledger.yaml"
        mismatches = check_claim_ledger_alignment(cfg, ledger_path)
        assert not mismatches, "Claim ledger mismatches:\n" + "\n".join(mismatches)

    def test_missing_ledger(self, tmp_path):
        cfg = load_gold_refinement_config(tmp_path)
        mismatches = check_claim_ledger_alignment(cfg, tmp_path / "nonexistent.yaml")
        assert len(mismatches) == 1
        assert "not found" in mismatches[0]
