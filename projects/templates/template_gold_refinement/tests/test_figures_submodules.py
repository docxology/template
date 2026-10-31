"""Direct tests for canonical figure submodules and their real domain inputs.

Graph builders use actual refinery and formalism data. Figure IO controls
write real matplotlib PNG/SVG pairs and inspect their quality records.
"""

from __future__ import annotations

import os

import matplotlib
import networkx as nx
import pytest

matplotlib.use("Agg")  # headless before any pyplot use
import matplotlib.pyplot as plt  # noqa: E402

from figures import _common, graphs


# --------------------------------------------------------------------------- #
# _common.py: FigureSpec dataclass + registry records
# --------------------------------------------------------------------------- #
class TestFigureSpecSubmodule:
    def test_specs_are_twelve_and_unique(self):
        specs = _common.FIGURE_SPECS
        assert len(specs) == 12
        for field in ("name", "label", "path", "svg_path"):
            values = [getattr(spec, field) for spec in specs]
            assert len(values) == len(set(values)), f"duplicate {field}"

    def test_svg_path_property_derives_from_png(self):
        spec = _common.FIGURE_SPEC_BY_NAME["purity_progression"]
        assert spec.path.endswith(".png")
        assert spec.svg_path == "purity_progression.svg"

    def test_registry_record_includes_svg_path(self):
        spec = _common.FIGURE_SPEC_BY_NAME["provenance_sankey"]
        record = spec.registry_record()
        assert record["name"] == "provenance_sankey"
        assert record["svg_path"] == spec.svg_path
        assert isinstance(record["data_sources"], tuple)

    def test_spec_lookup_helper_matches_index(self):
        assert _common._spec("token_density") is _common.FIGURE_SPEC_BY_NAME["token_density"]

    def test_spec_by_name_covers_every_spec(self):
        assert set(_common.FIGURE_SPEC_BY_NAME) == {s.name for s in _common.FIGURE_SPECS}

    def test_figure_markdown_variables_derive_from_specs(self):
        variables = _common.figure_markdown_variables()
        assert len(variables) == len(_common.FIGURE_SPECS)
        for spec in _common.FIGURE_SPECS:
            key = f"FIGURE_{spec.name.upper()}"
            assert key in variables
            assert f"{{#{spec.label}}}" in variables[key]


# --------------------------------------------------------------------------- #
# _common.py: deterministic purity transform + palettes
# --------------------------------------------------------------------------- #
class TestPurityNinesTransform:
    def test_monotonic_in_purity(self):
        values = _common.purity_nines_values((0.10, 0.375, 0.75, 0.9167, 0.999))
        assert values == sorted(values)

    def test_late_stage_gain_dominates(self):
        values = _common.purity_nines_values((0.9, 0.99, 0.999999999))
        assert values[-1] > values[0] * 8

    def test_clamps_perfect_purity_without_overflow(self):
        # purity == 1.0 -> 1 - p == 0 is clamped to 1e-12 -> finite 12.0
        (score,) = _common.purity_nines_values((1.0,))
        assert score == pytest.approx(12.0)

    def test_nines_score_one_tenth_purity_is_near_zero(self):
        assert _common._nines_score(0.9) == pytest.approx(1.0)

    def test_stage_palette_and_labels_align(self):
        assert len(_common.STAGE_COLORS) == 5
        assert len(_common.STAGE_LABELS) == 5
        assert all(color.startswith("#") for color in _common.STAGE_COLORS)
        assert _common.STAGE_LABELS[0] == "Ore"
        assert _common.STAGE_LABELS[-1] == "Certification"


