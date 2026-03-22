"""Smoke test for package ``__init__`` exports."""

import newspaper as nw


def test_public_api_importable() -> None:
    assert nw.LAYOUT is not None
    assert len(nw.PAGE_SLICES) == 16
    assert callable(nw.render_masthead_png)
    assert callable(nw.render_layout_schematic_png)
    assert callable(nw.multicol_begin)
    assert callable(nw.fixture_copy)
    assert callable(nw.get_slice)
    assert nw.slice_count() == 16
    assert callable(nw.dateline)
    assert callable(nw.column_count_valid)
    assert len(nw.all_tracked_manuscript_basenames()) >= 18
