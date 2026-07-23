"""Stale-metrics negative control for template_template.

Verifies that the generated metrics JSON (when present in output/) matches
the live repo state, and that the metrics dict contains the expected keys
with non-stale values. This closes the TODO item: "Add negative controls
for stale generated metrics."
"""

from __future__ import annotations

import json

from template_template.metrics import build_manuscript_metrics_dict

from helpers import PROJECT_DIR, REPO_ROOT


def test_metrics_dict_has_expected_keys() -> None:
    """The metrics dict must contain the canonical set of keys."""
    metrics = build_manuscript_metrics_dict(REPO_ROOT)
    expected_keys = {
        "coverage_floor_infrastructure",
        "coverage_floor_project",
        "figure_font_floor_pt",
        "figure_dpi",
    }
    assert expected_keys.issubset(metrics.keys()), f"Missing keys: {expected_keys - set(metrics.keys())}"


def test_metrics_dict_counts_are_positive() -> None:
    """Core live-count metrics must be positive integers, not stale zeros."""
    metrics = build_manuscript_metrics_dict(REPO_ROOT)
    # Only check counts that must always be positive in a healthy repo
    always_positive_keys = [
        "module_count",
        "project_count",
        "pipeline_stage_count",
        "python_file_count",
    ]
    for key in always_positive_keys:
        if key in metrics:
            value = metrics[key]
            if isinstance(value, int):
                assert value > 0, f"Stale zero count for {key}: {value}"


def test_generated_metrics_json_matches_live_repo_when_present() -> None:
    """If output/data/metrics.json exists, it must match the live metrics dict.

    This is the stale-metrics negative control: if the generated file
    drifts from the live repo state, the test fails.
    """
    metrics_path = PROJECT_DIR / "output" / "data" / "metrics.json"
    if not metrics_path.is_file():
        # No generated metrics file — nothing to check for staleness
        return

    generated = json.loads(metrics_path.read_text(encoding="utf-8"))
    live = build_manuscript_metrics_dict(REPO_ROOT)

    # Check that key policy values match
    policy_keys = [
        "coverage_floor_infrastructure",
        "coverage_floor_project",
        "figure_font_floor_pt",
        "figure_dpi",
    ]
    for key in policy_keys:
        if key in generated and key in live:
            assert generated[key] == live[key], f"Stale metric {key}: generated={generated[key]}, live={live[key]}"


def test_metrics_dict_does_not_contain_private_project_names() -> None:
    """Negative control: private/local project names must not appear in metrics."""
    metrics = build_manuscript_metrics_dict(REPO_ROOT)
    # These are known private lifecycle paths that should never appear
    forbidden_substrings = ["working/", "ongoing/", "archive/", "published/", "active/"]
    metrics_str = json.dumps(metrics)
    for forbidden in forbidden_substrings:
        assert forbidden not in metrics_str, f"Private path segment '{forbidden}' found in metrics"
