"""Tests for src.figures — figure generation for the gold-refinement exemplar."""

from __future__ import annotations

import json

from figures import (
    FIGURE_SPECS,
    STAGE_COLORS,
    STAGE_LABELS,
    build_claim_evidence_topology,
    build_formalism_traceability_graph,
    build_implementation_circuit_graph,
    build_provenance_flow_graph,
    figure_registry_payload,
    generate_all_figures,
    generate_claim_evidence_assay,
    generate_evidence_tier_ladder,
    generate_formalism_traceability,
    generate_implementation_circuit,
    generate_integrity_gate_matrix,
    generate_integrity_risk_matrix,
    generate_karat_grading_chart,
    generate_purity_progression,
    generate_token_density_chart,
    purity_nines_values,
    write_figure_quality_report,
)


def _write_representative_config(tmp_path):
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "config.yaml").write_text(
        "\n".join(
            [
                "paper:",
                "  title: Test",
                "gold_refinement:",
                "  lexicon:",
                "    metallurgical_terms: [cupellation, assaying]",
                "    manuscript_terms: [draft, claim]",
                "    purity_adjectives: [refined, certified]",
                "    refinement_verbs: [assay, certify]",
                "  slots:",
                "    - name: METHOD_METAL_TERM",
                "      category: metallurgical_terms",
                "      count: 1",
                "      section: methodology",
                "  contribution_claims:",
                "    - name: Pipeline mapping",
                "      claim: Configured claims are assayed against local evidence.",
                "      evidence: manuscript/config.yaml",
                "      boundary: local template exemplar",
                "",
            ]
        ),
        encoding="utf-8",
    )


class TestFigureSpecContract:
    def test_figure_specs_are_unique(self):
        assert len(FIGURE_SPECS) == 12
        for field in ("name", "label", "path", "svg_path"):
            values = [getattr(spec, field) for spec in FIGURE_SPECS]
            assert len(values) == len(set(values)), f"duplicate figure spec {field}"

    def test_registry_payload_matches_specs(self):
        payload = figure_registry_payload()
        figures = payload["figures"]
        assert len(figures) == len(FIGURE_SPECS)
        required = {
            "name",
            "label",
            "path",
            "svg_path",
            "caption",
            "generated_by",
            "data_sources",
            "visual_encoding",
        }
        for record in figures:
            assert required <= set(record)
            assert record["path"].endswith(".png")
            assert record["svg_path"].endswith(".svg")
            assert record["generated_by"].startswith("src/figures.py::")

    def test_graph_figure_specs_name_graph_encodings(self):
        encodings = {spec.name: spec.visual_encoding for spec in FIGURE_SPECS}
        for name in (
            "provenance_sankey",
            "formalism_traceability",
            "implementation_circuit",
            "claim_evidence_assay",
        ):
            assert "graph" in encodings[name]


class TestGraphTopologyContracts:
    def test_provenance_flow_graph_shape(self):
        graph, edge_widths = build_provenance_flow_graph()
        assert graph.number_of_nodes() == 6
        assert graph.number_of_edges() == 5
        assert len(edge_widths) == 5
        assert "ore" in graph

    def test_formalism_traceability_graph_shape(self):
        graph = build_formalism_traceability_graph()
        assert graph.number_of_nodes() == 18
        assert graph.number_of_edges() == 12
        assert sum(1 for _, data in graph.nodes(data=True) if data["kind"] == "formalism") == 6

    def test_implementation_circuit_graph_shape(self):
        graph = build_implementation_circuit_graph()
        assert graph.number_of_nodes() == 8
        assert graph.number_of_edges() == 9
        assert graph.nodes["figures"]["label"].endswith("PNG + SVG registry")

    def test_claim_evidence_topology_shape(self):
        class Entry:
            claim_name = "Local claim"
            evidence_source = "src/refinery.py::run_refinery"
            boundary = "local template"
            supported = True

        graph = build_claim_evidence_topology([Entry()])
        assert graph.number_of_nodes() == 3
        assert graph.number_of_edges() == 2
        assert {data["kind"] for _, data in graph.nodes(data=True)} == {"claim", "evidence", "boundary"}


