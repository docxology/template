"""Tests for ``newspaper.visualization``."""

import json

import matplotlib.image as mpimg
import numpy as np
import pytest

from newspaper.visualization import (
    configure_matplotlib_bw_style,
    load_manuscript_stats,
    render_wordcount_bar_chart_bw,
    render_wordcount_chart_from_stats_file,
    wordcount_pairs_from_manuscript_stats,
)


def test_wordcount_pairs_from_manuscript_stats() -> None:
    data = {
        "project": "x",
        "files": [
            {"path": "manuscript/01_front_page.md", "words": 42, "lines": 1, "bytes": 10},
            {"path": "manuscript/02_national.md", "words": 7, "lines": 1, "bytes": 5},
        ],
    }
    pairs = wordcount_pairs_from_manuscript_stats(data)
    assert pairs == [("01_front_page", 42), ("02_national", 7)]


def test_wordcount_pairs_empty_files() -> None:
    assert wordcount_pairs_from_manuscript_stats({}) == []
    assert wordcount_pairs_from_manuscript_stats({"files": []}) == []


def test_wordcount_pairs_skips_non_dict_and_bad_types() -> None:
    data = {
        "files": [
            "not-a-dict",
            {"path": 1, "words": 5},
            {"path": "m/x.md", "words": "many"},
            {"path": "m/y.md", "words": 9},
        ]
    }
    assert wordcount_pairs_from_manuscript_stats(data) == [("y", 9)]


def test_load_manuscript_stats_roundtrip(tmp_path) -> None:
    p = tmp_path / "manuscript_stats.json"
    payload = {"project": "p", "files": [{"path": "m/a.md", "words": 1, "lines": 1, "bytes": 2}]}
    p.write_text(json.dumps(payload), encoding="utf-8")
    assert load_manuscript_stats(p)["project"] == "p"


def test_load_manuscript_stats_rejects_non_object(tmp_path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("[1,2]", encoding="utf-8")
    with pytest.raises(ValueError, match="object"):
        load_manuscript_stats(p)


def test_render_wordcount_bar_chart_empty_entries(tmp_path) -> None:
    out = tmp_path / "empty.png"
    render_wordcount_bar_chart_bw(out, [], dpi=80)
    assert out.is_file()
    assert out.stat().st_size > 200


def test_render_wordcount_bar_chart_writes_file(tmp_path) -> None:
    out = tmp_path / "wc.png"
    entries = [("a", 10), ("b", 30), ("c", 20)]
    render_wordcount_bar_chart_bw(out, entries, dpi=100)
    assert out.is_file()
    assert out.stat().st_size > 800


def test_render_wordcount_bar_chart_deterministic(tmp_path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    entries = [("x", 100), ("y", 200)]
    render_wordcount_bar_chart_bw(a, entries, dpi=80)
    render_wordcount_bar_chart_bw(b, entries, dpi=80)
    assert a.read_bytes() == b.read_bytes()


def test_render_wordcount_bar_chart_grayscale_pixels(tmp_path) -> None:
    out = tmp_path / "g.png"
    render_wordcount_bar_chart_bw(out, [("stem", 50), ("other", 120)], dpi=120)
    img = mpimg.imread(out)
    assert img.ndim == 3
    rgb = img[:, :, :3]
    # Antialiasing may introduce tiny channel skew; keep tolerance loose.
    assert float(np.max(np.abs(rgb[:, :, 0] - rgb[:, :, 1]))) < 0.06
    assert float(np.max(np.abs(rgb[:, :, 1] - rgb[:, :, 2]))) < 0.06


def test_render_from_stats_file(tmp_path) -> None:
    stats = tmp_path / "manuscript_stats.json"
    stats.write_text(
        json.dumps(
            {
                "project": "t",
                "files": [{"path": "manuscript/01_front_page.md", "words": 5, "lines": 1, "bytes": 1}],
            }
        ),
        encoding="utf-8",
    )
    png = tmp_path / "out.png"
    render_wordcount_chart_from_stats_file(stats, png, dpi=100)
    assert png.is_file()


def test_configure_matplotlib_bw_style_idempotent() -> None:
    configure_matplotlib_bw_style()
    configure_matplotlib_bw_style()
    assert plt_rcparams_contains_bw_keys()


def plt_rcparams_contains_bw_keys() -> bool:
    import matplotlib.pyplot as plt

    return plt.rcParams["image.cmap"] == "gray"
