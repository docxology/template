from __future__ import annotations

from visualization.style import VIZ_CONFIG


class TestVizConfig:
    """Tests for the VIZ_CONFIG dictionary."""

    def test_config_has_required_keys(self) -> None:
        required = [
            "figure_size",
            "dpi",
            "font_size",
            "title_size",
            "palette",
            "subfield_colors",
            "grid_alpha",
            "edge_color",
        ]
        for key in required:
            assert key in VIZ_CONFIG, f"Missing key: {key}"

    def test_palette_has_eight_colors(self) -> None:
        assert len(VIZ_CONFIG["palette"]) == 8

    def test_subfield_colors_covers_all_domains(self) -> None:
        expected_domains = [
            "A2_philosophy",
            "A1_formal",
            "B_tools",
            "C1_neuroscience",
            "C2_robotics",
            "C3_language",
            "C4_psychiatry",
            "C5_biology",
        ]
        for sf in expected_domains:
            assert sf in VIZ_CONFIG["subfield_colors"]
