"""Tests for figure-registry and manuscript-token cross-reference integrity."""

from __future__ import annotations

import json
import re
from pathlib import Path

from figures import FIGURE_SPECS

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_FIG_LABEL_RE = re.compile(r"\[@fig:([a-z_]+)\]")
_EQ_REF_RE = re.compile(r"\[@(eq:[A-Za-z0-9_.:-]+)\]")
_EQ_DEF_RE = re.compile(r"\{#(eq:[A-Za-z0-9_.:-]+)\}|\\label\{(eq:[A-Za-z0-9_.:-]+)\}")
_TBL_REF_RE = re.compile(r"\[@(tbl:[A-Za-z0-9_.:-]+)\]")
_TBL_DEF_RE = re.compile(r"\{#(tbl:[A-Za-z0-9_.:-]+)\}")
_DOC_ONLY = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})


def _resolved_manuscript_text() -> str:
    from manuscript_variables import generate_variables

    variables = generate_variables(_PROJECT_ROOT)
    parts = []
    for md_file in sorted((_PROJECT_ROOT / "manuscript").glob("*.md")):
        if md_file.name in _DOC_ONLY:
            continue
        text = md_file.read_text(encoding="utf-8")
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        parts.append(text)
    return "\n\n".join(parts)


def _strip_markdown_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", text)


class TestFigureRegistryIntegrity:
    """Every [@fig:...] in manuscript must have a registry entry."""

    def test_all_fig_refs_in_registry(self):
        # Load figure registry
        registry_path = _PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
        assert registry_path.exists(), "figure_registry.json not found — run refinement_analysis.py first"

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

        assert not unresolved, "Manuscript figure references not in registry:\n" + "\n".join(
            f"  {label}: {files}" for label, files in sorted(unresolved.items())
        )

    def test_registry_has_all_expected_figures(self):
        registry_path = _PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
        assert registry_path.exists(), "figure_registry.json not found"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        labels = {f["label"] for f in registry.get("figures", [])}
        expected = {spec.label for spec in FIGURE_SPECS}
        missing = expected - labels
        assert not missing, f"Missing figures in registry: {missing}"
        assert labels == expected

    def test_all_pngs_exist(self):
        registry_path = _PROJECT_ROOT / "output" / "figures" / "figure_registry.json"
        assert registry_path.exists(), "figure_registry.json not found"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        figures_dir = _PROJECT_ROOT / "output" / "figures"
        for fig in registry.get("figures", []):
            png_path = figures_dir / fig["path"]
            svg_path = figures_dir / fig["svg_path"]
            assert {"name", "caption", "generated_by", "data_sources", "visual_encoding"} <= set(fig)
            assert png_path.exists(), f"Figure PNG not found: {png_path}"
            assert svg_path.exists(), f"Figure SVG not found: {svg_path}"
            assert png_path.stat().st_size > 100, f"Figure appears blank: {png_path}"
            assert svg_path.stat().st_size > 100, f"Figure SVG appears blank: {svg_path}"

    def test_figure_quality_report_matches_registry(self):
        quality_path = _PROJECT_ROOT / "output" / "reports" / "figure_quality_report.json"
        assert quality_path.exists(), "figure_quality_report.json not found"
        report = json.loads(quality_path.read_text(encoding="utf-8"))
        assert report["figure_count"] == len(FIGURE_SPECS)
        assert report["png_count"] == len(FIGURE_SPECS)
        assert report["svg_count"] == len(FIGURE_SPECS)
        assert report["registry_parity"] is True
        assert report["passing_count"] == len(FIGURE_SPECS)


class TestFormalReferenceIntegrity:
    def test_all_equation_refs_have_definitions(self):
        text = _strip_markdown_code(_resolved_manuscript_text())
        refs = set(_EQ_REF_RE.findall(text))
        defs = {a or b for a, b in _EQ_DEF_RE.findall(text)}
        assert refs <= defs, f"Missing equation definitions: {sorted(refs - defs)}"

    def test_all_table_refs_have_definitions(self):
        text = _strip_markdown_code(_resolved_manuscript_text())
        refs = set(_TBL_REF_RE.findall(text))
        defs = set(_TBL_DEF_RE.findall(text))
        assert refs <= defs, f"Missing table definitions: {sorted(refs - defs)}"


class TestDashboardIntegrity:
    """Dashboard HTML should be generated and valid."""

    def test_dashboard_exists(self):
        dashboard_path = _PROJECT_ROOT / "output" / "dashboard.html"
        assert dashboard_path.exists(), "dashboard.html not found — run refinement_analysis.py first"
        content = dashboard_path.read_text(encoding="utf-8")
        assert "<html" in content.lower()
        assert "Gold Refinement Dashboard" in content
        assert "Refinery Stages" in content
