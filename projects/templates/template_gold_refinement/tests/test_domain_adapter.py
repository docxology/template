from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from domain_adapter import load_domain_profile


def _write_domain_profile(tmp_path: Path) -> Path:
    (tmp_path / "domain_profile.yaml").write_text(
        yaml.dump(
            {
                "domain": "clinical_evidence_synthesis",
                "display_name": "Clinical Evidence",
                "required_packages": ["pandas", "numpy"],
                "preferred_outputs": ["pdf", "html"],
                "validation_gates": ["config_schema", "domain_validator"],
                "figure_types": ["evidence_flow"],
                "citation_policy": "local_source_or_scholarly",
                "review_gates": ["evidence completeness", "citation accuracy"],
                "source_policy": "Claims must cite local or scholarly evidence.",
                "artifact_expectations": ["output/reports/domain_profile.json"],
                "benchmark_rubric": {
                    "name": "clinical-readiness",
                    "dimensions": [
                        {"name": "evidence_coverage", "weight": 2.0, "minimum": 0.0, "maximum": 1.0},
                        {"name": "citation_accuracy", "weight": 1.0, "minimum": 0.0, "maximum": 1.0},
                    ],
                },
                "stage_mappings": [
                    {
                        "refinery_stage": "ore",
                        "domain_operation": "ingest the raw literature corpus",
                        "purity_target": 0.375,
                        "evidence_surface": "manuscript/config.yaml",
                    },
                    {
                        "refinery_stage": "certification",
                        "domain_operation": "run the publication gate",
                        "purity_target": 0.999999999,
                        "evidence_surface": "scripts/refinement_analysis.py",
                    },
                ],
                "analogy_boundary": {
                    "thesis": "The analogy is load-bearing for staged purification and source-owned validation.",
                    "limits": [
                        "It does not certify domain truth without domain-specific validators.",
                    ],
                    "non_claims": [
                        "The analogy is universal.",
                    ],
                },
                "llm_prompt_guidance": "Use only the configured lexicon and validators.",
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_load_domain_profile_parses_stage_map_and_rubric(tmp_path):
    root = _write_domain_profile(tmp_path)
    profile = load_domain_profile(root)

    assert profile.domain == "clinical_evidence_synthesis"
    assert profile.display_name == "Clinical Evidence"
    assert profile.required_packages == ("pandas", "numpy")
    assert profile.preferred_outputs == ("pdf", "html")
    assert profile.validation_gates == ("config_schema", "domain_validator")
    assert profile.review_gates == ("evidence completeness", "citation accuracy")
    assert profile.stage_count == 2
    assert profile.metric_count == 2
    assert "ingest the raw literature corpus" in profile.stage_rows()
    assert "evidence_coverage" in profile.metric_rows()
    assert "The analogy is load-bearing" in profile.boundary_summary()
    assert "The analogy is universal." in profile.boundary_summary()
    assert profile.purity_from_metrics({"evidence_coverage": 0.9, "citation_accuracy": 0.4}) == pytest.approx(
        0.7333333333
    )


def test_load_domain_profile_requires_declared_metrics(tmp_path):
    root = _write_domain_profile(tmp_path)
    profile = load_domain_profile(root)

    with pytest.raises(KeyError, match="citation_accuracy"):
        profile.purity_from_metrics({"evidence_coverage": 0.9})
