"""Tests for manuscript variable hydration."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from src.manuscript_variables import (
    compute_variables,
    compute_variables_and_provenance,
    compute_variables_from_payload,
)
from src.models import AutoResearchLoopResult
from src.source_ledger import load_source_ledger


def _candidate_display_label(value: object) -> str:
    text = str(value)
    if text == "nearest_centroid_baseline":
        return "baseline"
    return text.removeprefix("exp-").replace("-", " ")


SURVEY_CITEKEYS = {
    "baulin_discovery_engine_2025",
    "hao_ai_tools_focus_2026",
    "asai_openscholar_2026",
    "skarlinski_paperqa2_2024",
    "futurehouse_platform_2025",
    "lu_ai_scientist_nature_2026",
    "yamada_ai_scientist_v2_2025",
    "ghareeb_robin_2026",
    "kong_ai_auto_research_2026",
    "hasib_exhyte_2025",
    "wei_agentic_science_2025",
    "gridach_agentic_science_2025",
    "hubert_alphaproof_2025",
    "lu_process_driven_autoformalization_2024",
    "apollo_lean_collaboration_2025",
    "romera_paredes_alphaevolve_2025",
    "deepevolve_2025",
    "active_inference_science_2025",
    "graphrag_bench_2026",
    "brink_kg_rag_2026",
    "heddes_hdc_2024",
    "balazevic_tucker_2019",
    "yusupov_mixed_geometry_2025",
}

SECURITY_CITEKEYS = {
    "nist_sp800_207_zero_trust",
    "nist_sp800_218_ssdf",
    "slsa_spec_latest",
    "mitre_attack_t1195",
}


def test_manuscript_variables_cover_all_source_tokens(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    variables = compute_variables(project_root)
    tokens = set()
    for path in (project_root / "manuscript").glob("[0-9][0-9]_*.md"):
        tokens.update(re.findall(r"\{\{([A-Z0-9_]+)\}\}", path.read_text(encoding="utf-8")))

    assert tokens
    assert tokens <= set(variables)
    assert variables["READINESS_STATUS"] == "passed"
    assert variables["ACCEPTED_CANDIDATE_ID"] == "exp-mlp-tanh-64"
    assert variables["ACCEPTED_MODEL_TYPE"] == "mlp"
    assert variables["BASELINE_ACCURACY"].endswith("%")
    assert variables["BEST_ACCURACY"].endswith("%")
    assert variables["TRANSFORMER_EVALUATED"] == "true"
    assert variables["FIGURE_BLOCK_CANDIDATE_SCORES"].startswith("![")
    assert "fig:ml_candidate_scores" in variables["FIGURE_BLOCK_CANDIDATE_SCORES"]
    assert "fig:ml_per_class_accuracy" in variables["FIGURE_BLOCK_PER_CLASS_ACCURACY"]
    assert "fig:ml_learning_curves" in variables["FIGURE_BLOCK_LEARNING_CURVES"]
    assert "fig:ml_complexity_accuracy" in variables["FIGURE_BLOCK_COMPLEXITY_ACCURACY"]
    assert "fig:mnist_error_examples" in variables["FIGURE_BLOCK_ERROR_EXAMPLES"]
    assert "fig:ml_calibration_reliability" in variables["FIGURE_BLOCK_CALIBRATION_RELIABILITY"]
    assert "fig:ml_classification_metrics_heatmap" in variables["FIGURE_BLOCK_CLASSIFICATION_METRICS"]
    assert "fig:ml_confusion_pairs" in variables["FIGURE_BLOCK_CONFUSION_PAIRS"]
    assert "fig:ml_generalization_gap" in variables["FIGURE_BLOCK_GENERALIZATION_GAP"]
    assert "fig:ml_robustness_matrix" in variables["FIGURE_BLOCK_ROBUSTNESS_MATRIX"]
    assert "fig:ml_probability_margin_distribution" in variables["FIGURE_BLOCK_PROBABILITY_MARGIN"]
    assert "fig:ml_bootstrap_intervals" in variables["FIGURE_BLOCK_BOOTSTRAP_INTERVALS"]
    assert "fig:ml_paired_correctness" in variables["FIGURE_BLOCK_PAIRED_CORRECTNESS"]
    assert "fig:ml_selective_accuracy" in variables["FIGURE_BLOCK_SELECTIVE_ACCURACY"]
    assert "fig:ml_probability_quality" in variables["FIGURE_BLOCK_PROBABILITY_QUALITY"]
    assert "fig:ml_training_dynamics" in variables["FIGURE_BLOCK_TRAINING_DYNAMICS"]
    assert "fig:autoresearch_candidate_lifecycle" in variables["FIGURE_BLOCK_CANDIDATE_LIFECYCLE"]
    assert "fig:mnist_class_balance" in variables["FIGURE_BLOCK_DATASET_CLASS_BALANCE"]
    assert "fig:mnist_subset_contact_sheet" in variables["FIGURE_BLOCK_DATASET_CONTACT_SHEET"]
    assert "fig:autoresearch_security_control_matrix" in variables["FIGURE_BLOCK_SECURITY_CONTROL_MATRIX"]
    assert "fig:autoresearch_integrity_chain" in variables["FIGURE_BLOCK_INTEGRITY_CHAIN"]
    assert variables["TRAIN_PER_CLASS_COUNT"] == "200"
    assert variables["TEST_PER_CLASS_COUNT"] == "50"
    assert variables["ACCEPTED_MACRO_F1"].endswith("%")
    assert "to" in variables["ACCEPTED_ACCURACY_INTERVAL"]
    assert variables["ACCEPTED_CALIBRATION_ECE"].endswith("%")
    assert variables["ROBUSTNESS_MIN_ACCURACY"].endswith("%")
    assert "to" in variables["BOOTSTRAP_ACCURACY_INTERVAL"]
    assert "to" in variables["BOOTSTRAP_MACRO_F1_INTERVAL"]
    assert variables["PAIRED_NET_GAIN"].endswith("%")
    assert 0.0 <= float(variables["MCNEMAR_P_VALUE"]) <= 1.0
    assert variables["MEAN_CORRECT_CONFIDENCE"].endswith("%")
    assert variables["MEAN_ERROR_CONFIDENCE"].endswith("%")
    assert variables["LOW_MARGIN_COUNT"].isdigit()
    assert float(variables["ACCEPTED_BRIER_SCORE"]) >= 0.0
    assert float(variables["ACCEPTED_NEGATIVE_LOG_LIKELIHOOD"]) >= 0.0
    assert variables["ACCEPTED_TOP2_ACCURACY"].endswith("%")
    assert -1.0 <= float(variables["ACCEPTED_COHEN_KAPPA"]) <= 1.0
    assert variables["SELECTIVE_HIGH_CONFIDENCE_COVERAGE"].endswith("%")
    assert variables["SELECTIVE_HIGH_CONFIDENCE_ACCURACY"].endswith("%")
    assert variables["LEARNING_RATE_DECAY"] == "0.995"
    assert variables["GRADIENT_CLIP_NORM"] == "5"
    assert variables["ACCEPTED_BEST_EPOCH"].isdigit()
    assert float(variables["ACCEPTED_FINAL_LEARNING_RATE"]) >= 0.0
    assert float(variables["ACCEPTED_LOSS_REDUCTION"]) >= 0.0
    assert variables["ACCEPTED_TRAIN_TEST_GAP"].endswith("%")
    assert variables["ML_CANDIDATE_LEDGER_TABLE"].startswith("| Candidate |")
    assert variables["CLASSIFICATION_DIAGNOSTICS_TABLE"].startswith("| Class |")
    assert variables["CANDIDATE_INTERVAL_TABLE"].startswith("| Candidate |")
    assert variables["CLASS_BALANCE_TABLE"].startswith("| Split |")
    assert variables["CALIBRATION_BIN_TABLE"].startswith("| Confidence bin |")
    assert variables["CONFUSION_PAIR_TABLE"].startswith("| Pair |")
    assert variables["ROBUSTNESS_SCORE_TABLE"].startswith("| Candidate |")
    assert variables["PROBABILITY_DIAGNOSTICS_TABLE"].startswith("| Statistic |")
    assert variables["BOOTSTRAP_INTERVAL_TABLE"].startswith("| Metric |")
    assert variables["PAIRED_COMPARISON_TABLE"].startswith("| Matched comparison statistic |")
    assert variables["STATISTICAL_SUMMARY_TABLE"].startswith("| Statistic |")
    assert variables["SELECTIVE_ACCURACY_TABLE"].startswith("| Confidence threshold |")
    assert variables["PROBABILITY_QUALITY_TABLE"].startswith("| Candidate |")
    assert variables["TRAINING_DIAGNOSTICS_TABLE"].startswith("| Candidate |")
    assert variables["CANDIDATE_SELECTION_AUDIT_TABLE"].startswith("| Rank |")
    assert variables["DIAGNOSTIC_BOUNDARY_TABLE"].startswith("\\begingroup\\footnotesize")
    assert variables["SECURITY_ARTIFACT_TABLE"].startswith("| Security artifact |")
    assert variables["SECURITY_THREAT_MODEL_TABLE"].startswith("\\begingroup\\footnotesize")
    assert variables["SECURITY_INTEGRITY_TABLE"].startswith("| Integrity field |")
    assert variables["SECURITY_PROFILE_MODE"] == "local_deterministic"
    assert variables["SECURITY_NETWORK_POLICY"] == "default_offline"
    assert variables["SECURITY_INTEGRITY_ALGORITHM"] == "sha256"
    assert variables["SECURITY_EXTERNAL_SIGNING"] == "false"
    assert variables["SECURITY_ATTESTATION_STATUS"] == "passed"
    assert variables["SECURITY_ATTESTATION_MISSING_COUNT"] == "0"
    assert variables["SECURITY_ATTESTATION_MISMATCH_COUNT"] == "0"
    assert variables["FIGURE_METHOD_TABLE"].startswith("\\begingroup\\footnotesize")
    assert "| Figure | Source | Method | Scope |" in variables["FIGURE_METHOD_TABLE"]
    assert "@fig:ml_candidate_scores" in variables["FIGURE_METHOD_TABLE"]
    assert "[candidate intervals](../data/ml_candidate_intervals.json)" in variables["FIGURE_METHOD_TABLE"]
    assert variables["AUTORESEARCH_ARTIFACT_TABLE"].startswith("| Artifact |")
    assert variables["REVIEW_GATE_TABLE"].startswith("| Gate |")
    assert variables["BENCHMARK_SCORE_TABLE"].startswith("| Benchmark task |")
    assert variables["VARIABLE_PROVENANCE_TABLE"].startswith("| Source artifact |")


def test_variable_script_writes_resolved_manuscript(project_root: Path) -> None:
    script = project_root / "scripts" / "z_generate_manuscript_variables.py"
    result = subprocess.run([sys.executable, str(script)], cwd=project_root, text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    resolved = project_root / "output" / "manuscript" / "00_abstract.md"
    assert resolved.exists()
    assert "{{" not in resolved.read_text(encoding="utf-8")
    assert (project_root / "output" / "data" / "manuscript_variable_provenance.json").exists()
    assert (project_root / "output" / "data" / "manuscript_figure_blocks.json").exists()
    manifest = json.loads((project_root / "output" / "reports" / "artifact_manifest.json").read_text())
    variables_path = project_root / "output" / "data" / "manuscript_variables.json"
    variables_entry = next(row for row in manifest["entries"] if row["path"] == "output/data/manuscript_variables.json")
    assert variables_entry["sha256"] == hashlib.sha256(variables_path.read_bytes()).hexdigest()


def test_compute_variables_refuses_invalid_readiness(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
    tmp_path: Path,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    project = tmp_path / "template_autoresearch_project"
    shutil.copytree(
        project_root,
        project,
        ignore=shutil.ignore_patterns(".pytest_cache", "__pycache__"),
    )
    payload_path = project / "output" / "data" / "autoresearch_loop.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["metrics"]["readiness_valid"] = False
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="valid final readiness"):
        compute_variables(project)


def test_generated_figure_blocks_match_registry(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    variables, provenance = compute_variables_and_provenance(project_root)
    registry = json.loads((project_root / "output" / "figures" / "figure_registry.json").read_text(encoding="utf-8"))

    for token, label in {
        "FIGURE_BLOCK_STAGE_MATRIX": "fig:autoresearch_stage_matrix",
        "FIGURE_BLOCK_CANDIDATE_SCORES": "fig:ml_candidate_scores",
        "FIGURE_BLOCK_CONFUSION_MATRIX": "fig:ml_confusion_matrix",
        "FIGURE_BLOCK_PER_CLASS_ACCURACY": "fig:ml_per_class_accuracy",
        "FIGURE_BLOCK_LEARNING_CURVES": "fig:ml_learning_curves",
        "FIGURE_BLOCK_COMPLEXITY_ACCURACY": "fig:ml_complexity_accuracy",
        "FIGURE_BLOCK_ERROR_EXAMPLES": "fig:mnist_error_examples",
        "FIGURE_BLOCK_CALIBRATION_RELIABILITY": "fig:ml_calibration_reliability",
        "FIGURE_BLOCK_CLASSIFICATION_METRICS": "fig:ml_classification_metrics_heatmap",
        "FIGURE_BLOCK_CONFUSION_PAIRS": "fig:ml_confusion_pairs",
        "FIGURE_BLOCK_GENERALIZATION_GAP": "fig:ml_generalization_gap",
        "FIGURE_BLOCK_ROBUSTNESS_MATRIX": "fig:ml_robustness_matrix",
        "FIGURE_BLOCK_PROBABILITY_MARGIN": "fig:ml_probability_margin_distribution",
        "FIGURE_BLOCK_BOOTSTRAP_INTERVALS": "fig:ml_bootstrap_intervals",
        "FIGURE_BLOCK_PAIRED_CORRECTNESS": "fig:ml_paired_correctness",
        "FIGURE_BLOCK_SELECTIVE_ACCURACY": "fig:ml_selective_accuracy",
        "FIGURE_BLOCK_PROBABILITY_QUALITY": "fig:ml_probability_quality",
        "FIGURE_BLOCK_TRAINING_DYNAMICS": "fig:ml_training_dynamics",
        "FIGURE_BLOCK_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
        "FIGURE_BLOCK_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
        "FIGURE_BLOCK_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
        "FIGURE_BLOCK_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
        "FIGURE_BLOCK_SECURITY_CONTROL_MATRIX": "fig:autoresearch_security_control_matrix",
        "FIGURE_BLOCK_INTEGRITY_CHAIN": "fig:autoresearch_integrity_chain",
    }.items():
        block = variables[token]
        record = registry[label]
        assert record["caption"] in block
        assert f"#${label}" not in block
        assert f"#{label}" in block
        assert (project_root / "output" / "figures" / record["filename"]).exists()
        assert provenance["variables"][token]["source"] == "output/figures/figure_registry.json"


def test_generated_tables_are_backed_by_ledgers(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    variables = compute_variables(project_root)
    candidate_ledger = json.loads((project_root / "output" / "data" / "ml_candidate_ledger.json").read_text())
    review_decisions = json.loads((project_root / "output" / "data" / "review_decisions.json").read_text())
    benchmark_scores = json.loads((project_root / "output" / "data" / "benchmark_scores.json").read_text())
    diagnostics = json.loads((project_root / "output" / "data" / "ml_classification_diagnostics.json").read_text())
    calibration = json.loads((project_root / "output" / "data" / "ml_calibration_report.json").read_text())
    candidate_intervals = json.loads((project_root / "output" / "data" / "ml_candidate_intervals.json").read_text())
    class_balance = json.loads((project_root / "output" / "data" / "ml_class_balance.json").read_text())
    robustness = json.loads((project_root / "output" / "data" / "ml_robustness_report.json").read_text())
    probability = json.loads((project_root / "output" / "data" / "ml_probability_diagnostics.json").read_text())
    bootstrap = json.loads((project_root / "output" / "data" / "ml_bootstrap_intervals.json").read_text())
    paired = json.loads((project_root / "output" / "data" / "ml_paired_comparison.json").read_text())
    statistical = json.loads((project_root / "output" / "data" / "ml_statistical_summary.json").read_text())
    training = json.loads((project_root / "output" / "data" / "ml_training_diagnostics.json").read_text())
    selection = json.loads((project_root / "output" / "data" / "ml_candidate_selection_audit.json").read_text())
    boundary = json.loads((project_root / "output" / "data" / "ml_diagnostic_boundary.json").read_text())
    threat_model = json.loads((project_root / "output" / "data" / "autoresearch_threat_model.json").read_text())
    attestation = json.loads((project_root / "output" / "data" / "autoresearch_integrity_attestation.json").read_text())
    registry = json.loads((project_root / "output" / "figures" / "figure_registry.json").read_text())

    assert _candidate_display_label(candidate_ledger["accepted_candidate_id"]) in variables["ML_CANDIDATE_LEDGER_TABLE"]
    assert all(row["gate"] in variables["REVIEW_GATE_TABLE"] for row in review_decisions["decisions"])
    assert all(row["id"] in variables["BENCHMARK_SCORE_TABLE"] for row in benchmark_scores["tasks"])
    assert all(
        str(row["class_label"]) in variables["CLASSIFICATION_DIAGNOSTICS_TABLE"] for row in diagnostics["per_class"]
    )
    assert all(str(row["count"]) in variables["CALIBRATION_BIN_TABLE"] for row in calibration["bins"])
    assert all(str(row["successes"]) in variables["CANDIDATE_INTERVAL_TABLE"] for row in candidate_intervals["rows"])
    assert all(str(row["count"]) in variables["CLASS_BALANCE_TABLE"] for row in class_balance["rows"])
    assert all(
        _candidate_display_label(row["candidate_id"]) in variables["ROBUSTNESS_SCORE_TABLE"]
        for row in robustness["rows"]
    )
    compact_candidate_tables = (
        variables["ML_CANDIDATE_LEDGER_TABLE"],
        variables["CANDIDATE_INTERVAL_TABLE"],
        variables["ROBUSTNESS_SCORE_TABLE"],
        variables["PROBABILITY_QUALITY_TABLE"],
        variables["TRAINING_DIAGNOSTICS_TABLE"],
    )
    assert all("nearest_centroid_baseline" not in table for table in compact_candidate_tables)
    assert all("mlp tanh 64" in table for table in compact_candidate_tables)
    assert str(probability["low_margin_count"]) in variables["PROBABILITY_DIAGNOSTICS_TABLE"]
    assert all(
        str(row["metric"]).replace("macro_f1", "macro F1").replace("_", " ") in variables["BOOTSTRAP_INTERVAL_TABLE"]
        for row in bootstrap["intervals"]
    )
    assert str(paired["discordant_count"]) in variables["PAIRED_COMPARISON_TABLE"]
    assert (
        _candidate_display_label(statistical["candidate_probability_quality"][0]["candidate_id"])
        in variables["PROBABILITY_QUALITY_TABLE"]
    )
    assert all(
        str(row["retained_count"]) in variables["SELECTIVE_ACCURACY_TABLE"] for row in statistical["coverage_curve"]
    )
    assert str(training["accepted"]["best_epoch"]) in variables["TRAINING_DIAGNOSTICS_TABLE"]
    assert all(
        _candidate_display_label(row["candidate_id"]) in variables["CANDIDATE_SELECTION_AUDIT_TABLE"]
        for row in selection["rows"]
    )
    assert all(row["surface"].replace("_", " ") in variables["DIAGNOSTIC_BOUNDARY_TABLE"] for row in boundary["rows"])
    assert all(row["stride_category"] in variables["SECURITY_THREAT_MODEL_TABLE"] for row in threat_model["threats"])
    assert str(attestation["checked_count"]) in variables["SECURITY_INTEGRITY_TABLE"]
    assert all(f"@{label}" in variables["FIGURE_METHOD_TABLE"] for label in registry)
    assert all(
        len(cell) <= 120
        for row in variables["FIGURE_METHOD_TABLE"].splitlines()
        if row.startswith("|")
        for cell in row.split("|")
    )


def test_new_scholarship_citekeys_are_present_and_referenced(project_root: Path) -> None:
    references = (project_root / "manuscript" / "references.bib").read_text(encoding="utf-8")
    manuscript = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((project_root / "manuscript").glob("[0-9][0-9]_*.md"))
    )
    for citekey in {
        "wilkinson2016fair",
        "soiland_reyes2022rocrate",
        "soiland_reyes2024workflow_run_rocrate",
        "gebru2021datasheets",
        "mitchell2019model_cards",
        "guo2017calibration",
        "dietterich1998statistical_tests",
        "wilson1927probable_inference",
        "efron1993bootstrap",
        "brier1950verification",
        "cohen1960coefficient",
        *SURVEY_CITEKEYS,
        *SECURITY_CITEKEYS,
    }:
        assert f"{{{citekey}," in references
        assert f"@{citekey}" in manuscript


def test_survey_source_ledger_covers_current_trend_citations(project_root: Path) -> None:
    references = (project_root / "manuscript" / "references.bib").read_text(encoding="utf-8")
    manuscript = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((project_root / "manuscript").glob("[0-9][0-9]_*.md"))
    )
    entries = load_source_ledger(project_root / "manuscript" / "source_ledger.yaml")
    by_key = {entry.citekey: entry for entry in entries}
    assert set(by_key) == SURVEY_CITEKEYS
    for citekey in SURVEY_CITEKEYS:
        row = by_key[citekey]
        assert f"{{{citekey}," in references
        assert row.canonical_url in references
        assert f"@{citekey}" in manuscript


def test_compute_variables_handles_malformed_payload_sections() -> None:
    variables = compute_variables_from_payload(
        {
            "config": [],
            "metrics": [],
            "stage_results": [{"name": "plan"}],
            "claims": [{"identifier": "rq1"}],
        }
    )

    assert variables["AUTORESEARCH_TOPIC"] == "Deterministic AutoResearch"
    assert variables["LOOP_STAGE_COUNT"] == "1"
    assert variables["SUPPORTED_CLAIM_COUNT"] == "1"
    assert variables["READINESS_STATUS"] == "requires review"
    assert variables["ACCEPTED_CANDIDATE_ID"] == "N/A"
