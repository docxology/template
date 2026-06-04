"""Tests for verified evidence registry validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.validation.evidence_registry import (
    EVIDENCE_REGISTRY_REPORT_SCHEMA,
    EvidenceFact,
    VerifiedEvidenceRegistry,
    build_project_evidence_registry,
    unsupported_citation_tokens,
    unsupported_number_tokens,
    validate_text_against_registry,
    write_evidence_registry_report,
)


def test_registry_validates_supported_numbers_and_citations() -> None:
    registry = VerifiedEvidenceRegistry()
    registry.add(EvidenceFact(kind="number", value="42", source="metrics.json:answer"))
    registry.add(EvidenceFact(kind="citation", value="smith2026", source="references.bib"))

    report = validate_text_against_registry(
        "The result is 42 units and follows @smith2026.",
        registry,
    )

    assert unsupported_number_tokens(report) == []
    assert unsupported_citation_tokens(report) == []


def test_registry_flags_unsupported_numbers_and_citations() -> None:
    registry = VerifiedEvidenceRegistry()
    registry.add(EvidenceFact(kind="number", value="42", source="metrics.json:answer"))
    registry.add(EvidenceFact(kind="citation", value="smith2026", source="references.bib"))

    report = validate_text_against_registry(
        "The result is 43 units and follows @doe2026.",
        registry,
    )

    assert unsupported_number_tokens(report) == ["43"]
    assert unsupported_citation_tokens(report) == ["doe2026"]


def test_build_project_registry_collects_variables_bibtex_figures_and_data(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "output" / "data").mkdir(parents=True)
    (project / "manuscript" / "sections").mkdir(parents=True)
    (project / "data").mkdir()
    (project / "output" / "figures").mkdir(parents=True)

    (project / "output" / "data" / "manuscript_variables.json").write_text(
        '{"SAMPLE_SIZE": 128, "ERROR_RATE": 0.125}',
        encoding="utf-8",
    )
    (project / "output" / "data" / "results.csv").write_text(
        'name,iterations\nsmall,"2,000"\n',
        encoding="utf-8",
    )
    (project / "manuscript" / "references.bib").write_text(
        "@article{smith2026,title={A}}\n",
        encoding="utf-8",
    )
    (project / "manuscript" / "sections" / "01.md").write_text(
        "![Figure](../figures/plot.png){#fig:plot}\n\nTable: Values {#tbl:values}\n",
        encoding="utf-8",
    )
    (project / "data" / "claims.json").write_text(
        '[{"claim_id": "c1", "value": 128}]',
        encoding="utf-8",
    )
    (project / "figures.yaml").write_text(
        """
section_figures:
  methods_sheaf:
    - id: sheaf_layers_overview
      number: 6
""",
        encoding="utf-8",
    )
    sheaf_config = project / "manuscript" / "sheaf"
    sheaf_config.mkdir(parents=True)
    (sheaf_config / "tracks.yaml").write_text(
        """
tracks:
  simulation:
    order: 30
""",
        encoding="utf-8",
    )
    (project / "output" / "figures" / "plot.png").write_bytes(b"png")

    registry = build_project_evidence_registry(project)

    assert registry.has("number", "128")
    assert registry.has("number", "0.125")
    assert registry.has("number", "2000")
    assert registry.has("number", "2,000")
    assert registry.has("citation", "smith2026")
    assert registry.has("figure", "fig:plot")
    assert registry.has("table", "tbl:values")
    assert registry.has("artifact", "output/figures/plot.png")
    assert registry.has("number", "6")
    assert registry.has("number", "30")
    assert {fact.source_tier for fact in registry.lookup("number", "6")} == {"configuration"}
    assert {fact.source_path for fact in registry.lookup("number", "30")} == {"manuscript/sheaf/tracks.yaml"}

    report = validate_text_against_registry(
        "The generated table reports 2,000 iterations. Figure 6 lists track order 30.",
        registry,
    )
    assert unsupported_number_tokens(report) == []


def test_registry_validates_internal_section_and_equation_references(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01.md").write_text(
        "# Methods {#sec:methods}\n\n"
        "The update is defined below:\n\n"
        "$$\n"
        "x_{k+1} = x_k - \\alpha g_k\n"
        "\\label{eq:update}\n"
        "$$\n",
        encoding="utf-8",
    )

    registry = build_project_evidence_registry(project)
    report = validate_text_against_registry("See [@sec:methods] and [@eq:update].", registry)

    assert registry.has("section", "sec:methods")
    assert registry.has("equation", "eq:update")
    assert unsupported_citation_tokens(report) == []


def test_registry_accepts_numeric_variants_and_preserves_provenance() -> None:
    registry = VerifiedEvidenceRegistry()
    registry.add(
        EvidenceFact(
            kind="number",
            value="0.125",
            source="output/data/manuscript_variables.json:$.ERROR_RATE",
            source_path="output/data/manuscript_variables.json",
            source_field="$.ERROR_RATE",
            source_tier="generated_metric",
            tolerance=0.001,
        )
    )

    report = validate_text_against_registry("The Results show 12.5% error.", registry)

    assert unsupported_number_tokens(report) == []
    fact = registry.lookup("number", "12.5")[0]
    assert fact.source_path == "output/data/manuscript_variables.json"
    assert fact.source_field == "$.ERROR_RATE"
    assert fact.source_tier == "generated_metric"


def test_strict_zones_fail_but_introduction_numbers_warn() -> None:
    registry = VerifiedEvidenceRegistry()
    text = """
