"""Comprehensive validation for the configurable AutoResearch figure system.

No mocks: every figure is generated with real numpy/matplotlib from the deterministic
bounded ML task and the real loop result, then asserted to be a non-blank,
correctly-dimensioned PNG. The figure-style config is exercised for defaults, partial
overrides, malformed input, and actual application (dpi changes pixel dimensions; a
palette override changes rendered bytes). ``apply_style`` is checked for restore-on-exit
(no global-state leakage), and an isolated-vs-batch differential confirms order
independence within a process.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
from matplotlib import image as mpimg

from infrastructure.autoresearch import BudgetPolicy

from src.diagnostics import diagnostic_bundle
from src.figure_quality import figure_quality_report_payload
from src.figure_registry import figure_registry_payload
from src.figure_registry_contract import figure_method
from src.figure_specs import ALL_FIGURE_LABELS, FIGURE_DISPATCH, FIGURE_METHODS
from src.figure_style import (
    DEFAULT_FIGURE_STYLE,
    FigureStyleConfig,
    apply_style,
    figure_style_from_mapping,
    get_active_style,
    load_figure_style,
)
from src.figures import (
    write_candidate_lifecycle_figure,
    write_closure_flow_figure,
    write_mnist_class_balance_figure,
    write_mnist_error_examples_figure,
    write_mnist_subset_contact_sheet_figure,
    write_ml_bootstrap_intervals_figure,
    write_ml_calibration_reliability_figure,
    write_ml_candidate_rank_stability_figure,
    write_ml_candidate_scores_figure,
    write_ml_classification_metrics_heatmap,
    write_ml_complexity_accuracy_figure,
    write_ml_confusion_matrix_figure,
    write_ml_confusion_pairs_figure,
    write_ml_generalization_gap_figure,
    write_ml_learning_curve_figure,
    write_ml_paired_correctness_figure,
    write_ml_per_class_accuracy_figure,
    write_ml_probability_margin_figure,
    write_ml_probability_quality_figure,
    write_ml_robustness_matrix_figure,
    write_ml_selective_accuracy_figure,
    write_ml_training_dynamics_figure,
    write_stage_matrix_figure,
)
from src.figures_security import (
    write_security_control_matrix_figure,
    write_security_integrity_chain_figure,
)
from src.ml_task import run_bounded_ml_task

_THREAT_MODEL = {
    "controls": [
        {"id": "ctrl-checksums", "framework": "nist_csf", "status": "implemented", "evidence_key": "checksum_manifest"},
        {"id": "ctrl-review", "framework": "owasp_samm", "status": "planned", "evidence_key": "human_review_gate"},
    ]
}
_ATTESTATION_PASSED = {"status": "passed", "checked_count": 6, "missing_count": 0, "mismatch_count": 0}
_ATTESTATION_PENDING = {"status": "pending", "checked_count": 4, "missing_count": 1, "mismatch_count": 1}


@pytest.fixture(scope="module")
def ml_result(project_root: Path):
    """Run the deterministic bounded ML task once for figure generation."""
    return run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))


@pytest.fixture(scope="module")
def diagnostics(project_root: Path, ml_result):
    """Compute the diagnostic bundle that drives most figures."""
    return diagnostic_bundle(project_root, ml_result)


def _figure_calls(project_root: Path, figures_dir: Path, ml_result, loop_result, diag) -> dict:
    """Map each registered figure filename to a zero-arg callable that writes it."""
    return {
        "autoresearch_stage_matrix.png": lambda: write_stage_matrix_figure(figures_dir, loop_result),
        "autoresearch_closure_flow.png": lambda: write_closure_flow_figure(figures_dir, loop_result),
        "ml_candidate_scores.png": lambda: write_ml_candidate_scores_figure(
            figures_dir, ml_result, diag["candidate_intervals"]
        ),
        "ml_confusion_matrix.png": lambda: write_ml_confusion_matrix_figure(figures_dir, ml_result),
        "ml_per_class_accuracy.png": lambda: write_ml_per_class_accuracy_figure(figures_dir, ml_result),
        "ml_learning_curves.png": lambda: write_ml_learning_curve_figure(figures_dir, ml_result),
        "ml_complexity_accuracy.png": lambda: write_ml_complexity_accuracy_figure(figures_dir, ml_result),
        "mnist_error_examples.png": lambda: write_mnist_error_examples_figure(project_root, figures_dir, ml_result),
        "ml_calibration_reliability.png": lambda: write_ml_calibration_reliability_figure(
            figures_dir, diag["calibration_report"], diag["calibration_bin_intervals"]
        ),
        "ml_classification_metrics_heatmap.png": lambda: write_ml_classification_metrics_heatmap(
            figures_dir, diag["classification_diagnostics"]
        ),
        "ml_confusion_pairs.png": lambda: write_ml_confusion_pairs_figure(
            figures_dir, diag["classification_diagnostics"]
        ),
        "ml_generalization_gap.png": lambda: write_ml_generalization_gap_figure(
            figures_dir, diag["classification_diagnostics"]
        ),
        "ml_robustness_matrix.png": lambda: write_ml_robustness_matrix_figure(figures_dir, diag["robustness_report"]),
        "ml_probability_margin_distribution.png": lambda: write_ml_probability_margin_figure(
            figures_dir, diag["probability_diagnostics"]
        ),
        "ml_bootstrap_intervals.png": lambda: write_ml_bootstrap_intervals_figure(
            figures_dir, diag["bootstrap_intervals"]
        ),
        "ml_paired_correctness.png": lambda: write_ml_paired_correctness_figure(figures_dir, diag["paired_comparison"]),
        "ml_selective_accuracy.png": lambda: write_ml_selective_accuracy_figure(
            figures_dir, diag["statistical_summary"]
        ),
        "ml_probability_quality.png": lambda: write_ml_probability_quality_figure(
            figures_dir, diag["statistical_summary"]
        ),
        "ml_training_dynamics.png": lambda: write_ml_training_dynamics_figure(
            figures_dir, diag["training_diagnostics"]
        ),
        "ml_candidate_rank_stability.png": lambda: write_ml_candidate_rank_stability_figure(
            figures_dir, diag["candidate_rank_stability"]
        ),
        "autoresearch_candidate_lifecycle.png": lambda: write_candidate_lifecycle_figure(figures_dir, ml_result),
        "mnist_class_balance.png": lambda: write_mnist_class_balance_figure(figures_dir, diag["class_balance"]),
        "mnist_subset_contact_sheet.png": lambda: write_mnist_subset_contact_sheet_figure(
            project_root, figures_dir, ml_result
        ),
        "autoresearch_security_control_matrix.png": lambda: write_security_control_matrix_figure(
            figures_dir, _THREAT_MODEL
        ),
        "autoresearch_integrity_chain.png": lambda: write_security_integrity_chain_figure(
            figures_dir, _ATTESTATION_PASSED
        ),
    }


def _image_stats(path: Path) -> tuple[float, int, int]:
    pixels = np.asarray(mpimg.imread(path), dtype=float)
    grayscale = pixels[..., :3].mean(axis=2) if pixels.ndim == 3 else pixels
    return float(np.var(grayscale)), int(pixels.shape[1]), int(pixels.shape[0])


# --- A. every registered figure is fully working ---------------------------


def test_figure_label_parity_across_specs_dispatch_contract_records(
    autoresearch_loop_result, ml_result
) -> None:
    """Registry labels must match across specs, dispatch, methods, and records."""
    registry = figure_registry_payload(autoresearch_loop_result, ml_result)
    assert set(ALL_FIGURE_LABELS) == set(FIGURE_DISPATCH)
    assert set(FIGURE_METHODS) == set(ALL_FIGURE_LABELS)
    assert set(registry) == set(ALL_FIGURE_LABELS)
    for label in ALL_FIGURE_LABELS:
        assert figure_method(label) == FIGURE_METHODS[label]
        dispatch = FIGURE_DISPATCH[label]
        record = registry[label]
        assert record["filename"] == dispatch.filename
        index = ALL_FIGURE_LABELS.index(label)
        assert record["figure_id"] == f"figure_{index:03d}"
        metadata = record.get("metadata", {})
        assert isinstance(metadata, dict)
        assert metadata.get("source")


def test_figure_calls_cover_every_registered_figure(autoresearch_loop_result, ml_result, diagnostics, tmp_path):
    """The test's call map must cover exactly the registry's 25 figure filenames."""
    registry = figure_registry_payload(autoresearch_loop_result, ml_result)
    registry_filenames = {str(record["filename"]) for record in registry.values()}
    call_filenames = set(_figure_calls(tmp_path, tmp_path, ml_result, autoresearch_loop_result, diagnostics))
    assert registry_filenames == call_filenames
    assert len(call_filenames) == 25


_REGISTERED_FIGURE_FILENAMES = [
    "autoresearch_stage_matrix.png",
    "autoresearch_closure_flow.png",
    "ml_candidate_scores.png",
    "ml_confusion_matrix.png",
    "ml_per_class_accuracy.png",
    "ml_learning_curves.png",
    "ml_complexity_accuracy.png",
    "mnist_error_examples.png",
    "ml_calibration_reliability.png",
    "ml_classification_metrics_heatmap.png",
    "ml_confusion_pairs.png",
    "ml_generalization_gap.png",
    "ml_robustness_matrix.png",
    "ml_probability_margin_distribution.png",
    "ml_bootstrap_intervals.png",
    "ml_paired_correctness.png",
    "ml_selective_accuracy.png",
    "ml_probability_quality.png",
    "ml_training_dynamics.png",
    "ml_candidate_rank_stability.png",
    "autoresearch_candidate_lifecycle.png",
    "mnist_class_balance.png",
    "mnist_subset_contact_sheet.png",
    "autoresearch_security_control_matrix.png",
    "autoresearch_integrity_chain.png",
]


@pytest.mark.parametrize(
    "filename",
    [
        "autoresearch_stage_matrix.png",
        "autoresearch_closure_flow.png",
        "ml_candidate_scores.png",
        "ml_confusion_matrix.png",
        "ml_per_class_accuracy.png",
        "ml_learning_curves.png",
        "ml_complexity_accuracy.png",
        "mnist_error_examples.png",
        "ml_calibration_reliability.png",
        "ml_classification_metrics_heatmap.png",
        "ml_confusion_pairs.png",
        "ml_generalization_gap.png",
        "ml_robustness_matrix.png",
        "ml_probability_margin_distribution.png",
        "ml_bootstrap_intervals.png",
        "ml_paired_correctness.png",
        "ml_selective_accuracy.png",
        "ml_probability_quality.png",
        "ml_training_dynamics.png",
        "ml_candidate_rank_stability.png",
        "autoresearch_candidate_lifecycle.png",
        "mnist_class_balance.png",
        "mnist_subset_contact_sheet.png",
        "autoresearch_security_control_matrix.png",
        "autoresearch_integrity_chain.png",
    ],
)
def test_each_figure_generates_nonblank_png(
    filename, project_root, autoresearch_loop_result, ml_result, diagnostics, tmp_path
):
    """Each figure writes a real, non-blank, positively-dimensioned PNG."""
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    calls = _figure_calls(project_root, figures_dir, ml_result, autoresearch_loop_result, diagnostics)
    path = calls[filename]()
    assert path == figures_dir / filename
    assert path.exists()
    assert path.stat().st_size > 0
    variance, width, height = _image_stats(path)
    assert variance > 0.0, f"{filename} rendered blank"
    assert width > 0 and height > 0


def test_closure_flow_covers_pending_and_passed_states(project_root, autoresearch_loop_result, tmp_path):
    """Drive closure-flow and integrity-chain through both readiness branches."""
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    closure = write_closure_flow_figure(figures_dir, autoresearch_loop_result)
    passed = write_security_integrity_chain_figure(figures_dir, _ATTESTATION_PASSED)
    pending = write_security_integrity_chain_figure(figures_dir, _ATTESTATION_PENDING)
    pending_control = write_security_control_matrix_figure(figures_dir, _THREAT_MODEL)
    for path in (closure, passed, pending, pending_control):
        assert _image_stats(path)[0] > 0.0


def test_full_quality_report_valid_for_all_registered(
    project_root, autoresearch_loop_result, ml_result, diagnostics, tmp_path
):
    """Generating all 25 figures yields a require_all_registered quality report that is valid."""
    figures_dir = tmp_path / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    # symlink the data dir so registry metadata 'source' files resolve under tmp_path
    (tmp_path / "output" / "data").mkdir(parents=True, exist_ok=True)
    for call in _figure_calls(project_root, figures_dir, ml_result, autoresearch_loop_result, diagnostics).values():
        call()
    registry = figure_registry_payload(autoresearch_loop_result, ml_result)
    report = figure_quality_report_payload(
        tmp_path, registry, generated_at="2026-05-26T00:00:00+00:00", require_all_registered=True
    )
    assert report["figure_count"] == 25
    assert report["unregistered_pngs"] == []
    assert all(row["exists"] and row["nonblank"] and row["has_alt_text"] for row in report["figures"])


# --- B. configurability: the FigureStyleConfig contract --------------------


def test_default_style_reproduces_historical_values():
    assert DEFAULT_FIGURE_STYLE.dpi == 160
    assert DEFAULT_FIGURE_STYLE.transparent is False
    assert DEFAULT_FIGURE_STYLE.heatmap_colormap == "Blues"
    assert DEFAULT_FIGURE_STYLE.metrics_colormap == "YlGnBu"
    assert DEFAULT_FIGURE_STYLE.color("baseline") == "#52525b"
    assert DEFAULT_FIGURE_STYLE.color("accepted") == "#0072b2"


def test_color_fallback_for_unknown_role():
    assert DEFAULT_FIGURE_STYLE.color("does_not_exist", "#abcabc") == "#abcabc"


def test_rc_params_scale_font_size():
    assert DEFAULT_FIGURE_STYLE.rc_params()["font.size"] == 10.0
    assert FigureStyleConfig(font_scale=1.5).rc_params()["font.size"] == 15.0


def test_to_dict_is_json_safe_and_complete():
    payload = FigureStyleConfig(dpi=120).to_dict()
    assert payload["dpi"] == 120
    assert payload["schema"].startswith("template-autoresearch-figure-style")
    assert isinstance(payload["palette"], dict)
    assert set(payload) >= {
        "dpi",
        "transparent",
        "font_scale",
        "grid",
        "heatmap_colormap",
        "metrics_colormap",
        "palette",
    }


def test_from_mapping_partial_override_merges_over_defaults():
    style = figure_style_from_mapping({"dpi": 90, "palette": {"accent": "#123456"}})
    assert style.dpi == 90
    assert style.color("accent") == "#123456"
    # untouched roles keep the default
    assert style.color("baseline") == "#52525b"
    # untouched scalars keep the default
    assert style.heatmap_colormap == "Blues"


def test_from_mapping_supports_short_hex():
    style = figure_style_from_mapping({"palette": {"accent": "#abc"}})
    assert style.color("accent") == "#abc"


@pytest.mark.parametrize(
    "raw",
    [
        {"dpi": 0},
        {"dpi": -10},
        {"dpi": "high"},
        {"dpi": True},
        {"font_scale": 0},
        {"font_scale": "big"},
        {"grid": "yes"},
        {"heatmap_colormap": ""},
        {"heatmap_colormap": 7},
        {"palette": "not-a-mapping"},
        {"palette": {"accent": "blue"}},
        {"palette": {"accent": "#12g456"}},
        {"palette": {"accent": "#12345"}},
        {"dpii": 999},  # typo'd top-level key must fail loudly
        {"transperent": True},  # typo'd top-level key
        {"palette": {"acccent": "#123456"}},  # typo'd palette role must fail loudly
    ],
)
def test_from_mapping_rejects_malformed(raw):
    with pytest.raises(ValueError):
        figure_style_from_mapping(raw)


def test_from_mapping_rejects_non_mapping():
    with pytest.raises(ValueError):
        figure_style_from_mapping(["not", "a", "mapping"])  # type: ignore[arg-type]


def test_unknown_top_level_key_message_names_the_key():
    with pytest.raises(ValueError, match="unknown figure style key"):
        figure_style_from_mapping({"dpii": 999})
    # a valid key alongside is not enough to mask the typo
    with pytest.raises(ValueError, match="font_sizee"):
        figure_style_from_mapping({"dpi": 120, "font_sizee": 8})


def test_unknown_palette_role_message_names_the_role():
    with pytest.raises(ValueError, match="unknown palette role"):
        figure_style_from_mapping({"palette": {"acccent": "#123456"}})
    # control: a correctly-spelled role does NOT raise (proves the guard discriminates)
    assert figure_style_from_mapping({"palette": {"accent": "#123456"}}).color("accent") == "#123456"


def test_load_figure_style_reads_figures_yaml(tmp_path):
    (tmp_path / "figures.yaml").write_text("dpi: 200\ngrid: false\npalette:\n  accent: '#0a0b0c'\n", encoding="utf-8")
    style = load_figure_style(tmp_path)
    assert style.dpi == 200
    assert style.grid is False
    assert style.color("accent") == "#0a0b0c"
    # untouched roles still merge from defaults
    assert style.color("baseline") == "#52525b"


def test_load_figure_style_defaults_when_file_empty(tmp_path):
    (tmp_path / "figures.yaml").write_text("\n", encoding="utf-8")
    assert load_figure_style(tmp_path) is DEFAULT_FIGURE_STYLE


def test_load_figure_style_defaults_when_file_absent(tmp_path):
    assert load_figure_style(tmp_path) is DEFAULT_FIGURE_STYLE


def test_load_figure_style_rejects_non_mapping_root(tmp_path):
    (tmp_path / "figures.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_figure_style(tmp_path)


def test_shipped_figures_yaml_loads_and_matches_defaults(project_root):
    """The shipped figures.yaml parses and its values reproduce the defaults."""
    style = load_figure_style(project_root)
    assert style.dpi == DEFAULT_FIGURE_STYLE.dpi
    assert style.heatmap_colormap == DEFAULT_FIGURE_STYLE.heatmap_colormap
    assert style.color("accepted") == DEFAULT_FIGURE_STYLE.color("accepted")
    assert style.color("accent2") == DEFAULT_FIGURE_STYLE.color("accent2")  # merged default


# --- C. apply_style: activation + restore (no global-state leakage) ---------


def test_apply_style_activates_and_restores():
    import matplotlib

    before = get_active_style()
    with apply_style(FigureStyleConfig(dpi=72, font_scale=2.0)):
        assert get_active_style().dpi == 72
        assert matplotlib.rcParams["font.size"] == 20.0
    assert get_active_style() is before


def test_apply_style_restores_on_exception():
    before = get_active_style()
    with pytest.raises(RuntimeError):
        with apply_style(FigureStyleConfig(dpi=33)):
            assert get_active_style().dpi == 33
            raise RuntimeError("boom")
    assert get_active_style() is before


def test_apply_style_nesting_restores_inner_then_outer():
    before = get_active_style()
    with apply_style(FigureStyleConfig(dpi=120)):
        with apply_style(FigureStyleConfig(dpi=80)):
            assert get_active_style().dpi == 80
        assert get_active_style().dpi == 120
    assert get_active_style() is before


# --- D. the config is actually applied (positive controls) ------------------


def test_dpi_override_changes_pixel_dimensions(project_root, ml_result, tmp_path):
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    with apply_style(FigureStyleConfig(dpi=80)):
        low = write_ml_confusion_matrix_figure(figures_dir, ml_result)
    _, low_w, low_h = _image_stats(low)
    with apply_style(FigureStyleConfig(dpi=160)):
        high = write_ml_confusion_matrix_figure(figures_dir, ml_result)
    _, high_w, high_h = _image_stats(high)
    assert high_w > low_w and high_h > low_h
    assert high_w == pytest.approx(low_w * 2, abs=2)


def test_palette_override_changes_rendered_bytes(autoresearch_loop_result, tmp_path):
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    default_png = figures_dir / "default" / "autoresearch_stage_matrix.png"
    default_png.parent.mkdir(parents=True, exist_ok=True)
    styled_png = figures_dir / "styled" / "autoresearch_stage_matrix.png"
    styled_png.parent.mkdir(parents=True, exist_ok=True)

    with apply_style(DEFAULT_FIGURE_STYLE):
        write_stage_matrix_figure(default_png.parent, autoresearch_loop_result)
    with apply_style(figure_style_from_mapping({"palette": {"accent": "#ff0000", "positive": "#ff00ff"}})):
        write_stage_matrix_figure(styled_png.parent, autoresearch_loop_result)

    assert _digest(default_png) != _digest(styled_png)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_isolated_equals_batch_no_order_leakage(
    project_root, ml_result, autoresearch_loop_result, diagnostics, tmp_path
):
    """A figure generated alone matches the same figure generated after others (intra-process)."""
    alone_dir = tmp_path / "alone"
    batch_dir = tmp_path / "batch"
    alone_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)
    style = FigureStyleConfig(dpi=110, palette={**DEFAULT_FIGURE_STYLE.palette, "accent": "#aa3366"})

    with apply_style(style):
        alone = write_ml_confusion_matrix_figure(alone_dir, ml_result)
    with apply_style(style):
        # render several others first, then the target
        write_stage_matrix_figure(batch_dir, autoresearch_loop_result)
        write_ml_learning_curve_figure(batch_dir, ml_result)
        write_security_control_matrix_figure(batch_dir, _THREAT_MODEL)
        batch = write_ml_confusion_matrix_figure(batch_dir, ml_result)

    assert _digest(alone) == _digest(batch)


# --- E. figure_quality edge branches ---------------------------------------

# --- F. figures_core helper edge branches ----------------------------------


def test_status_color_canonical_and_muted_fallback():
    from src.figures_core import _status_color

    with apply_style(DEFAULT_FIGURE_STYLE):
        assert _status_color("accepted") == "#0072b2"
        assert _status_color("baseline") == "#52525b"
        # deferred is now a live status role (default keeps the historical colour)
        assert _status_color("deferred") == DEFAULT_FIGURE_STYLE.color("deferred")
        # a genuinely non-canonical status still resolves to the muted role
        assert _status_color("anything_else") == DEFAULT_FIGURE_STYLE.color("muted")
    # overriding palette.deferred actually changes the deferred colour (no longer a dead knob)
    with apply_style(figure_style_from_mapping({"palette": {"deferred": "#ff0000"}})):
        assert _status_color("deferred") == "#ff0000"


def test_first_label_index_raises_when_label_absent():
    from src.figures_core import _first_label_index

    assert _first_label_index(np.array([0, 1, 2, 1]), 1) == 1
    with pytest.raises(ValueError):
        _first_label_index(np.array([0, 1, 2]), 9)


def test_class_balance_count_returns_zero_when_no_match():
    from src.figures_core import _class_balance_count

    rows = [{"split": "test", "class_label": 1, "count": 5}]
    assert _class_balance_count(rows, "test", 1) == 5
    assert _class_balance_count(rows, "train", 1) == 0
    assert _class_balance_count([], "train", 0) == 0


def test_styled_grid_skips_when_grid_disabled():
    from matplotlib import pyplot as plt

    from src.figures_core import styled_grid

    fig, ax = plt.subplots()
    with apply_style(FigureStyleConfig(grid=False)):
        styled_grid(ax, "y")  # must be a no-op
    assert not any(line.get_visible() for line in ax.yaxis.get_gridlines())
    with apply_style(FigureStyleConfig(grid=True)):
        styled_grid(ax, "y")  # now draws
    assert all(line.get_visible() for line in ax.yaxis.get_gridlines())
    plt.close(fig)


def test_quality_report_handles_missing_and_sourceless_records(tmp_path):
    (tmp_path / "output" / "figures").mkdir(parents=True, exist_ok=True)
    registry = {
        "fig:missing": {"filename": "missing.png", "caption": "c", "metadata": {"source": "output/data/x.json"}},
        "fig:sourceless": {"filename": "also_missing.png", "caption": "c", "metadata": {"source": ""}},
    }
    report = figure_quality_report_payload(
        tmp_path, registry, generated_at="2026-05-26T00:00:00+00:00", require_all_registered=True
    )
    assert report["valid"] is False
    rows = {row["label"]: row for row in report["figures"]}
    assert rows["fig:missing"]["exists"] is False
    assert rows["fig:sourceless"]["source_exists"] is False
