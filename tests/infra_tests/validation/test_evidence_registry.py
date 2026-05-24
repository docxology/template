"""Tests for verified evidence registry validation."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.evidence_registry import (
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

    report = validate_text_against_registry("The generated table reports 2,000 iterations.", registry)
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

    payload = report_path.read_text(encoding="utf-8")
    assert '"smith2026"' in payload
    assert report_path == tmp_path / "reports" / "evidence_registry.json"


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