# Introduction
Prior work often reports 77 cases.

# Results
The measured value was 43 units.
"""

    report = validate_text_against_registry(text, registry)

    assert [issue.value for issue in report.warnings] == ["77"]
    assert [issue.value for issue in report.errors] == ["43"]
    assert report.has_errors is True


def test_registry_ignores_inline_and_fenced_code_examples() -> None:
    registry = VerifiedEvidenceRegistry()
    text = """
# Results
Use `[@key]` to illustrate syntax; do not treat `999` as a claim.

```markdown
The result is 888 and cites [@missing].
```
"""

    report = validate_text_against_registry(text, registry)

    assert unsupported_number_tokens(report) == []
    assert unsupported_citation_tokens(report) == []


def test_write_evidence_registry_report(tmp_path: Path) -> None:
    registry = VerifiedEvidenceRegistry()
    registry.add(EvidenceFact(kind="citation", value="smith2026", source="manuscript/references.bib"))

    report_path = write_evidence_registry_report(tmp_path, registry)

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema"] == EVIDENCE_REGISTRY_REPORT_SCHEMA
    assert payload["fact_count"] == 1
    assert payload["kind_counts"] == {"citation": 1}
    assert payload["omitted_fact_count"] == 0
    assert payload["sample_facts"][0]["value"] == "smith2026"
    assert report_path == tmp_path / "reports" / "evidence_registry.json"


def test_write_evidence_registry_report_preserves_stable_fact_timestamps(tmp_path: Path) -> None:
    first = VerifiedEvidenceRegistry()
    first.add(
        EvidenceFact(
            kind="citation",
            value="smith2026",
            source="manuscript/references.bib",
            checked_at="2026-05-24T00:00:00+00:00",
        )
    )
    report_path = write_evidence_registry_report(tmp_path, first)
    first_payload = report_path.read_text(encoding="utf-8")

    second = VerifiedEvidenceRegistry()
    second.add(
        EvidenceFact(
            kind="citation",
            value="smith2026",
            source="manuscript/references.bib",
            checked_at="2026-05-24T00:01:00+00:00",
        )
    )
    write_evidence_registry_report(tmp_path, second)

    assert report_path.read_text(encoding="utf-8") == first_payload


def test_compact_registry_report_caps_samples_and_summarizes_facts() -> None:
    registry = VerifiedEvidenceRegistry(
        EvidenceFact(kind="citation", value=f"smith{i}", source="references.bib", source_tier="bibliography")
        for i in range(250)
    )
    registry.add(
        EvidenceFact(
            kind="number",
            value="88",
            source="output/data/results.json",
            source_tier="generated_metric",
            stale=True,
        )
    )

    payload = registry.to_compact_dict(sample_limit=3)

    assert payload["schema"] == EVIDENCE_REGISTRY_REPORT_SCHEMA
    assert payload["fact_count"] == 252
    assert payload["kind_counts"] == {"citation": 250, "number": 2}
    assert payload["source_tiers"] == {"bibliography": 250, "generated_metric": 2}
    assert len(payload["sample_facts"]) == 3
    assert payload["omitted_fact_count"] == 249
    assert payload["freshness_warnings"][0]["value"] == "88"


def test_full_registry_report_is_explicit_debug_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry = VerifiedEvidenceRegistry()
    registry.add(EvidenceFact(kind="citation", value="smith2026", source="manuscript/references.bib"))
    full_path = tmp_path / "reports" / "evidence_registry_full.json"

    monkeypatch.delenv("TEMPLATE_EVIDENCE_REGISTRY_FULL", raising=False)
    write_evidence_registry_report(tmp_path, registry)
    assert full_path.exists() is False

    monkeypatch.setenv("TEMPLATE_EVIDENCE_REGISTRY_FULL", "1")
    write_evidence_registry_report(tmp_path, registry)
    full_payload = json.loads(full_path.read_text(encoding="utf-8"))
    assert full_payload["facts"][0]["value"] == "smith2026"

    monkeypatch.delenv("TEMPLATE_EVIDENCE_REGISTRY_FULL", raising=False)
    write_evidence_registry_report(tmp_path, registry)
    assert full_path.exists() is False


def test_claim_ledger_ingestion_preserves_claim_metadata_and_freshness(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "data").mkdir(parents=True)
    (project / "data" / "claim_ledger.json").write_text(
        """
