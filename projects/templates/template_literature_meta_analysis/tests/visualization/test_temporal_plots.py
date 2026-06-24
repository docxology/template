from __future__ import annotations
from pathlib import Path
from visualization.temporal_plots import plot_growth_curve, plot_subfield_timeline


class TestTemporalPlots:
    """Tests for temporal trend visualization functions."""

    YEAR_COUNTS = {2018: 5, 2019: 8, 2020: 12, 2021: 15, 2022: 22, 2023: 30}
    CUMULATIVE = {2018: 5, 2019: 13, 2020: 25, 2021: 40, 2022: 62, 2023: 92}

    def test_plot_growth_curve_creates_file(self, tmp_path: Path) -> None:
        output = tmp_path / "growth_curve.png"
        result = plot_growth_curve(self.YEAR_COUNTS, self.CUMULATIVE, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_growth_curve_single_year(self, tmp_path: Path) -> None:
        output = tmp_path / "single_year.png"
        result = plot_growth_curve({2023: 10}, {2023: 10}, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_subfield_timeline_creates_file(self, tmp_path: Path) -> None:
        subfield_data = {
            "A2_philosophy": {2018: 3, 2019: 5, 2020: 7, 2021: 8},
            "C1_neuroscience": {2018: 1, 2019: 2, 2020: 3, 2021: 5},
            "C2_robotics": {2018: 1, 2019: 1, 2020: 2, 2021: 2},
        }
        output = tmp_path / "subfield_timeline.png"
        result = plot_subfield_timeline(subfield_data, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_subfield_timeline_empty(self, tmp_path: Path) -> None:
        output = tmp_path / "empty_timeline.png"
        result = plot_subfield_timeline({}, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check (empty plot still produces valid image)
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0

    def test_plot_subfield_timeline_all_eight(self, tmp_path: Path) -> None:
        subfield_data = {
            "A2_philosophy": {2020: 10, 2021: 12},
            "B_tools": {2020: 5, 2021: 8},
            "C2_robotics": {2020: 3, 2021: 4},
            "C1_neuroscience": {2020: 7, 2021: 9},
            "C4_psychiatry": {2020: 4, 2021: 5},
            "A1_formal": {2020: 2, 2021: 3},
            "C5_biology": {2020: 1, 2021: 2},
            "C3_language": {2020: 1, 2021: 2},
        }
        output = tmp_path / "all_subfields.png"
        result = plot_subfield_timeline(subfield_data, output)
        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0
        # Content validation: PIL check
        from PIL import Image

        img = Image.open(output)
        assert img.width > 0 and img.height > 0
