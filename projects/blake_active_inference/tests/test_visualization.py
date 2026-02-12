"""Tests for Blake Active Inference visualization module."""

import tempfile
from pathlib import Path
import pytest

# Import the visualization module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from visualization import (
    create_doors_of_perception_figure,
    create_fourfold_vision_figure,
    create_perception_action_cycle_figure,
    create_thematic_atlas_figure,
    create_newtons_sleep_figure,
    create_four_zoas_figure,
    create_temporal_horizons_figure,
    create_collective_jerusalem_figure,
    generate_all_figures,
    COLORS,
    FONTS,
)


class TestVisualizationModule:
    """Test suite for visualization functions."""
    
    def test_colors_palette_exists(self):
        """Verify the color palette is properly defined."""
        required_colors = [
            "external", "sensory", "active", "internal",
            "blanket", "background", "text",
            "vision_1", "vision_2", "vision_3", "vision_4",
            # Zoa colors
            "urizen", "urthona", "luvah", "tharmas",
            # State colors
            "pathology", "balanced", "rigid",
            # Collective colors
            "shared", "agent_1", "agent_2", "agent_3",
            # Temporal colors
            "fast", "mid", "slow", "deep",
            # Atlas
            "theme_line",
        ]
        for color_name in required_colors:
            assert color_name in COLORS, f"Missing color: {color_name}"
            assert COLORS[color_name].startswith("#"), f"Invalid color format: {color_name}"
    
    def test_doors_of_perception_figure_creates_figure(self):
        """Test that doors of perception figure is created successfully."""
        fig = create_doors_of_perception_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)
    
    def test_doors_of_perception_figure_saves_to_file(self):
        """Test that doors of perception figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_doors.png"
            fig = create_doors_of_perception_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)
    
    def test_fourfold_vision_figure_creates_figure(self):
        """Test that fourfold vision figure is created successfully."""
        fig = create_fourfold_vision_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)
    
    def test_fourfold_vision_figure_saves_to_file(self):
        """Test that fourfold vision figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_fourfold.png"
            fig = create_fourfold_vision_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)
    
    def test_perception_action_cycle_figure_creates_figure(self):
        """Test that perception-action cycle figure is created successfully."""
        fig = create_perception_action_cycle_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)
    
    def test_perception_action_cycle_figure_saves_to_file(self):
        """Test that perception-action cycle figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_cycle.png"
            fig = create_perception_action_cycle_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)
    
    def test_generate_all_figures_creates_all_outputs(self):
        """Test that generate_all_figures creates all expected figures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            figures = generate_all_figures(output_dir)

            # Check all 8 figures are returned
            expected_names = [
                "thematic_atlas",
                "doors_of_perception",
                "fourfold_vision",
                "perception_action_cycle",
                "newtons_sleep",
                "four_zoas",
                "temporal_horizons",
                "collective_jerusalem",
            ]
            for name in expected_names:
                assert name in figures, f"Missing figure: {name}"

            assert len(figures) == 8, f"Expected 8 figures, got {len(figures)}"

            # Check all files exist
            for name, path in figures.items():
                assert path.exists(), f"Figure {name} not created at {path}"
                assert path.stat().st_size > 0, f"Figure {name} is empty"
    
    def test_figure_custom_dimensions(self):
        """Test that custom figure dimensions are respected."""
        fig = create_doors_of_perception_figure(figsize=(8, 6))
        width, height = fig.get_size_inches()
        assert abs(width - 8) < 0.1
        assert abs(height - 6) < 0.1
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestBlakeQuotations:
    """Test that Blake quotations are properly sourced."""
    
    def test_doors_of_perception_source(self):
        """Verify the main quotation source is correct."""
        # This is a documentation test - the quotation attribution
        # should be: The Marriage of Heaven and Hell, Plate 14
        expected_source = "Marriage of Heaven and Hell"
        # Verify main quotation source
        import matplotlib.text
        import matplotlib.pyplot as plt

        fig = create_doors_of_perception_figure()
        found = False
        for text_obj in fig.findobj(matplotlib.text.Text):
            if expected_source in text_obj.get_text():
                found = True
                break
        plt.close(fig)
        
        assert found, f"Source '{expected_source}' not found in figure text"
    
    def test_fourfold_vision_source(self):
        """Verify the fourfold vision quotation source."""
        # Source: Letter to Thomas Butts, 22 November 1802
        expected_source = "Letter to Thomas Butts"
        # Verify fourfold vision quotation source
        import matplotlib.text
        import matplotlib.pyplot as plt

        fig = create_fourfold_vision_figure()
        found = False
        for text_obj in fig.findobj(matplotlib.text.Text):
            if expected_source in text_obj.get_text():
                found = True
                break
        plt.close(fig)
        
        assert found, f"Source '{expected_source}' not found in figure text"