[
  {
    "claim_id": "c-error-rate",
    "kind": "number",
    "value": 88,
    "source": "output/data/results.json",
    "source_tier": "claim_ledger",
    "freshness": "stale",
    "artifact_path": "output/data/results.json"
  }
]
""",
        encoding="utf-8",
    )

    registry = build_project_evidence_registry(project)
    fact = registry.lookup("number", "88")[0]
    report_path = write_evidence_registry_report(project / "output", registry)
    payload = report_path.read_text(encoding="utf-8")

    assert fact.source_field == "c-error-rate"
    assert fact.source_tier == "claim_ledger"
    assert fact.stale is True
    assert '"freshness_warnings"' in payload


def test_trusted_number_tiers_rejects_self_referential_metric() -> None:
    registry = VerifiedEvidenceRegistry()
    # A strict-zone number that traces ONLY to the run's own generated output.
    registry.add(
        EvidenceFact(kind="number", value="0.873", source="output/data/ml_task.json", source_tier="generated_metric")
    )
    text = "## Results\n\nThe held-out accuracy was 0.873 on the test set.\n"
    trusted = frozenset({"bibliography", "data_source", "claim_ledger"})

    # Opt-in tier filter: a strict number tracing only to generated_metric is an error.
    strict_report = validate_text_against_registry(text, registry, trusted_number_tiers=trusted)
    assert any(issue.kind == "number" and issue.value == "0.873" for issue in strict_report.errors)

    # Default (None) preserves the historical behavior — the number is accepted.
    default_report = validate_text_against_registry(text, registry)
    assert not any(issue.value == "0.873" for issue in default_report.errors)


def test_trusted_number_tiers_accepts_external_source() -> None:
    registry = VerifiedEvidenceRegistry()
    # The same number, but tagged as coming from an input data source (external truth).
    registry.add(EvidenceFact(kind="number", value="0.873", source="data/input.json", source_tier="data_source"))
    text = "## Results\n\nThe held-out accuracy was 0.873 on the test set.\n"
    report = validate_text_against_registry(text, registry, trusted_number_tiers=frozenset({"data_source"}))
    assert not any(issue.value == "0.873" for issue in report.errors)


def test_lookup_fresh_only_filters_stale_facts() -> None:
    """fresh_only drops stale/inactive facts (AI-SPINE-V2 fail-closed primitive)."""
    registry = VerifiedEvidenceRegistry()
    registry.add(
        EvidenceFact(kind="number", value="0.5", source="ledger", source_tier="claim_ledger", stale=True)
    )
    # Default: the stale fact is still returned (report builder relies on this).
    assert registry.lookup("number", "0.5")
    assert registry.has("number", "0.5")
    # fresh_only: the stale fact no longer counts as support.
    assert registry.lookup("number", "0.5", fresh_only=True) == ()
    assert not registry.has("number", "0.5", fresh_only=True)


def test_stale_fact_fails_closed_in_strict_zone() -> None:
    """Negative control: a strict-zone number backed only by a stale fact errors."""
    registry = VerifiedEvidenceRegistry()
    registry.add(
        EvidenceFact(kind="number", value="0.873", source="ledger", source_tier="claim_ledger", stale=True)
    )
    text = "## Results\n\nThe held-out accuracy was 0.873 on the test set.\n"
    report = validate_text_against_registry(text, registry)
    assert any(issue.kind == "number" and issue.value == "0.873" for issue in report.errors)


def test_fresh_fact_supports_number_in_strict_zone() -> None:
    """Positive control: an active, non-stale fact still validates the number."""
    registry = VerifiedEvidenceRegistry()
    registry.add(EvidenceFact(kind="number", value="0.873", source="ledger", source_tier="claim_ledger"))
    text = "## Results\n\nThe held-out accuracy was 0.873 on the test set.\n"
    report = validate_text_against_registry(text, registry)
    assert not any(issue.value == "0.873" for issue in report.errors)


def test_stale_fact_tolerated_in_lenient_zone() -> None:
    """Lenient zones stay tolerant of stale facts (no new error)."""
    registry = VerifiedEvidenceRegistry()
    registry.add(
        EvidenceFact(kind="number", value="0.873", source="ledger", source_tier="claim_ledger", stale=True)
    )
    text = "Some background prose mentioning 0.873 in passing.\n"
    report = validate_text_against_registry(text, registry)
    assert not any(issue.severity == "error" and issue.value == "0.873" for issue in report.errors)