# --------------------------------------------------------------------------- #
# _common.py: label / path helpers
# --------------------------------------------------------------------------- #
class TestCommonHelpers:
    def test_source_display_label_strips_symbol_suffix(self):
        assert _common._source_display_label("src/refinery.py::run_refinery") == "refinery.py"

    def test_source_display_label_strips_fragment(self):
        assert _common._source_display_label("manuscript/config.yaml#gold_refinement") == "config.yaml"

    def test_source_display_label_basename_for_path(self):
        assert _common._source_display_label("output/reports/token_plan.json") == "token_plan.json"

    def test_source_display_label_passthrough_plain_token(self):
        assert _common._source_display_label("local") == "local"

    def test_short_label_wraps_long_text(self):
        wrapped = _common._short_label("certification nine nines purity output", width=12)
        assert "\n" in wrapped
        explicit = "Input ore\n10.00%\n24K (nine-nines certified)\n99.9999999% (nine-nines)"
        wrapped = _common._short_label(explicit, width=18)
        assert wrapped.splitlines()[:2] == ["Input ore", "10.00%"]
        assert "".join(wrapped.split()) == "".join(explicit.split())

    def test_svg_path_helper_swaps_suffix(self, tmp_path):
        assert _common._svg_path(tmp_path / "fig.png") == tmp_path / "fig.svg"

    def test_ensure_output_dir_creates_nested(self, tmp_path):
        target = tmp_path / "figs" / "nested"
        result = _common._ensure_output_dir(target)
        assert result == target
        assert target.is_dir()


# --------------------------------------------------------------------------- #
# _common.py: headless figure IO helpers (real PNG/SVG, no mocks)
# --------------------------------------------------------------------------- #
class TestFigureIoHelpers:
    def _make_figure(self):
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([0, 1, 2], [0.1, 0.5, 0.99], color="#FFD700")
        _common._style_axes(ax, grid_axis="y")
        return fig

    def test_save_figure_writes_png_and_svg(self, tmp_path):
        out = tmp_path / "demo.png"
        returned = _common._save_figure(self._make_figure(), out)
        assert returned == out
        assert out.exists() and out.stat().st_size > 1000
        svg = tmp_path / "demo.svg"
        assert svg.exists() and svg.stat().st_size > 1000

    def test_normalize_svg_whitespace_strips_trailing_space(self, tmp_path):
        svg = tmp_path / "ws.svg"
        svg.write_text("<svg>  \n  body \n</svg>\n", encoding="utf-8")
        _common._normalize_svg_whitespace(svg)
        text = svg.read_text(encoding="utf-8")
        assert "  \n" not in text
        assert text.endswith("\n")

    def test_quality_record_on_real_png_passes_quality(self, tmp_path):
        spec = _common.FIGURE_SPEC_BY_NAME["purity_progression"]
        # Render a sufficiently large, non-white figure to satisfy the gate.
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar([0, 1, 2, 3, 4], [0.1, 0.4, 0.75, 0.92, 0.999], color=_common.STAGE_COLORS)
        _common._save_figure(fig, tmp_path / spec.path)
        record = _common._quality_record(tmp_path, spec)
        assert record["png_exists"] is True
        assert record["svg_exists"] is True
        assert record["width_px"] >= 900
        assert record["height_px"] >= 600
        assert record["nonwhite_fraction"] > 0.01
        assert record["passes_quality"] is True

    def test_quality_record_missing_png_fails_quality(self, tmp_path):
        spec = _common.FIGURE_SPEC_BY_NAME["token_density"]
        record = _common._quality_record(tmp_path, spec)
        assert record["png_exists"] is False
        assert record["png_bytes"] == 0
        assert record["passes_quality"] is False


class TestDrawLabeledDigraph:
    """Drive the shared digraph renderer onto headless axes with real graphs."""

    def test_draws_provenance_graph_with_edge_labels(self, tmp_path):
        graph, edge_widths = graphs.build_provenance_flow_graph()
        positions = {n: (data["x"], data["y"]) for n, data in graph.nodes(data=True)}
        fig, ax = plt.subplots(figsize=(8, 4))
        _common._draw_labeled_digraph(ax, graph, positions, edge_widths=edge_widths)
        # off-axis after drawing; figure renders without raising
        assert not ax.axison
        out = _common._save_figure(fig, tmp_path / "drawn.png")
        assert out.exists() and out.stat().st_size > 1000

    def test_draws_graph_without_edge_labels(self, tmp_path):
        graph = nx.DiGraph()
        graph.add_node("a", label="Alpha", kind="source")
        graph.add_node("b", kind="unknown_kind")  # exercises label/color fallbacks
        graph.add_edge("a", "b")  # no edge label -> skips edge-label branch
        positions = {"a": (0.0, 0.0), "b": (1.0, 0.0)}
        fig, ax = plt.subplots(figsize=(4, 3))
        _common._draw_labeled_digraph(ax, graph, positions)
        assert not ax.axison
        plt.close(fig)


