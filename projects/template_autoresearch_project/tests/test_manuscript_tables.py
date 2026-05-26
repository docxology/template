"""Tests for generated manuscript table builders."""

from __future__ import annotations

from src.manuscript_tables import build_table_specs, variable_provenance_table


def test_build_table_specs_generates_compact_registry_and_diagnostic_tables() -> None:
    registry = {
        "fig:ml_candidate_scores": {
            "metadata": {
                "source": "output/data/ml_candidate_intervals.json",
                "method": "Wilson interval lollipop plot",
                "claim_boundary": "Fixed local test split only",
            }
        }
    }
    candidate_ledger = {
        "baseline": {
            "identifier": "nearest_centroid_baseline",
            "model_type": "nearest_centroid",
            "test_accuracy": 0.4,
            "parameter_count": 10,
        },
        "candidates": [
            {
                "identifier": "exp-mlp-tanh-64",
                "model_type": "mlp",
                "status": "accepted",
                "test_accuracy": 0.72,
                "parameter_count": 128,
            }
        ],
    }
    review_decisions = {
        "decisions": [{"gate": "human_review", "required": True, "decision": "deferred", "rationale": "review"}]
    }
    benchmark_scores = {
        "tasks": [
            {
                "id": "readiness-smoke",
                "status": "graded",
                "score": 1.0,
                "grading_output_path": "output/reports/score.json",
            }
        ]
    }
    artifact_manifest = {"entries": [{"path": "output/data/autoresearch_loop.json", "size_bytes": 123}]}
    classification = {
        "per_class": [{"class_label": 0, "precision": 0.7, "recall": 0.8, "f1": 0.75, "support": 50}],
        "top_confusion_pairs": [{"true_label": 8, "predicted_label": 3, "count": 4, "true_class_error_rate": 0.08}],
    }
    candidate_intervals = {
        "rows": [
            {
                "candidate_id": "exp-mlp-tanh-64",
                "status": "accepted",
                "successes": 36,
                "test_size": 50,
                "accuracy": 0.72,
                "ci_low": 0.58,
                "ci_high": 0.83,
            }
        ]
    }
    class_balance = {"rows": [{"split": "test", "class_label": 0, "count": 50, "fraction": 0.1}]}
    calibration = {
        "bins": [
            {
                "lower": 0.8,
                "upper": 1.0,
                "count": 12,
                "accuracy": 0.75,
                "mean_confidence": 0.9,
                "absolute_gap": 0.15,
            }
        ]
    }
    robustness = {
        "rows": [{"candidate_id": "exp-mlp-tanh-64", "transform": "identity", "accuracy": 0.72, "sample_count": 500}]
    }
    probability = {
        "mean_confidence": 0.82,
        "mean_correct_confidence": 0.88,
        "mean_error_confidence": 0.61,
        "mean_margin": 0.44,
        "mean_correct_margin": 0.51,
        "mean_error_margin": 0.18,
        "low_margin_count": 9,
    }
    bootstrap = {
        "intervals": [{"metric": "macro_f1", "observed": 0.7, "ci_low": 0.62, "ci_high": 0.76, "resample_mean": 0.69}]
    }
    paired = {
        "both_correct": 200,
        "accepted_only_correct": 75,
        "baseline_only_correct": 40,
        "both_wrong": 185,
        "discordant_count": 115,
        "exact_mcnemar_p": 0.002,
        "net_accuracy_gain": 0.07,
    }
    statistical = {
        "accuracy": 0.72,
        "balanced_accuracy": 0.71,
        "macro_f1": 0.7,
        "top2_accuracy": 0.9,
        "cohen_kappa": 0.69,
        "brier_score": 0.22,
        "negative_log_likelihood": 0.8,
        "expected_calibration_error": 0.05,
        "coverage_curve": [
            {"threshold": 0.8, "coverage": 0.4, "selective_accuracy": 0.86, "retained_count": 200, "error_count": 28}
        ],
        "candidate_probability_quality": [
            {
                "candidate_id": "exp-mlp-tanh-64",
                "accuracy": 0.72,
                "top2_accuracy": 0.9,
                "brier_score": 0.22,
                "negative_log_likelihood": 0.8,
                "mean_confidence": 0.82,
            }
        ],
    }
    training = {
        "rows": [
            {
                "candidate_id": "exp-mlp-tanh-64",
                "status": "accepted",
                "best_epoch": 12,
                "best_test_accuracy": 0.72,
                "final_test_accuracy": 0.7,
                "train_test_accuracy_gap": 0.04,
                "loss_reduction": 0.33,
                "final_learning_rate": 0.001,
            }
        ]
    }
    candidate_selection = {
        "rows": [
            {
                "rank": 1,
                "candidate_id": "exp-mlp-tanh-64",
                "status": "accepted",
                "test_accuracy": 0.72,
                "wilson_ci_low": 0.58,
                "wilson_ci_high": 0.83,
                "brier_score": 0.22,
                "negative_log_likelihood": 0.8,
                "parameter_count": 128,
            }
        ]
    }
    diagnostic_boundary = {
        "rows": [
            {
                "surface": "objective_selection",
                "source_artifact": "output/data/ml_candidate_selection_audit.json",
                "method": "rank by configured metric",
                "supports": "candidate choice",
                "does_not_support": "general MNIST performance",
            }
        ]
    }
    security_profile = {"mode": "local_deterministic", "network_policy": "default_offline"}
    security_threat_model = {
        "threats": [
            {
                "id": "threat-output-tamper",
                "stride_category": "Repudiation",
                "attack_technique": "T1195.002",
                "scenario": "Generated outputs could change before render.",
                "residual_risk": "Local checksums are not external signatures.",
            }
        ]
    }
    security_inventory = {
        "inputs": [{"path": "autoresearch.yaml"}],
        "generated_artifacts": [{"path": "output/data/a.json"}],
    }
    security_attestation = {
        "status": "passed",
        "algorithm": "sha256",
        "checked_count": 10,
        "missing_count": 0,
        "mismatch_count": 0,
        "external_signature": False,
    }

    tables = build_table_specs(
        registry,
        candidate_ledger,
        review_decisions,
        benchmark_scores,
        artifact_manifest,
        classification,
        candidate_intervals,
        class_balance,
        calibration,
        robustness,
        probability,
        bootstrap,
        paired,
        statistical,
        training,
        candidate_selection,
        diagnostic_boundary,
        security_profile,
        security_threat_model,
        security_inventory,
        security_attestation,
    )

    assert set(tables) >= {"FIGURE_METHOD_TABLE", "CANDIDATE_SELECTION_AUDIT_TABLE", "SECURITY_THREAT_MODEL_TABLE"}
    assert "@fig:ml_candidate_scores" in tables["FIGURE_METHOD_TABLE"][0]
    assert "[candidate intervals](../data/ml_candidate_intervals.json)" in tables["FIGURE_METHOD_TABLE"][0]
    assert "mlp tanh 64" in tables["ML_CANDIDATE_LEDGER_TABLE"][0]
    assert "macro F1" in tables["BOOTSTRAP_INTERVAL_TABLE"][0]
    assert "objective selection" in tables["DIAGNOSTIC_BOUNDARY_TABLE"][0]
    assert "T1195.002" in tables["SECURITY_THREAT_MODEL_TABLE"][0]
    assert "external signature" in tables["SECURITY_INTEGRITY_TABLE"][0]
    assert "{#tbl:security-integrity}" in tables["SECURITY_INTEGRITY_TABLE"][0]


def test_variable_provenance_table_counts_sources() -> None:
    table = variable_provenance_table(
        {
            "A": {"source": "output/data/a.json", "pointer": "/a"},
            "B": {"source": "output/data/a.json", "pointer": "/b"},
            "C": {"source": "output/data/c.json", "pointer": "/c"},
        }
    )

    assert "| output/data/a.json | 2 |" in table
    assert "| output/data/c.json | 1 |" in table