class TestPurityTransform:
    def test_nines_transform_expands_late_stage_gain(self):
        values = purity_nines_values((0.9, 0.99, 0.999999999))
        assert values == sorted(values)
        assert values[-1] > values[0] * 8


class TestPurityProgressionFigure:
    def test_generates_png(self, tmp_path):
        out = generate_purity_progression(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100  # non-blank

    def test_uses_project_root(self, tmp_path):
        # Create a minimal project structure
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "output").mkdir()
        out = generate_purity_progression(project_root=tmp_path)
        assert out.exists()
        assert "figures" in str(out)


class TestKaratGradingFigure:
    def test_generates_png(self, tmp_path):
        out = generate_karat_grading_chart(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100


class TestTokenDensityFigure:
    def test_generates_png_with_data(self, tmp_path):
        # Provide token plan data directly
        data = {
            "section_counts": {"methodology": 5, "results": 2, "discussion": 1},
            "category_counts": {"metallurgical_terms": 3, "manuscript_terms": 2},
        }
        out = generate_token_density_chart(tmp_path, token_plan_data=data)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_generates_png_without_data(self, tmp_path):
        out = generate_token_density_chart(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"

    def test_generates_png_with_empty_section_and_category_counts(self, tmp_path):
        """Chart handles empty section_counts and category_counts gracefully."""
        data = {
            "section_counts": {},
            "category_counts": {},
        }
        out = generate_token_density_chart(tmp_path, token_plan_data=data)
        assert out.exists()
        assert out.suffix == ".png"

    def test_token_density_with_project_root_none_output_dir(self, tmp_path):
        """token_density with output_dir=None and project_root uses project_root path."""
        (tmp_path / "manuscript").mkdir()
        out = generate_token_density_chart(output_dir=None, project_root=tmp_path)
        assert out.exists()
        assert "figures" in str(out)


class TestGenerateAllFigures:
    def test_generates_all_figures(self, tmp_path):
        _write_representative_config(tmp_path)
        paths = generate_all_figures(tmp_path)
        assert len(paths) == 12
        for p in paths:
            assert p.exists()
            assert p.suffix == ".png"
            assert p.stat().st_size > 100
            svg_path = p.with_suffix(".svg")
            assert svg_path.exists()
            assert svg_path.stat().st_size > 100

    def test_writes_figure_registry(self, tmp_path):
        _write_representative_config(tmp_path)
        generate_all_figures(tmp_path)
        registry_path = tmp_path / "output" / "figures" / "figure_registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        assert "figures" in registry
        assert len(registry["figures"]) == 12
        for fig in registry["figures"]:
            assert fig["svg_path"].endswith(".svg")
            assert fig["data_sources"]
            assert fig["visual_encoding"]
        labels = [f["label"] for f in registry["figures"]]
        assert "fig:purity_progression" in labels
        assert "fig:karat_grading" in labels
        assert "fig:token_density" in labels
        assert "fig:integrity_gate_matrix" in labels
        assert "fig:formalism_traceability" in labels
        assert "fig:implementation_circuit" in labels
        assert "fig:claim_evidence_assay" in labels
        assert "fig:integrity_risk_matrix" in labels
        assert "fig:evidence_tier_ladder" in labels

    def test_writes_figure_quality_report(self, tmp_path):
        _write_representative_config(tmp_path)
        generate_all_figures(tmp_path)
        quality_path = tmp_path / "output" / "reports" / "figure_quality_report.json"
        assert quality_path.exists()
        report = json.loads(quality_path.read_text(encoding="utf-8"))
        assert report["schema"] == "template-gold-refinement-figure-quality-v1"
        assert report["figure_count"] == 12
        assert report["png_count"] == 12
        assert report["svg_count"] == 12
        assert report["registry_parity"] is True
        assert report["passing_count"] == 12
        for record in report["records"]:
            assert record["width_px"] >= 900
            assert record["height_px"] >= 600
            assert record["nonwhite_fraction"] > 0.01
            assert record["color_variance"] > 0.00001

    def test_quality_report_detects_missing_svg(self, tmp_path):
        _write_representative_config(tmp_path)
        generate_all_figures(tmp_path)
        first_svg = tmp_path / "output" / "figures" / FIGURE_SPECS[0].svg_path
        first_svg.unlink()
        quality_path = write_figure_quality_report(tmp_path)
        report = json.loads(quality_path.read_text(encoding="utf-8"))
        assert report["svg_count"] == 11
        assert report["passing_count"] == 11


class TestStageConstants:
    def test_stage_colors_length(self):
        assert len(STAGE_COLORS) == 5

    def test_stage_labels_length(self):
        assert len(STAGE_LABELS) == 5

    def test_stage_labels_content(self):
        assert STAGE_LABELS[0] == "Ore"
        assert STAGE_LABELS[4] == "Certification"


class TestAdditionalFigures:
    """Tests for provenance_sankey, purity_claim_scatter, token_heatmap."""

    def test_provenance_sankey_generates_png(self, tmp_path):
        from figures import generate_provenance_sankey
        out = generate_provenance_sankey(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_purity_claim_scatter_generates_png(self, tmp_path):
        from figures import generate_purity_claim_scatter
        out = generate_purity_claim_scatter(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_token_heatmap_generates_png(self, tmp_path):
        from figures import generate_token_heatmap
        (tmp_path / "manuscript").mkdir()
        out = generate_token_heatmap(tmp_path, project_root=tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_token_heatmap_with_unused_category(self, tmp_path):
        """Heatmap handles categories with no tokens (vals empty) gracefully."""
        import yaml
        (tmp_path / "manuscript").mkdir()
        # Config with a lexicon category that has no matching slot
        (tmp_path / "manuscript" / "config.yaml").write_text(
            yaml.dump({
                "gold_refinement": {
                    "seed": 1,
                    "composition_depth": "compact",
                    "lexicon": {
                        "metallurgical_terms": ["cupellation", "assaying"],
                        "manuscript_terms": ["draft", "claim"],
                        "purity_adjectives": ["refined", "pure"],
                        "refinement_verbs": ["smelt", "certify"],
                        "unused_category": ["alpha", "beta"],
                    },
                    "slots": [
                        # Only uses metallurgical_terms — unused_category has no slot
                        {"name": "SLOT_A", "category": "metallurgical_terms", "count": 1, "section": "methodology"},
                    ],
                }
            }),
            encoding="utf-8",
        )
        from figures import generate_token_heatmap
        out = generate_token_heatmap(tmp_path, project_root=tmp_path)
        assert out.exists()
        assert out.stat().st_size > 100

    def test_integrity_gate_matrix_generates_png(self, tmp_path):
        (tmp_path / "manuscript").mkdir()
        out = generate_integrity_gate_matrix(tmp_path, project_root=tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_formalism_traceability_generates_png(self, tmp_path):
        out = generate_formalism_traceability(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_implementation_circuit_generates_png(self, tmp_path):
        out = generate_implementation_circuit(tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_claim_evidence_assay_generates_png(self, tmp_path):
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Test\n", encoding="utf-8"
        )
        out = generate_claim_evidence_assay(tmp_path, project_root=tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_integrity_risk_matrix_generates_png(self, tmp_path):
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Test\n", encoding="utf-8"
        )
        out = generate_integrity_risk_matrix(tmp_path, project_root=tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100

    def test_evidence_tier_ladder_generates_png(self, tmp_path):
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Test\n", encoding="utf-8"
        )
        out = generate_evidence_tier_ladder(tmp_path, project_root=tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 100