# --------------------------------------------------------------------------- #
# graphs.py: pure DiGraph builders driven by real project data
# --------------------------------------------------------------------------- #
class TestGraphBuildersSubmodule:
    def test_provenance_flow_graph_is_digraph_with_expected_shape(self):
        graph, edge_widths = graphs.build_provenance_flow_graph()
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() == 6  # ore + 5 stages
        assert graph.number_of_edges() == 5
        assert len(edge_widths) == 5
        assert all(width > 0 for width in edge_widths)
        assert "ore" in graph
        assert graph.nodes["ore"]["x"] == 0.0
        # final stage node is the publication layer
        assert graph.nodes["stage_5"]["kind"] == "publication"

    def test_provenance_edge_widths_scale_with_gain(self):
        graph, edge_widths = graphs.build_provenance_flow_graph()
        # widest edge corresponds to the largest single-stage purity gain
        assert max(edge_widths) == pytest.approx(6.0)
        assert min(edge_widths) > 1.0

    def test_formalism_traceability_graph_topology(self):
        graph = graphs.build_formalism_traceability_graph()
        assert isinstance(graph, nx.DiGraph)
        kinds = [data["kind"] for _, data in graph.nodes(data=True)]
        n_formalism = kinds.count("formalism")
        # 3 nodes per formalism (formalism, equation, source); 2 edges per formalism
        assert graph.number_of_nodes() == n_formalism * 3
        assert graph.number_of_edges() == n_formalism * 2
        assert {data["kind"] for _, data in graph.nodes(data=True)} == {
            "formalism",
            "equation",
            "source",
        }
        assert all("x" in data and "y" in data for _, data in graph.nodes(data=True))

    def test_implementation_circuit_graph_layers(self):
        graph = graphs.build_implementation_circuit_graph()
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() == 8
        assert graph.number_of_edges() == 9
        assert graph.nodes["figures"]["label"].endswith("PNG + SVG registry")
        # feedback edge closes the circuit back to config
        assert graph.has_edge("publication", "config")
        assert all("layer" in data for _, data in graph.nodes(data=True))

    def test_claim_evidence_topology_dedupes_shared_evidence(self):
        class Entry:
            def __init__(self, name, evidence, boundary, supported):
                self.claim_name = name
                self.evidence_source = evidence
                self.boundary = boundary
                self.supported = supported

        entries = [
            Entry("Claim A", "src/refinery.py::run_refinery", "local", True),
            Entry("Claim B", "src/refinery.py::run_refinery", "local", False),
        ]
        graph = graphs.build_claim_evidence_topology(entries)
        assert isinstance(graph, nx.DiGraph)
        # 2 claims + 1 shared evidence node + 1 shared boundary node
        assert graph.number_of_nodes() == 4
        assert {data["kind"] for _, data in graph.nodes(data=True)} == {
            "claim",
            "evidence",
            "boundary",
        }
        labels = {
            (u, v): data.get("label")
            for u, v, data in graph.edges(data=True)
            if data.get("label") in {"supported", "missing"}
        }
        assert "supported" in labels.values()
        assert "missing" in labels.values()

    def test_claim_evidence_topology_handles_none_boundary(self):
        class Entry:
            claim_name = "Boundaryless"
            evidence_source = "manuscript/config.yaml"
            boundary = None
            supported = True

        graph = graphs.build_claim_evidence_topology([Entry()])
        # None boundary falls back to the "local" label
        boundary_labels = [data["label"] for _, data in graph.nodes(data=True) if data["kind"] == "boundary"]
        assert boundary_labels == ["local"]


def test_submodules_loaded_from_subpackage_files():
    """Bind the imports to the actual canonical figure submodules."""
    assert os.path.basename(os.path.dirname(_common.__file__)) == "figures"
    assert _common.__file__.endswith(os.path.join("figures", "_common.py"))
    assert graphs.__file__.endswith(os.path.join("figures", "graphs.py"))
