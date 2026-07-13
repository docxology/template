"""test_figures.py — Tests for the figures module.

Skips all tests when matplotlib is unavailable.  Uses tmp_path so generated
PNG files land in an isolated temp directory and never pollute source tree.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

# ---------------------------------------------------------------------------
# Skip guard — applied at collection time before any matplotlib import
# ---------------------------------------------------------------------------

try:
    import matplotlib  # noqa: F401

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _MATPLOTLIB_AVAILABLE,
    reason="matplotlib not installed — skipping figure tests",
)

# Only import the module when matplotlib is present so collection succeeds
# in minimal CI environments.
if _MATPLOTLIB_AVAILABLE:
    from src.figures import (
        all_figures,
        generate_architecture_overview,
        generate_cover_art,
        generate_fond_taxonomy,
        generate_pipeline_flow,
        generate_resilience_layers,
        generate_resource_counts,
        generate_rule_hierarchy,
        generate_status_dashboard,
        generate_tool_contract,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_png(path: pathlib.Path) -> None:
    """Assert that *path* exists, is a file, and looks like a PNG."""
    assert path.exists(), f"Expected figure at {path}"
    assert path.is_file(), f"Not a file: {path}"
    assert path.suffix.lower() == ".png", f"Expected .png suffix, got: {path.suffix}"
    assert path.stat().st_size > 0, f"Empty file: {path}"


# ---------------------------------------------------------------------------
# generate_architecture_overview
# ---------------------------------------------------------------------------


class TestGenerateArchitectureOverview:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_architecture_overview(output_dir=tmp_path)
        _assert_png(result)

    def test_returns_path_object(self, tmp_path: pathlib.Path):
        result = generate_architecture_overview(output_dir=tmp_path)
        assert isinstance(result, pathlib.Path)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_architecture_overview(output_dir=tmp_path)
        assert result.name == "architecture_overview.png"

    def test_custom_filename(self, tmp_path: pathlib.Path):
        result = generate_architecture_overview(output_dir=tmp_path, filename="my_arch.png")
        assert result.name == "my_arch.png"
        _assert_png(result)

    def test_output_dir_created_if_absent(self, tmp_path: pathlib.Path):
        nested = tmp_path / "a" / "b" / "c"
        assert not nested.exists()
        result = generate_architecture_overview(output_dir=nested)
        assert nested.is_dir()
        _assert_png(result)


# ---------------------------------------------------------------------------
# generate_resource_counts
# ---------------------------------------------------------------------------


class TestGenerateResourceCounts:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_resource_counts(output_dir=tmp_path)
        _assert_png(result)

    def test_returns_path_object(self, tmp_path: pathlib.Path):
        result = generate_resource_counts(output_dir=tmp_path)
        assert isinstance(result, pathlib.Path)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_resource_counts(output_dir=tmp_path)
        assert result.name == "resource_counts.png"

    def test_custom_counts(self, tmp_path: pathlib.Path):
        counts = {"Alpha": 10, "Beta": 5, "Gamma": 0}
        result = generate_resource_counts(counts=counts, output_dir=tmp_path)
        _assert_png(result)

    def test_single_item_counts(self, tmp_path: pathlib.Path):
        """Edge case: single-item dict should not raise."""
        result = generate_resource_counts(counts={"Only": 1}, output_dir=tmp_path)
        _assert_png(result)

    def test_zero_value_counts(self, tmp_path: pathlib.Path):
        """All-zero values should produce a valid (flat) bar chart."""
        result = generate_resource_counts(counts={"A": 0, "B": 0}, output_dir=tmp_path)
        _assert_png(result)

    def test_output_dir_created_if_absent(self, tmp_path: pathlib.Path):
        nested = tmp_path / "sub"
        result = generate_resource_counts(output_dir=nested)
        assert nested.is_dir()
        _assert_png(result)


# ---------------------------------------------------------------------------
# generate_status_dashboard
# ---------------------------------------------------------------------------


class TestGenerateStatusDashboard:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_status_dashboard(output_dir=tmp_path)
        _assert_png(result)

    def test_returns_path_object(self, tmp_path: pathlib.Path):
        result = generate_status_dashboard(output_dir=tmp_path)
        assert isinstance(result, pathlib.Path)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_status_dashboard(output_dir=tmp_path)
        assert result.name == "status_dashboard.png"

    def test_custom_statuses_ok(self, tmp_path: pathlib.Path):
        statuses = {"comp_a": "ok", "comp_b": "ok"}
        result = generate_status_dashboard(statuses=statuses, output_dir=tmp_path)
        _assert_png(result)

    def test_custom_statuses_mixed(self, tmp_path: pathlib.Path):
        statuses = {
            "comp_a": "ok",
            "comp_b": "partial",
            "comp_c": "missing",
        }
        result = generate_status_dashboard(statuses=statuses, output_dir=tmp_path)
        _assert_png(result)

    def test_single_component(self, tmp_path: pathlib.Path):
        """Edge case: single component should not divide-by-zero."""
        result = generate_status_dashboard(statuses={"solo": "ok"}, output_dir=tmp_path)
        _assert_png(result)

    def test_unknown_status_string(self, tmp_path: pathlib.Path):
        """Unknown status values should fall back to neutral colour, not raise."""
        result = generate_status_dashboard(statuses={"comp": "unknown_status"}, output_dir=tmp_path)
        _assert_png(result)

    def test_output_dir_created_if_absent(self, tmp_path: pathlib.Path):
        nested = tmp_path / "dash" / "out"
        result = generate_status_dashboard(output_dir=nested)
        assert nested.is_dir()
        _assert_png(result)


# ---------------------------------------------------------------------------
# all_figures
# ---------------------------------------------------------------------------


class TestAllFigures:
    def test_returns_dict(self, tmp_path: pathlib.Path):
        result = all_figures(output_dir=tmp_path)
        assert isinstance(result, dict)

    def test_expected_keys(self, tmp_path: pathlib.Path):
        result = all_figures(output_dir=tmp_path)
        expected = {
            "architecture_overview",
            "resource_counts",
            "status_dashboard",
            "fond_taxonomy",
            "rule_hierarchy",
            "tool_contract",
            "resilience_layers",
            "pipeline_flow",
            "cover_art",
        }
        assert set(result.keys()) == expected

    def test_all_values_are_paths(self, tmp_path: pathlib.Path):
        result = all_figures(output_dir=tmp_path)
        for key, path in result.items():
            assert isinstance(path, pathlib.Path), f"{key}: expected Path, got {type(path)}"

    def test_all_files_exist(self, tmp_path: pathlib.Path):
        result = all_figures(output_dir=tmp_path)
        for path in result.values():
            _assert_png(path)

    def test_output_dir_created_if_absent(self, tmp_path: pathlib.Path):
        nested = tmp_path / "generated" / "figs"
        assert not nested.exists()
        all_figures(output_dir=nested)
        assert nested.is_dir()

    def test_all_figures_accepts_string_output_dir(self, tmp_path: pathlib.Path):
        result = all_figures(output_dir=str(tmp_path))
        assert isinstance(result, dict)
        for path in result.values():
            assert path is not None
            _assert_png(path)


class TestGenerateStatusDashboardIntegrationResult:
    def test_uses_integration_result_statuses(self, tmp_path: pathlib.Path):
        class StatusCarrier:
            statuses = {"Bibliography Fond": "partial", "Contacts Fond": "missing"}

        result = generate_status_dashboard(
            integration_result=StatusCarrier(),
            output_dir=tmp_path,
        )
        _assert_png(result)


# ---------------------------------------------------------------------------
# generate_fond_taxonomy
# ---------------------------------------------------------------------------


class TestGenerateFondTaxonomy:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_fond_taxonomy(output_dir=tmp_path)
        _assert_png(result)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_fond_taxonomy(output_dir=tmp_path)
        assert result.name == "fond_taxonomy.png"

    def test_custom_filename(self, tmp_path: pathlib.Path):
        result = generate_fond_taxonomy(output_dir=tmp_path, filename="tax.png")
        assert result.name == "tax.png"
        _assert_png(result)


# ---------------------------------------------------------------------------
# generate_rule_hierarchy
# ---------------------------------------------------------------------------


class TestGenerateRuleHierarchy:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_rule_hierarchy(output_dir=tmp_path)
        _assert_png(result)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_rule_hierarchy(output_dir=tmp_path)
        assert result.name == "rule_hierarchy.png"


# ---------------------------------------------------------------------------
# generate_tool_contract
# ---------------------------------------------------------------------------


class TestGenerateToolContract:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_tool_contract(output_dir=tmp_path)
        _assert_png(result)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_tool_contract(output_dir=tmp_path)
        assert result.name == "tool_contract.png"


# ---------------------------------------------------------------------------
# generate_resilience_layers
# ---------------------------------------------------------------------------


class TestGenerateResilienceLayers:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_resilience_layers(output_dir=tmp_path)
        _assert_png(result)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_resilience_layers(output_dir=tmp_path)
        assert result.name == "resilience_layers.png"


# ---------------------------------------------------------------------------
# generate_pipeline_flow
# ---------------------------------------------------------------------------


class TestGeneratePipelineFlow:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_pipeline_flow(output_dir=tmp_path)
        _assert_png(result)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_pipeline_flow(output_dir=tmp_path)
        assert result.name == "pipeline_flow.png"


# ---------------------------------------------------------------------------
# generate_cover_art
# ---------------------------------------------------------------------------


class TestGenerateCoverArt:
    def test_creates_file(self, tmp_path: pathlib.Path):
        result = generate_cover_art(output_dir=tmp_path)
        _assert_png(result)

    def test_default_filename(self, tmp_path: pathlib.Path):
        result = generate_cover_art(output_dir=tmp_path)
        assert result.name == "cover_art.png"

    def test_custom_filename(self, tmp_path: pathlib.Path):
        result = generate_cover_art(output_dir=tmp_path, filename="my_cover.png")
        assert result.name == "my_cover.png"
        _assert_png(result)

    def test_output_dir_created_if_absent(self, tmp_path: pathlib.Path):
        nested = tmp_path / "cover" / "out"
        result = generate_cover_art(output_dir=nested)
        assert nested.is_dir()
        _assert_png(result)


class TestDefaultOutputDirectory:
    def test_generate_architecture_overview_uses_default_dir(self, tmp_path: pathlib.Path):
        result = generate_architecture_overview(
            default_output_dir=lambda: tmp_path / "default",
        )
        _assert_png(result)
        assert result.parent == tmp_path / "default"
