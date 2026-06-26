"""Tests for src.figures — figure generation for the gold-refinement exemplar."""

from __future__ import annotations

import json

from figures import (
    STAGE_COLORS,
    STAGE_LABELS,
    generate_all_figures,
    generate_karat_grading_chart,
    generate_purity_progression,
    generate_token_density_chart,
)


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
    def test_generates_all_three(self, tmp_path):
        # Create a minimal project structure
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Test\n", encoding="utf-8"
        )
        paths = generate_all_figures(tmp_path)
        assert len(paths) == 6
        for p in paths:
            assert p.exists()
            assert p.suffix == ".png"
            assert p.stat().st_size > 100

    def test_writes_figure_registry(self, tmp_path):
        (tmp_path / "manuscript").mkdir()
        (tmp_path / "manuscript" / "config.yaml").write_text(
            "paper:\n  title: Test\n", encoding="utf-8"
        )
        generate_all_figures(tmp_path)
        registry_path = tmp_path / "output" / "figures" / "figure_registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        assert "figures" in registry
        assert len(registry["figures"]) == 6
        labels = [f["label"] for f in registry["figures"]]
        assert "fig:purity_progression" in labels
        assert "fig:karat_grading" in labels
        assert "fig:token_density" in labels


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
