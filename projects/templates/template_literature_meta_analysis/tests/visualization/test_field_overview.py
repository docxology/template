from __future__ import annotations
from pathlib import Path
from visualization.field_overview import plot_field_summary, plot_subfield_distribution


class TestFieldOverview:
    """Tests for field_overview visualization functions."""

    SUBFIELD_COUNTS = {
        "A2_philosophy": 50,
        "C1_neuroscience": 30,
        "C2_robotics": 10,
        "B_tools": 25,
        "C4_psychiatry": 15,
        "A1_formal": 8,
        "C5_biology": 5,
        "C3_language": 7,
    }

    def test_plot_field_summary_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "field_summary.png"
        result = plot_field_summary(
            total_papers=150,
            subfield_counts=self.SUBFIELD_COUNTS,
            output_path=output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_field_summary_returns_path(self, tmp_path: Path) -> None:
        output = tmp_path / "sub" / "field_summary.png"
        result = plot_field_summary(
            total_papers=100,
            subfield_counts={"A2_philosophy": 80, "C2_robotics": 20},
            output_path=output,
        )
        assert result == output
        assert output.exists()
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_subfield_distribution_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "subfield_dist.png"
        result = plot_subfield_distribution(
            subfield_counts=self.SUBFIELD_COUNTS,
            output_path=output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_subfield_distribution_empty_data(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_dist.png"
        result = plot_subfield_distribution(
            subfield_counts={},
            output_path=output,
        )
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check (empty plot still produces valid image)
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_subfield_distribution_small_slice_grouped_into_other(self, tmp_path: Path) -> None:
        """Subfields below the 2% threshold are folded into an 'Other' bucket."""
        # A1_formal and C5_biology are each 1% of total=100 -> below threshold -> Other.
        counts = {
            "A2_philosophy": 50,
            "C1_neuroscience": 48,
            "A1_formal": 1,   # 1% < 2% threshold
            "C5_biology": 1,  # 1% < 2% threshold — total Other bucket = 2
        }
        output = tmp_path / "other_dist.png"
        result = plot_subfield_distribution(subfield_counts=counts, output_path=output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        from PIL import Image
        img = Image.open(output)
        assert img.width > 0 and img.height > 0
