"""Evidence and policy bindings for the self-referential manuscript."""

from __future__ import annotations

import yaml

from infrastructure.core.config.schema import ResolvedTestingConfig
from infrastructure.core.project_pyproject import project_declared_coverage_floor
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    validate_text_against_registry,
)
from template_template.metrics import build_manuscript_metrics_dict
from template_template.viz_palette import FIGURE_DPI, FONT_FLOOR

from helpers import PROJECT_DIR, REPO_ROOT


def _ledger_claims() -> dict[str, dict[str, object]]:
    payload = yaml.safe_load((PROJECT_DIR / "data" / "claim_ledger.yaml").read_text(encoding="utf-8"))
    return {str(row["claim_id"]): row for row in payload["claims"]}


def test_generated_policy_metrics_match_executable_sources() -> None:
    """Manuscript policy tokens must come from the settings the gates execute."""
    metrics = build_manuscript_metrics_dict(REPO_ROOT)
    defaults = ResolvedTestingConfig()

    assert metrics["coverage_floor_infrastructure"] == defaults.infra_coverage_threshold
    assert metrics["coverage_floor_project"] == project_declared_coverage_floor(PROJECT_DIR)
    assert metrics["figure_font_floor_pt"] == FONT_FLOOR
    assert metrics["figure_dpi"] == FIGURE_DPI


def test_policy_ledger_matches_executable_sources() -> None:
    """The human-readable claim ledger must drift with canonical constants."""
    claims = _ledger_claims()
    defaults = ResolvedTestingConfig()

    assert claims["infrastructure-coverage-floor"]["value"] == defaults.infra_coverage_threshold
    assert claims["project-coverage-floor"]["value"] == project_declared_coverage_floor(PROJECT_DIR)
    assert claims["figure-font-floor"]["value"] == FONT_FLOOR
    assert claims["figure-render-dpi"]["value"] == FIGURE_DPI


def test_claim_ledger_source_paths_exist() -> None:
    """A ledger row may not point at a missing or aspirational artifact."""
    for claim_id, row in _ledger_claims().items():
        source_path = PROJECT_DIR / str(row["artifact_path"])
        assert source_path.is_file(), f"{claim_id} source does not exist: {source_path}"


def test_source_manuscript_has_no_unsupported_evidence_tokens() -> None:
    """All source-manuscript numbers and citations need registered provenance."""
    registry = build_project_evidence_registry(PROJECT_DIR)
    failures: list[str] = []
    for path in sorted((PROJECT_DIR / "manuscript").glob("*.md")):
        report = validate_text_against_registry(path.read_text(encoding="utf-8"), registry)
        failures.extend(
            f"{path.name}:{issue.line_number}: unsupported {issue.kind} {issue.value}"
            for issue in (*report.errors, *report.warnings)
        )

    assert not failures, "\n".join(failures)


def test_evidence_gate_rejects_an_unregistered_result() -> None:
    """Negative control: the manuscript gate must fail closed on invented data."""
    registry = build_project_evidence_registry(PROJECT_DIR)
    report = validate_text_against_registry(
        "# Results\nThe unregistered benchmark took 42424242.75 seconds.\n",
        registry,
    )

    assert report.has_errors
    assert any(issue.value == "42424242.75" for issue in report.errors)
