from __future__ import annotations
from pathlib import Path
from visualization.hypothesis_charts import (
    plot_hypothesis_dashboard,
    plot_evidence_timeline,
    plot_assertion_type_breakdown,
    plot_assertion_summary,
)


class TestHypothesisCharts:
    """Tests for hypothesis dashboard and evidence timeline."""

    SCORES = {
        "PRIMARY_EFFICACY": 0.72,
        "OPTIMAL_PERFORMANCE": 0.45,
        "MECHANISTIC_BASIS": -0.15,
        "PROCESS_MODEL": 0.88,
        "SCALABILITY": -0.20,
        "CLINICAL_UTILITY": 0.55,
        "BIOLOGICAL_BASIS": 0.30,
        "DOMAIN_GENERALIZATION": 0.10,
    }

    def test_plot_hypothesis_dashboard_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "hypothesis_dashboard.png"
        result = plot_hypothesis_dashboard(self.SCORES, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_hypothesis_dashboard_small_data(self, tmp_path: Path) -> None:
        output = tmp_path / "small_dashboard.png"
        result = plot_hypothesis_dashboard(
            {"PRIMARY_EFFICACY": 0.7, "SCALABILITY": -0.2},
            output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_hypothesis_dashboard_all_positive(self, tmp_path: Path) -> None:
        output = tmp_path / "positive_dash.png"
        result = plot_hypothesis_dashboard(
            {"A": 0.5, "B": 0.8, "C": 0.3},
            output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_hypothesis_dashboard_all_negative(self, tmp_path: Path) -> None:
        output = tmp_path / "negative_dash.png"
        result = plot_hypothesis_dashboard(
            {"A": -0.5, "B": -0.8, "C": -0.3},
            output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
        # Additional check for non-blank figure using matplotlib
        import matplotlib.image as mpimg

        img_arr = mpimg.imread(output)
        assert img_arr.mean() > 0.01, "Figure appears blank"

    def test_plot_evidence_timeline_creates_file(self, tmp_path: Path) -> None:
        yearly = {
            "PRIMARY_EFFICACY": {2018: 0.3, 2019: 0.5, 2020: 0.6, 2021: 0.72},
            "SCALABILITY": {2018: -0.1, 2019: -0.15, 2020: -0.18, 2021: -0.20},
        }
        output = tmp_path / "evidence_timeline.png"
        result = plot_evidence_timeline(yearly, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_evidence_timeline_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_timeline.png"
        result = plot_evidence_timeline({}, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check (empty plot still produces valid image)
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_evidence_timeline_single_hypothesis(self, tmp_path: Path) -> None:
        yearly = {
            "PROCESS_MODEL": {2019: 0.4, 2020: 0.6, 2021: 0.75, 2022: 0.88},
        }
        output = tmp_path / "single_hyp_timeline.png"
        result = plot_evidence_timeline(yearly, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_assertion_type_breakdown_creates_file(self, tmp_path: Path) -> None:
        assertion_counts = {
            "PRIMARY_EFFICACY": {"supports": 50, "contradicts": 5, "neutral": 20},
            "OPTIMAL_PERFORMANCE": {"supports": 30, "contradicts": 10, "neutral": 40},
            "PROCESS_MODEL": {"supports": 80, "contradicts": 2, "neutral": 15},
        }
        output = tmp_path / "assertion_breakdown.png"
        result = plot_assertion_type_breakdown(assertion_counts, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_assertion_type_breakdown_single_hypothesis(self, tmp_path: Path) -> None:
        assertion_counts = {
            "SCALABILITY": {"supports": 10, "contradicts": 3, "neutral": 7},
        }
        output = tmp_path / "single_breakdown.png"
        result = plot_assertion_type_breakdown(assertion_counts, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_assertion_summary_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "assertion_summary.png"
        result = plot_assertion_summary(
            total_assertions=500,
            type_counts={"supports": 300, "contradicts": 50, "neutral": 150},
            hypothesis_counts={
                "PRIMARY_EFFICACY": 100,
                "OPTIMAL_PERFORMANCE": 80,
                "PROCESS_MODEL": 120,
                "SCALABILITY": 60,
                "CLINICAL_UTILITY": 40,
                "BIOLOGICAL_BASIS": 50,
                "DOMAIN_GENERALIZATION": 30,
                "MECHANISTIC_BASIS": 20,
            },
            output_path=output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_hypothesis_dashboard_empty_scores(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_dashboard.png"
        result = plot_hypothesis_dashboard({}, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0

    def test_plot_hypothesis_dashboard_uses_hypothesis_names_lookup(self, tmp_path: Path) -> None:
        output = tmp_path / "named_dashboard.png"
        result = plot_hypothesis_dashboard({"H1": 0.6, "H2": -0.2}, output)
        assert result == output
        assert output.exists()

    def test_plot_evidence_timeline_skips_empty_year_series(self, tmp_path: Path) -> None:
        yearly = {
            "PRIMARY_EFFICACY": {2020: 0.5},
            "EMPTY_HYP": {},
        }
        output = tmp_path / "partial_timeline.png"
        result = plot_evidence_timeline(yearly, output)
        assert result == output
        assert output.exists()

    def test_plot_assertion_type_breakdown_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_breakdown.png"
        result = plot_assertion_type_breakdown({}, output)
        assert result == output
        assert output.exists()

    def test_plot_assertion_summary_no_data_panels(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_summary.png"
        result = plot_assertion_summary(
            total_assertions=0,
            type_counts={},
            hypothesis_counts={},
            output_path=output,
        )
        assert result == output
        assert output.exists()

    def test_plot_assertion_summary_minimal(self, tmp_path: Path) -> None:
        output = tmp_path / "minimal_summary.png"
        result = plot_assertion_summary(
            total_assertions=10,
            type_counts={"supports": 7, "contradicts": 1, "neutral": 2},
            hypothesis_counts={"PRIMARY_EFFICACY": 10},
            output_path=output,
        )
        assert result == output
        assert output.exists()

    def test_plot_assertion_summary_types_without_hypotheses(self, tmp_path: Path) -> None:
        output = tmp_path / "types_only_summary.png"
        result = plot_assertion_summary(
            total_assertions=5,
            type_counts={"supports": 3, "neutral": 2},
            hypothesis_counts={},
            output_path=output,
        )
        assert result == output
        assert output.exists()

    def test_plot_hypothesis_dashboard_unknown_key_title_case(self, tmp_path: Path) -> None:
        output = tmp_path / "fallback_labels.png"
        result = plot_hypothesis_dashboard({"custom_metric": 0.25}, output)
        assert result == output
        assert output.exists()