class TestFontSizeEnforcement:
    """Ensure all figure text meets the 10pt minimum for print readability."""

    def test_doors_minimum_font_size(self):
        """All text in Figure 1 meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_doors_of_perception_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_fourfold_minimum_font_size(self):
        """All text in Figure 2 meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_fourfold_vision_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_cycle_minimum_font_size(self):
        """All text in Figure 3 meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_perception_action_cycle_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestThematicAtlasFigure:
    """Test suite for thematic atlas figure."""

    def test_creates_figure(self):
        """Test that thematic atlas figure is created successfully."""
        fig = create_thematic_atlas_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_saves_to_file(self):
        """Test that thematic atlas figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_atlas.png"
            fig = create_thematic_atlas_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_minimum_font_size(self):
        """All text in thematic atlas meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_thematic_atlas_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestNewtonsSleepFigure:
    """Test suite for Newton's Sleep figure."""

    def test_creates_figure(self):
        """Test that Newton's Sleep figure is created successfully."""
        fig = create_newtons_sleep_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_saves_to_file(self):
        """Test that Newton's Sleep figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_newtons_sleep.png"
            fig = create_newtons_sleep_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_minimum_font_size(self):
        """All text in Newton's Sleep meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_newtons_sleep_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestFourZoasFigure:
    """Test suite for Four Zoas figure."""

    def test_creates_figure(self):
        """Test that Four Zoas figure is created successfully."""
        fig = create_four_zoas_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_saves_to_file(self):
        """Test that Four Zoas figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_four_zoas.png"
            fig = create_four_zoas_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_minimum_font_size(self):
        """All text in Four Zoas meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_four_zoas_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestTemporalHorizonsFigure:
    """Test suite for Temporal Horizons figure."""

    def test_creates_figure(self):
        """Test that temporal horizons figure is created successfully."""
        fig = create_temporal_horizons_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_saves_to_file(self):
        """Test that temporal horizons figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_temporal.png"
            fig = create_temporal_horizons_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_minimum_font_size(self):
        """All text in temporal horizons meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_temporal_horizons_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestCollectiveJerusalemFigure:
    """Test suite for Collective Jerusalem figure."""

    def test_creates_figure(self):
        """Test that collective Jerusalem figure is created successfully."""
        fig = create_collective_jerusalem_figure()
        assert fig is not None
        assert hasattr(fig, "savefig")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_saves_to_file(self):
        """Test that collective Jerusalem figure saves correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_jerusalem.png"
            fig = create_collective_jerusalem_figure(output_path=output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            import matplotlib.pyplot as plt
            plt.close(fig)

    def test_minimum_font_size(self):
        """All text in collective Jerusalem meets 10pt minimum font size."""
        import matplotlib
        import matplotlib.text

        fig = create_collective_jerusalem_figure()
        for text_obj in fig.findobj(matplotlib.text.Text):
            if text_obj.get_text().strip():
                assert text_obj.get_fontsize() >= FONTS['quote'], \
                    (f"Font size {text_obj.get_fontsize()} below minimum "
                     f"{FONTS['quote']} for text: '{text_obj.get_text()[:30]}'")
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestUnicodeSubscripts:
    """Ensure figures use LaTeX math notation instead of Unicode subscripts."""

    def test_no_unicode_subscripts(self):
        """No Unicode subscripts in figure text -- use LaTeX math instead."""
        import matplotlib
        import matplotlib.text

        unicode_subscripts = '\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089'

        figs = [
            create_doors_of_perception_figure(),
            create_fourfold_vision_figure(),
            create_perception_action_cycle_figure(),
            create_thematic_atlas_figure(),
            create_newtons_sleep_figure(),
            create_four_zoas_figure(),
            create_temporal_horizons_figure(),
            create_collective_jerusalem_figure(),
        ]
        for fig in figs:
            for text_obj in fig.findobj(matplotlib.text.Text):
                text = text_obj.get_text()
                for char in unicode_subscripts:
                    assert char not in text, \
                        (f"Unicode subscript '{char}' found in text: "
                         f"'{text[:40]}'. Use LaTeX $_{{{char}}}$ instead.")
            import matplotlib.pyplot as plt
            plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
