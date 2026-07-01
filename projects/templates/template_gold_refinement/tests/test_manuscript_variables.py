"""Tests for src.manuscript_variables — manuscript token generation.

Includes a live cross-reference test that reads the actual manuscript files
and asserts every {{TOKEN}} they contain is produced by generate_variables().
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from manuscript_variables import generate_variables, save_variables

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})
_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def _make_minimal_project(tmp_path: Path) -> Path:
    """Build a minimal project tree to exercise generate_variables()."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        yaml.dump(
            {
                "paper": {"title": "Test Paper", "version": "1.0"},
                "authors": [{"name": "Alice"}],
                "keywords": ["gold refining", "assaying"],
                "gold_refinement": {
                    "seed": 431,
                    "composition_depth": "deep",
                    "lexicon": {
                        "metallurgical_terms": ["cupellation", "assaying", "smelting"],
                        "manuscript_terms": ["draft", "claim", "citation"],
                        "purity_adjectives": ["unrefined", "purified", "certified"],
                        "refinement_verbs": ["assaying", "certifying", "refining"],
                    },
                    "slots": [
                        {
                            "name": "METHOD_METAL_TERM",
                            "category": "metallurgical_terms",
                            "count": 2,
                            "section": "methodology",
                        },
                        {
                            "name": "RESULTS_PURITY_ADJ",
                            "category": "purity_adjectives",
                            "count": 1,
                            "section": "results",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


# --------------------------------------------------------------------------- #
# generate_variables — structure and key coverage
# --------------------------------------------------------------------------- #


def test_all_keys_uppercase(tmp_path):
    root = _make_minimal_project(tmp_path)
    variables = generate_variables(root)
    assert isinstance(variables, dict)
    assert all(isinstance(k, str) and k == k.upper() for k in variables), "All keys must be UPPERCASE_SNAKE"


def test_refinery_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "REFINERY_NUM_STAGES" in v
    assert "REFINERY_FINAL_PURITY" in v
    assert "REFINERY_FINAL_KARAT" in v
    assert "REFINERY_IS_CERTIFIED" in v
    assert v["REFINERY_NUM_STAGES"] == "5"
    assert "nine-nines" in v["REFINERY_FINAL_KARAT"]
    assert v["REFINERY_IS_CERTIFIED"] == "Yes"


def test_stage_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    for i in range(1, 6):
        prefix = f"STAGE_{i}"
        assert f"{prefix}_NAME" in v
        assert f"{prefix}_OUTPUT_PURITY" in v
        assert f"{prefix}_KARAT" in v


def test_token_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "TOKEN_COUNT" in v
    assert "TOKEN_SEED" in v
    assert v["TOKEN_SEED"] == "431"
    # Individual token variables
    assert "METHOD_METAL_TERM_1" in v
    assert "METHOD_METAL_TERM_2" in v
    assert "RESULTS_PURITY_ADJ" in v  # count=1, so no _1 suffix


def test_config_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "CONFIG_VERSION" in v
    assert "CONFIG_SEED" in v
    assert "CONFIG_NUM_LEXICON_CATEGORIES" in v
    assert "CONFIG_NUM_SLOTS" in v
    assert "CONFIG_FIRST_AUTHOR" in v
    assert v["CONFIG_FIRST_AUTHOR"] == "Alice"
    assert "gold refining" in v["CONFIG_KEYWORDS"]


def test_artifact_counts(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "ARTIFACT_FIGURES" in v
    assert "ARTIFACT_DATA_FILES" in v
    assert "ARTIFACT_REPORTS" in v
    assert "ARTIFACT_TOTAL" in v


def test_provenance_variables(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "CONFIG_HASH" in v
    assert len(v["CONFIG_HASH"]) == 16
    assert "GENERATION_TIMESTAMP" in v
    assert "PYTHON_VERSION" in v


def test_table_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "STAGE_TABLE_ROWS" in v
    assert "TOKEN_CATEGORY_TABLE" in v
    assert "TOKEN_SECTION_TABLE" in v
    assert "TOKEN_PROVENANCE_TABLE" in v
    assert "LEXICON_TABLE" in v
    assert "PURITY_SEQUENCE" in v
    assert "FORMALISM_TABLE_ROWS" in v
    assert "FORMALISM_EQUATION_BLOCKS" in v
    assert "FORMALISM_TRACEABILITY_TABLE" in v
    assert "INTEGRITY_DIMENSION_TABLE" in v
    assert "INTEGRITY_OWNER_TABLE" in v
    assert "EVIDENCE_TIER_TABLE" in v
    assert "SECURITY_ASSAY_TABLE" in v
    assert "FIGURE_QUALITY_TABLE" in v


def test_title_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert "TITLE_ABSTRACT" in v
    assert "TITLE_INTRODUCTION" in v
    assert "TITLE_METHODOLOGY" in v


def test_real_project_expanded_token_surface():
    project_root = Path(__file__).resolve().parent.parent
    v = generate_variables(project_root)
    assert v["TOKEN_COUNT"] == "24"
    assert v["CONFIG_TOTAL_TOKEN_COUNT"] == "24"
    for token in (
        "INTRO_INTEGRITY_TERM_1",
        "METHOD_GATE_TERM_3",
        "RESULTS_EVIDENCE_TERM_3",
        "DISCUSSION_BOUNDARY_TERM_2",
        "REPRO_EVIDENCE_TERM_2",
        "EVALUATION_GATE_TERM_2",
        "AUTHORING_BOUNDARY_TERM_2",
    ):
        assert token in v


def test_formalism_and_claim_support_variables_present(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    assert v["FORMALISM_COUNT"] == "7"
    assert "eq:certification_predicate" in v["FORMALISM_EQUATION_LABELS"]
    assert "eq:adversarial_assay" in v["FORMALISM_EQUATION_LABELS"]
    assert v["CLAIM_SUPPORT_REGISTRY_PATH"] == "output/reports/claim_support_registry.json"
    assert v["FIGURE_QUALITY_REPORT_PATH"] == "output/reports/figure_quality_report.json"
    assert "FIGURE_QUALITY_STATUS" in v
    assert "FIGURE_QUALITY_PASSING_COUNT" in v
    assert "SHARED_EVIDENCE_KIND_TABLE" in v
    assert "fig:implementation_circuit" in v["FIGURE_IMPLEMENTATION_CIRCUIT"]
    assert "fig:claim_evidence_assay" in v["FIGURE_CLAIM_EVIDENCE_ASSAY"]
    assert "fig:integrity_risk_matrix" in v["FIGURE_INTEGRITY_RISK_MATRIX"]
    assert "fig:evidence_tier_ladder" in v["FIGURE_EVIDENCE_TIER_LADDER"]
    assert v["INTEGRITY_DIMENSION_COUNT"] == "9"
    assert "highest residual risk" in v["INTEGRITY_RISK_SUMMARY"]


def test_real_project_security_assay_variables_present():
    project_root = Path(__file__).resolve().parent.parent
    v = generate_variables(project_root)
    assert v["SECURITY_ASSAY_COUNT"] == "5"
    assert "5 adversarial assay rows" in v["SECURITY_ASSAY_SUMMARY"]
    assert "NIST SP 800-207" in v["SECURITY_ASSAY_TABLE"]
    assert "MITRE ATT&CK" in v["SECURITY_ASSAY_TABLE"]
    assert "Codex Security" in v["SECURITY_ASSAY_TABLE"]
    assert "No Codex Security or Deep Security Scan findings are claimed" in v["SECURITY_ASSAY_BOUNDARY"]


def test_figure_quality_variables_read_generated_report(tmp_path):
    root = _make_minimal_project(tmp_path)
    reports_dir = root / "output" / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "figure_quality_report.json").write_text(
        json.dumps(
            {
                "schema": "template-gold-refinement-figure-quality-v1",
                "figure_count": 1,
                "png_count": 1,
                "svg_count": 1,
                "passing_count": 1,
                "registry_parity": True,
                "records": [
                    {
                        "name": "purity_progression",
                        "png_exists": True,
                        "svg_exists": True,
                        "width_px": 1800,
                        "height_px": 1200,
                        "nonwhite_fraction": 0.123456,
                        "color_variance": 0.01234567,
                        "passes_quality": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    v = generate_variables(root)
    assert v["FIGURE_QUALITY_STATUS"] == "passing"
    assert v["FIGURE_QUALITY_TOTAL"] == "1"
    assert v["FIGURE_QUALITY_PNG_COUNT"] == "1"
    assert v["FIGURE_QUALITY_SVG_COUNT"] == "1"
    assert v["FIGURE_QUALITY_REGISTRY_PARITY"] == "Yes"
    assert "| purity_progression | yes | yes | 1800x1200 | 0.123 | 0.01234567 | pass |" in v["FIGURE_QUALITY_TABLE"]


def test_config_hash_na_when_no_config(tmp_path):
    """When no config.yaml exists, CONFIG_HASH should be 'N/A'."""
    v = generate_variables(tmp_path)
    assert v["CONFIG_HASH"] == "N/A"


def test_require_analysis_outputs_raises(tmp_path):
    root = _make_minimal_project(tmp_path)
    with pytest.raises(FileNotFoundError, match="refinery_results"):
        generate_variables(root, require_analysis_outputs=True)


def test_require_analysis_outputs_passes_with_data(tmp_path):
    root = _make_minimal_project(tmp_path)
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "refinery_results.json").write_text("{}", encoding="utf-8")
    variables = generate_variables(root, require_analysis_outputs=True)
    assert variables["REFINERY_NUM_STAGES"] == "5"


# --------------------------------------------------------------------------- #
# save_variables
# --------------------------------------------------------------------------- #


def test_save_variables_round_trip(tmp_path):
    root = _make_minimal_project(tmp_path)
    variables = generate_variables(root)
    out = tmp_path / "vars.json"
    save_variables(variables, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["REFINERY_NUM_STAGES"] == "5"
    assert loaded["CONFIG_FIRST_AUTHOR"] == "Alice"


def test_save_variables_creates_parent_dir(tmp_path):
    root = _make_minimal_project(tmp_path)
    v = generate_variables(root)
    deep = tmp_path / "a" / "b" / "c" / "vars.json"
    save_variables(v, deep)
    assert deep.exists()


# --------------------------------------------------------------------------- #
# Live cross-reference: every {{TOKEN}} in the actual manuscript must be
# produced by generate_variables()
# --------------------------------------------------------------------------- #


def test_all_manuscript_tokens_are_generated(tmp_path):
    """Regression guard: every {{TOKEN}} used in manuscript/*.md must be
    produced by generate_variables() so no placeholder can appear in a
    rendered PDF.

    Uses the real project config (not the minimal tmp_path project) because
    the manuscript references tokens from the full config's slots.
    """
    project_root = Path(__file__).resolve().parent.parent
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        pytest.skip("manuscript/ directory not found; skipping cross-reference check")

    # Use the real project root so all configured slots are present
    produced = set(generate_variables(project_root))

    unresolved: dict[str, list[str]] = {}
    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in _DOC_ONLY:
            continue
        text = md_file.read_text(encoding="utf-8")
        for token in _TOKEN_RE.findall(text):
            if token not in produced:
                unresolved.setdefault(token, []).append(md_file.name)

    assert not unresolved, "Manuscript tokens not produced by generate_variables():\n" + "\n".join(
        f"  {{{{{t}}}}}: {files}" for t, files in sorted(unresolved.items())
    )
