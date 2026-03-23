"""Smoke test for package ``__init__`` exports."""

import newspaper as nw


def test_public_api_importable() -> None:
    assert nw.LAYOUT is not None
    assert len(nw.PAGE_SLICES) == 16
    assert callable(nw.render_masthead_png)
    assert callable(nw.render_layout_schematic_png)
    assert callable(nw.render_wordcount_bar_chart_bw)
    assert callable(nw.render_wordcount_chart_from_stats_file)
    assert callable(nw.wordcount_pairs_from_manuscript_stats)
    assert callable(nw.configure_matplotlib_bw_style)
    assert callable(nw.load_manuscript_stats)
    assert callable(nw.render_section_banner_bw)
    assert callable(nw.section_banner_filename)
    assert len(nw.section_banner_targets()) == 19
    assert "S01_layout_and_pipeline" in nw.OPTIONAL_MANUSCRIPT_STEM_TO_TITLE
    assert callable(nw.multicol_begin)
    assert callable(nw.fixture_copy)
    assert callable(nw.get_slice)
    assert nw.slice_count() == 16
    assert callable(nw.dateline)
    assert callable(nw.column_count_valid)
    assert len(nw.all_tracked_manuscript_basenames()) >= 20
