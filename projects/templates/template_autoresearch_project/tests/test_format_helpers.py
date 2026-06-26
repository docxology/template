"""Tests for manuscript token format helpers and remaining ml/data validation branches.

Covers previously-uncovered paths in:
- manuscript/manuscript_tokens_format.py  (load_json_mapping, load_optional_json_mapping,
  string_value float branch, currency_value, decimal_value, accuracy_interval N/A branch,
  top_confusion_pair_label empty branch, bootstrap_interval no-match branch, p_value N/A,
  last_coverage_value empty/non-numeric, image_shape N/A, artifact_role all branches,
  artifact_markdown_link data/ and other-path branches, short_scope truncation,
  per_class_count multiple-count branches, first_model_candidate no-match)
- ml/data.py  (remaining _validate_mnist_shapes errors, _positive_int/_nonnegative_int
  bool/negative cases, _probability_float out-of-range, _decay_float boundary,
  robustness_transforms empty list, _mapping_list non-mapping entries, _int_value)

No mocks: all pure-function unit tests with temp files as needed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.manuscript.manuscript_tokens_format import (
    accuracy_interval,
    artifact_markdown_link,
    artifact_role,
    bootstrap_interval,
    candidate_display_label,
    currency_value,
    dataset_short_name,
    decimal_value,
    escape_table_cell,
    first_model_candidate,
    image_shape,
    last_coverage_value,
    load_json_mapping,
    load_optional_json_mapping,
    metric_label,
    model_family_labels,
    model_type_label,
    p_value,
    per_class_count,
    percent_value,
    short_scope,
    status_counts,
    status_summary,
    string_value,
    top_confusion_pair_label,
)


# ---------------------------------------------------------------------------
# load_json_mapping
# ---------------------------------------------------------------------------


def test_load_json_mapping_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="required JSON artifact is missing"):
        load_json_mapping(tmp_path / "nonexistent.json")


def test_load_json_mapping_raises_for_non_mapping_json(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a mapping"):
        load_json_mapping(path)


def test_load_json_mapping_returns_mapping(tmp_path: Path) -> None:
    path = tmp_path / "ok.json"
    path.write_text('{"key": "value"}', encoding="utf-8")
    result = load_json_mapping(path)
    assert result["key"] == "value"


# ---------------------------------------------------------------------------
# load_optional_json_mapping
# ---------------------------------------------------------------------------


def test_load_optional_json_mapping_returns_empty_for_missing(tmp_path: Path) -> None:
    result = load_optional_json_mapping(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_optional_json_mapping_returns_mapping_when_present(tmp_path: Path) -> None:
    path = tmp_path / "present.json"
    path.write_text('{"x": 1}', encoding="utf-8")
    result = load_optional_json_mapping(path)
    assert result["x"] == 1


# ---------------------------------------------------------------------------
# string_value — float branch
# ---------------------------------------------------------------------------


def test_string_value_formats_float_as_g() -> None:
    assert string_value(3.14) == "3.14"
    assert string_value(1.0) == "1"  # :g strips trailing zero


def test_string_value_non_float() -> None:
    assert string_value("hello") == "hello"
    assert string_value(42) == "42"
    assert string_value(None) == "None"


# ---------------------------------------------------------------------------
# percent_value — N/A branch
# ---------------------------------------------------------------------------


def test_percent_value_returns_na_for_non_numeric() -> None:
    assert percent_value("high") == "N/A"
    assert percent_value(None) == "N/A"


def test_percent_value_formats_numerics() -> None:
    assert percent_value(0.75) == "75.0%"
    assert percent_value(1) == "100.0%"


# ---------------------------------------------------------------------------
# currency_value — N/A branch
# ---------------------------------------------------------------------------


def test_currency_value_returns_na_for_non_numeric() -> None:
    assert currency_value("N/A") == "N/A"
    assert currency_value(None) == "N/A"


def test_currency_value_formats_numerics() -> None:
    assert currency_value(1.5) == "1.50"
    assert currency_value(0) == "0.00"


# ---------------------------------------------------------------------------
# decimal_value — N/A branch
# ---------------------------------------------------------------------------


def test_decimal_value_returns_na_for_non_numeric() -> None:
    assert decimal_value("N/A") == "N/A"
    assert decimal_value(None) == "N/A"


def test_decimal_value_formats_numerics() -> None:
    assert decimal_value(0.123) == "0.123"
    assert decimal_value(1) == "1.000"


# ---------------------------------------------------------------------------
# accuracy_interval — N/A branch
# ---------------------------------------------------------------------------


def test_accuracy_interval_returns_na_when_missing_keys() -> None:
    assert accuracy_interval({}) == "N/A"
    assert accuracy_interval({"accuracy_ci_low": "x"}) == "N/A"


def test_accuracy_interval_returns_formatted_range() -> None:
    result = accuracy_interval({"accuracy_ci_low": 0.8, "accuracy_ci_high": 0.9})
    assert "80.0%" in result
    assert "90.0%" in result


# ---------------------------------------------------------------------------
# top_confusion_pair_label — empty pairs branch
# ---------------------------------------------------------------------------


def test_top_confusion_pair_label_returns_none_for_empty_pairs() -> None:
    assert top_confusion_pair_label({}) == "none"
    assert top_confusion_pair_label({"top_confusion_pairs": []}) == "none"


def test_top_confusion_pair_label_formats_first_pair() -> None:
    result = top_confusion_pair_label(
        {"top_confusion_pairs": [{"true_label": 4, "predicted_label": 9, "count": 5}]}
    )
    assert "4 ->" in result
    assert "9" in result
    assert "5" in result


# ---------------------------------------------------------------------------
# bootstrap_interval — no matching metric
# ---------------------------------------------------------------------------


def test_bootstrap_interval_returns_na_when_metric_not_found() -> None:
    assert bootstrap_interval({"intervals": [{"metric": "accuracy", "ci_low": 0.8, "ci_high": 0.9}]}, "macro_f1") == "N/A"


def test_bootstrap_interval_returns_formatted_when_found() -> None:
    result = bootstrap_interval(
        {"intervals": [{"metric": "accuracy", "ci_low": 0.8, "ci_high": 0.9}]},
        "accuracy",
    )
    assert "80.0%" in result
    assert "90.0%" in result


# ---------------------------------------------------------------------------
# p_value — N/A branch
# ---------------------------------------------------------------------------


def test_p_value_returns_na_for_non_numeric() -> None:
    assert p_value("high") == "N/A"
    assert p_value(None) == "N/A"


def test_p_value_formats_numeric() -> None:
    assert p_value(0.05) == "0.050"


# ---------------------------------------------------------------------------
# last_coverage_value — empty rows / non-numeric value branches
# ---------------------------------------------------------------------------


def test_last_coverage_value_returns_none_for_empty_rows() -> None:
    assert last_coverage_value({}, "coverage") is None
    assert last_coverage_value({"coverage_curve": []}, "coverage") is None


def test_last_coverage_value_returns_none_for_non_numeric() -> None:
    result = last_coverage_value({"coverage_curve": [{"coverage": "N/A"}]}, "coverage")
    assert result is None


def test_last_coverage_value_returns_float_for_numeric() -> None:
    result = last_coverage_value({"coverage_curve": [{"coverage": 0.7}, {"coverage": 0.9}]}, "coverage")
    assert result == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# image_shape — N/A branch
# ---------------------------------------------------------------------------


def test_image_shape_returns_na_for_wrong_type() -> None:
    assert image_shape("not-a-list") == "N/A"
    assert image_shape(None) == "N/A"
    assert image_shape([28]) == "N/A"  # length 1, not 2


def test_image_shape_formats_pair() -> None:
    assert image_shape([28, 28]) == "28 by 28"
    assert image_shape((100, 200)) == "100 by 200"


# ---------------------------------------------------------------------------
# artifact_role — all branches
# ---------------------------------------------------------------------------


def test_artifact_role_png() -> None:
    assert artifact_role("output/figures/ml_confusion_matrix.png") == "Generated figure"


def test_artifact_role_manuscript() -> None:
    assert artifact_role("output/manuscript/00_abstract.md") == "Manuscript hydration"


def test_artifact_role_benchmark() -> None:
    assert artifact_role("output/data/benchmark_scores.json") == "Benchmark grading"


def test_artifact_role_review() -> None:
    assert artifact_role("output/data/autoresearch_review_packet.json") == "Review packet"


def test_artifact_role_security() -> None:
    assert artifact_role("output/data/autoresearch_security_profile.json") == "Security evidence"
    assert artifact_role("output/data/threat_model.json") == "Security evidence"
    assert artifact_role("output/data/integrity_attestation.json") == "Security evidence"
    assert artifact_role("output/data/supply_chain_inventory.json") == "Security evidence"


def test_artifact_role_ledger() -> None:
    assert artifact_role("output/data/run_ledger.json") == "Run or candidate ledger"


def test_artifact_role_readiness() -> None:
    assert artifact_role("output/reports/autoresearch_readiness.json") == "Readiness validation"


def test_artifact_role_evidence() -> None:
    assert artifact_role("output/reports/evidence_registry.json") == "Evidence registry"


def test_artifact_role_fallback() -> None:
    assert artifact_role("output/data/misc_artifact.json") == "Loop artifact"


# ---------------------------------------------------------------------------
# artifact_markdown_link — data/ and other-path branches
# ---------------------------------------------------------------------------


def test_artifact_markdown_link_output_path() -> None:
    result = artifact_markdown_link("output/data/ml_task_results.json")
    assert result.startswith("[")
    assert "../data/ml_task_results.json" in result


def test_artifact_markdown_link_data_path() -> None:
    result = artifact_markdown_link("data/mnist_small.npz")
    assert "../../data/mnist_small.npz" in result


def test_artifact_markdown_link_other_path() -> None:
    result = artifact_markdown_link("manuscript/config.yaml")
    assert "manuscript/config.yaml" in result


def test_artifact_markdown_link_empty_path() -> None:
    result = artifact_markdown_link("")
    assert "[N/A]" in result


# ---------------------------------------------------------------------------
# short_scope — truncation branch
# ---------------------------------------------------------------------------


def test_short_scope_short_value_unchanged() -> None:
    assert short_scope("hello world") == "hello world"


def test_short_scope_truncates_long_value() -> None:
    long_value = "a " * 60  # 120 chars
    result = short_scope(long_value)
    assert result.endswith("...")
    assert len(result) <= 92


def test_short_scope_collapses_whitespace() -> None:
    assert short_scope("  hello   world  ") == "hello world"


# ---------------------------------------------------------------------------
# per_class_count — multiple counts branch
# ---------------------------------------------------------------------------


def test_per_class_count_returns_na_for_empty_rows() -> None:
    assert per_class_count({}, "train") == "N/A"
    assert per_class_count({"rows": []}, "train") == "N/A"


def test_per_class_count_single_count() -> None:
    data = {"rows": [{"split": "train", "count": 200}, {"split": "train", "count": 200}]}
    assert per_class_count(data, "train") == "200"


def test_per_class_count_multiple_counts() -> None:
    data = {"rows": [{"split": "train", "count": 100}, {"split": "train", "count": 200}]}
    result = per_class_count(data, "train")
    assert "100" in result
    assert "200" in result


# ---------------------------------------------------------------------------
# first_model_candidate — no-match branch
# ---------------------------------------------------------------------------


def test_first_model_candidate_returns_empty_when_not_found() -> None:
    candidates = [{"model_type": "mlp"}, {"model_type": "softmax_regression"}]
    assert first_model_candidate(candidates, "nearest_centroid") == {}


def test_first_model_candidate_returns_first_match() -> None:
    candidates = [{"model_type": "mlp", "id": "c1"}, {"model_type": "mlp", "id": "c2"}]
    result = first_model_candidate(candidates, "mlp")
    assert result["id"] == "c1"


# ---------------------------------------------------------------------------
# model_type_label — unknown type fallback
# ---------------------------------------------------------------------------


def test_model_type_label_known_types() -> None:
    assert model_type_label("mlp") == "MLP"
    assert model_type_label("nearest_centroid") == "nearest-centroid"
    assert model_type_label("softmax_regression") == "softmax regression"
    assert model_type_label("tiny_patch_transformer") == "tiny patch-attention"


def test_model_type_label_unknown_type_replaces_underscores() -> None:
    assert model_type_label("custom_model_type") == "custom model type"


# ---------------------------------------------------------------------------
# metric_label — unknown metric fallback
# ---------------------------------------------------------------------------


def test_metric_label_known_metrics() -> None:
    assert metric_label("accuracy") == "accuracy"
    assert metric_label("macro_f1") == "macro F1"


def test_metric_label_unknown_replaces_underscores() -> None:
    assert metric_label("custom_metric") == "custom metric"


# ---------------------------------------------------------------------------
# status_counts and status_summary
# ---------------------------------------------------------------------------


def test_status_counts_returns_counter() -> None:
    candidates = [{"status": "accepted"}, {"status": "rejected"}, {"status": "accepted"}]
    counts = status_counts(candidates)
    assert counts["accepted"] == 2
    assert counts["rejected"] == 1


def test_status_summary_returns_sorted_string() -> None:
    candidates = [{"status": "rejected"}, {"status": "accepted"}, {"status": "deferred"}]
    result = status_summary(candidates)
    assert "accepted: 1" in result
    assert "deferred: 1" in result
    assert "rejected: 1" in result


# ---------------------------------------------------------------------------
# model_family_labels
# ---------------------------------------------------------------------------


def test_model_family_labels_deduplicates_and_sorts() -> None:
    baseline = {"model_type": "nearest_centroid"}
    candidates = [{"model_type": "mlp"}, {"model_type": "mlp"}]
    result = model_family_labels(baseline, candidates)
    # Should contain MLP and nearest-centroid (deduplicated)
    assert "MLP" in result
    assert "nearest-centroid" in result
    # Only one MLP (deduplicated)
    assert result.count("MLP") == 1


# ---------------------------------------------------------------------------
# dataset_short_name
# ---------------------------------------------------------------------------


def test_dataset_short_name_returns_first_word() -> None:
    assert dataset_short_name("MNIST handwritten digit") == "MNIST"


def test_dataset_short_name_returns_unchanged_for_single_word() -> None:
    assert dataset_short_name("MNIST") == "MNIST"


def test_dataset_short_name_preserves_na() -> None:
    assert dataset_short_name("N/A") == "N/A"


# ---------------------------------------------------------------------------
# candidate_display_label
# ---------------------------------------------------------------------------


def test_candidate_display_label_strips_exp_prefix() -> None:
    assert candidate_display_label("exp-mlp-tanh-64") == "mlp tanh 64"


def test_candidate_display_label_baseline() -> None:
    assert candidate_display_label("nearest_centroid_baseline") == "baseline"


# ---------------------------------------------------------------------------
# escape_table_cell
# ---------------------------------------------------------------------------


def test_escape_table_cell_pipes_and_newlines() -> None:
    result = escape_table_cell("a | b\nc | d")
    assert "\\|" in result
    assert "<br>" in result


# ---------------------------------------------------------------------------
# ml/data.py — remaining validation helpers
# ---------------------------------------------------------------------------


def test_positive_int_rejects_bool() -> None:
    from src.ml.data import _positive_int  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="must be a positive integer"):
        _positive_int(True, "field")


def test_positive_int_rejects_zero() -> None:
    from src.ml.data import _positive_int  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="must be a positive integer"):
        _positive_int(0, "field")


def test_positive_int_rejects_negative() -> None:
    from src.ml.data import _positive_int  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="must be a positive integer"):
        _positive_int(-1, "field")


def test_nonnegative_int_rejects_bool() -> None:
    from src.ml.data import _nonnegative_int  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="must be a non-negative integer"):
        _nonnegative_int(True, "field")


def test_nonnegative_int_rejects_negative() -> None:
    from src.ml.data import _nonnegative_int  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="must be a non-negative integer"):
        _nonnegative_int(-1, "field")


def test_nonnegative_int_accepts_zero() -> None:
    from src.ml.data import _nonnegative_int  # type: ignore[attr-defined]
    assert _nonnegative_int(0, "field") == 0


def test_probability_float_rejects_out_of_range() -> None:
    from src.ml.data import _probability_float  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="between 0 and 1"):
        _probability_float(1.5, "field")


def test_probability_float_accepts_boundary() -> None:
    from src.ml.data import _probability_float  # type: ignore[attr-defined]
    assert _probability_float(0.0, "field") == pytest.approx(0.0)
    assert _probability_float(1.0, "field") == pytest.approx(1.0)


def test_decay_float_rejects_zero() -> None:
    from src.ml.data import _decay_float  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="greater than 0"):
        _decay_float(0.0, "field")


def test_decay_float_rejects_above_one() -> None:
    from src.ml.data import _decay_float  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="at most 1"):
        _decay_float(1.5, "field")


def test_mapping_list_rejects_non_list() -> None:
    from src.ml.data import _mapping_list  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="must be a list"):
        _mapping_list("not_a_list", "label")


def test_mapping_list_rejects_non_mapping_entries() -> None:
    from src.ml.data import _mapping_list  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="entries must be mappings"):
        _mapping_list(["not_a_dict"], "label")


def test_robustness_transforms_rejects_empty_list(tmp_path: Path, project_root: Path) -> None:
    """Empty robustness_transforms list should raise ValueError."""
    import yaml
    from src.ml.data import load_mnist_task_config

    real_config_text = (project_root / "mnist_task.yaml").read_text(encoding="utf-8")
    config_dict = yaml.safe_load(real_config_text)
    config_dict["robustness_transforms"] = []  # empty list → error

    bad_config_path = tmp_path / "mnist_task.yaml"
    bad_config_path.write_text(yaml.dump(config_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="must not be empty"):
        load_mnist_task_config(tmp_path, "mnist_task.yaml")


def test_validate_mnist_shapes_rejects_wrong_image_dims(project_root: Path) -> None:
    """Arrays that aren't (n,28,28) shape should raise ValueError."""
    import numpy as np
    from src.ml.data import _validate_mnist_shapes  # type: ignore[attr-defined]

    x_bad = np.zeros((10, 14, 14))  # wrong spatial dims
    y = np.zeros(10, dtype=np.int64)
    x_good = np.zeros((10, 28, 28))

    with pytest.raises(ValueError, match="must have shape"):
        _validate_mnist_shapes(x_bad, y, x_good, y)


def test_validate_mnist_shapes_rejects_1d_labels(project_root: Path) -> None:
    """2D label array should raise ValueError."""
    import numpy as np
    from src.ml.data import _validate_mnist_shapes  # type: ignore[attr-defined]

    x = np.zeros((10, 28, 28))
    y_2d = np.zeros((10, 1), dtype=np.int64)  # 2D → must be 1D
    with pytest.raises(ValueError, match="one-dimensional"):
        _validate_mnist_shapes(x, y_2d, x, np.zeros(10, dtype=np.int64))


def test_validate_mnist_shapes_rejects_mismatched_lengths(project_root: Path) -> None:
    """Mismatched image/label sizes should raise ValueError."""
    import numpy as np
    from src.ml.data import _validate_mnist_shapes  # type: ignore[attr-defined]

    x = np.zeros((10, 28, 28))
    y_short = np.zeros(8, dtype=np.int64)  # wrong length
    with pytest.raises(ValueError, match="matching lengths"):
        _validate_mnist_shapes(x, y_short, x, np.zeros(10, dtype=np.int64))
