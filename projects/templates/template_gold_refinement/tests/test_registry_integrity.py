"""Tests for figure-registry and manuscript-token cross-reference integrity."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_FIG_LABEL_RE = re.compile(r"\[@fig:([a-z_]+)\]")
_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})


class TestFigureRegistryIntegrity:
    """Every [@fig:...] in manuscript must have a registry entry."""

    def test_all_fig_refs_in_registry(self):
        # Load figure registry
        registry_path = _PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
        if not registry_path.exists():
            pytest.skip("figure_registry.json not found — run refinement_analysis.py first")

        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registered_labels = {f["label"] for f in registry.get("figures", [])}
        assert len(registered_labels) > 0, "No figures registered"

        # Scan manuscript for [@fig:...] references
        manuscript_dir = _PROJECT_ROOT / "manuscript"
        unresolved: dict[str, list[str]] = {}
        for md_file in sorted(manuscript_dir.glob("*.md")):
            if md_file.name in _DOC_ONLY:
                continue
            text = md_file.read_text(encoding="utf-8")
            for label in _FIG_LABEL_RE.findall(text):
                full_label = f"fig:{label}"
                if full_label not in registered_labels:
                    unresolved.setdefault(full_label, []).append(md_file.name)

        assert not unresolved, (
            "Manuscript figure references not in registry:\n"
            + "\n".join(f"  {label}: {files}" for label, files in sorted(unresolved.items()))
        )

    def test_registry_has_all_expected_figures(self):
        registry_path = _PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
        if not registry_path.exists():
            pytest.skip("figure_registry.json not found")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        labels = {f["label"] for f in registry.get("figures", [])}
        expected = {
            "fig:purity_progression",
            "fig:karat_grading",
            "fig:token_density",
            "fig:provenance_sankey",
            "fig:purity_claim_scatter",
            "fig:token_heatmap",
        }
        missing = expected - labels
        assert not missing, f"Missing figures in registry: {missing}"

    def test_all_pngs_exist(self):
        registry_path = _PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
        if not registry_path.exists():
            pytest.skip("figure_registry.json not found")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        figures_dir = _PROJECT_ROOT / "output" / "figures"
        for fig in registry.get("figures", []):
            png_path = figures_dir / fig["path"]
            assert png_path.exists(), f"Figure PNG not found: {png_path}"
            assert png_path.stat().st_size > 100, f"Figure appears blank: {png_path}"


class TestDashboardIntegrity:
    """Dashboard HTML should be generated and valid."""

    def test_dashboard_exists(self):
        dashboard_path = _PROJECT_ROOT / "output" / "dashboard.html"
        if not dashboard_path.exists():
            pytest.skip("dashboard.html not found — run refinement_analysis.py first")
        content = dashboard_path.read_text(encoding="utf-8")
        assert "<html" in content.lower()
        assert "Gold Refinement Dashboard" in content
        assert "Refinery Stages" in content
