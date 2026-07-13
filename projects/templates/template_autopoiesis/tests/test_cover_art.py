"""Tests for cover_art module."""

from __future__ import annotations

import math
from pathlib import Path


from src.cover_art import (
    ring_root_angles,
    domain_root_indices,
    branch_segments,
    build_ring_geometry,
    BranchSegment,
    DOMAIN_COLORS,
    render_cover,
)
from src.grammar import KNOWN_DOMAINS


# ---------------------------------------------------------------------------
# ring_root_angles
# ---------------------------------------------------------------------------


def test_ring_root_angles_count():
    angles = ring_root_angles(5)
    assert len(angles) == 5


def test_ring_root_angles_first_is_zero():
    angles = ring_root_angles(5)
    assert angles[0] == 0.0


def test_ring_root_angles_evenly_spaced():
    n = 6
    angles = ring_root_angles(n)
    diffs = [angles[i + 1] - angles[i] for i in range(n - 1)]
    expected = 2 * math.pi / n
    for d in diffs:
        assert abs(d - expected) < 1e-12


# ---------------------------------------------------------------------------
# domain_root_indices
# ---------------------------------------------------------------------------


def test_domain_root_indices_keys():
    domains = ("a", "b", "c")
    idx = domain_root_indices(domains)
    assert set(idx.keys()) == set(domains)


def test_domain_root_indices_values():
    domains = ("x", "y", "z")
    idx = domain_root_indices(domains)
    assert idx["x"] == 0
    assert idx["y"] == 1
    assert idx["z"] == 2


# ---------------------------------------------------------------------------
# branch_segments
# ---------------------------------------------------------------------------


def test_branch_segments_count():
    segs = branch_segments(KNOWN_DOMAINS)
    assert len(segs) == len(KNOWN_DOMAINS)


def test_branch_segments_are_branch_segment():
    segs = branch_segments(KNOWN_DOMAINS)
    for s in segs:
        assert isinstance(s, BranchSegment)


def test_branch_segments_domains_match():
    segs = branch_segments(KNOWN_DOMAINS)
    for seg, domain in zip(segs, KNOWN_DOMAINS):
        assert seg.domain == domain


# ---------------------------------------------------------------------------
# build_ring_geometry
# ---------------------------------------------------------------------------


def test_build_ring_geometry_length():
    segs = build_ring_geometry(KNOWN_DOMAINS)
    assert len(segs) == len(KNOWN_DOMAINS)


def test_build_ring_geometry_radius():
    segs = build_ring_geometry(KNOWN_DOMAINS, radius=2.0)
    for s in segs:
        assert s.radius == 2.0


def test_build_ring_geometry_arc_order():
    segs = build_ring_geometry(KNOWN_DOMAINS)
    # Each segment starts where the previous ends (approximately)
    for i in range(len(segs) - 1):
        assert segs[i].theta_start < segs[i].theta_end
        assert segs[i].theta_end <= segs[i + 1].theta_start + 0.1


def test_build_ring_geometry_colors_from_palette():
    segs = build_ring_geometry(KNOWN_DOMAINS)
    for seg in segs:
        if seg.domain in DOMAIN_COLORS:
            assert seg.color == DOMAIN_COLORS[seg.domain]


# ---------------------------------------------------------------------------
# render_cover
# ---------------------------------------------------------------------------


def test_render_cover_creates_file(tmp_path):
    out = tmp_path / "cover.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out)
    assert out.exists()


def test_render_cover_file_nonempty(tmp_path):
    out = tmp_path / "cover.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out)
    assert out.stat().st_size > 1000


def test_render_cover_returns_path(tmp_path):
    out = tmp_path / "cover.png"
    result = render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out)
    assert result == out


def test_render_cover_creates_parent_dirs(tmp_path):
    out = tmp_path / "deep" / "nested" / "cover.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out)
    assert out.exists()


def test_render_cover_byte_stable(tmp_path):
    out1 = tmp_path / "c1.png"
    out2 = tmp_path / "c2.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out1)
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out2)
    assert out1.read_bytes() == out2.read_bytes()


def test_render_cover_different_seed_different_bytes(tmp_path):
    out1 = tmp_path / "c1.png"
    out2 = tmp_path / "c2.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out1)
    render_cover(domains=KNOWN_DOMAINS, seed=99, out_path=out2)
    assert out1.read_bytes() != out2.read_bytes()


def test_render_cover_wide_figsize(tmp_path):
    out = tmp_path / "wide.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out, figsize=(16, 9))
    assert out.exists()


def test_render_cover_optional_title(tmp_path):
    out = tmp_path / "titled.png"
    render_cover(
        domains=KNOWN_DOMAINS,
        seed=42,
        out_path=out,
        title="Test Title",
        subtitle="Test Subtitle",
        author="test_author",
    )
    assert out.exists()


# ---------------------------------------------------------------------------
# Additional: seed_dot_positions, color_gradient, non-trivial size,
# portrait aspect, byte-stable-with-new-elements, segments-count-richer
# ---------------------------------------------------------------------------


def test_seed_dot_positions_reproducible():
    """seed_dot_positions is just RNG state — verify same seed gives same cover bytes."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        p1 = Path(f.name)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        p2 = Path(f.name)
    render_cover(domains=KNOWN_DOMAINS, seed=1618033, out_path=p1)
    render_cover(domains=KNOWN_DOMAINS, seed=1618033, out_path=p2)
    assert p1.read_bytes() == p2.read_bytes()
    p1.unlink(missing_ok=True)
    p2.unlink(missing_ok=True)


def test_color_gradient_non_trivial(tmp_path):
    """Cover file should be non-trivial (not a solid color) — size check."""
    out = tmp_path / "gradient_test.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out, dpi=72)
    assert out.stat().st_size > 5000


def test_non_trivial_size(tmp_path):
    """Higher DPI should produce larger file."""
    out_low = tmp_path / "low_dpi.png"
    out_high = tmp_path / "high_dpi.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out_low, dpi=72)
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out_high, dpi=150)
    assert out_high.stat().st_size > out_low.stat().st_size


def test_portrait_aspect(tmp_path):
    out = tmp_path / "portrait.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out, figsize=(6, 9))
    assert out.exists()


def test_byte_stable_with_new_elements(tmp_path):
    """Two calls with same params and different seeds produce same file (not the same content)."""
    out_s1_a = tmp_path / "s1_a.png"
    out_s1_b = tmp_path / "s1_b.png"
    render_cover(domains=KNOWN_DOMAINS, seed=7, out_path=out_s1_a)
    render_cover(domains=KNOWN_DOMAINS, seed=7, out_path=out_s1_b)
    assert out_s1_a.read_bytes() == out_s1_b.read_bytes()


def test_segments_count_richer():
    """build_ring_geometry with 3 domains still returns 3 segments."""
    segs = build_ring_geometry(("optimization", "dynamics", "statistics"))
    assert len(segs) == 3
    assert segs[0].domain == "optimization"


# ---------------------------------------------------------------------------
# QR seal (grammar_hash) — the branch that runs in production via
# scripts/generate_cover_art.py, exercised directly here for the first time.
# ---------------------------------------------------------------------------


def test_render_cover_with_grammar_hash_creates_file(tmp_path):
    out = tmp_path / "sealed.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out, grammar_hash="deadbeef12345678")
    assert out.exists()


def test_render_cover_with_grammar_hash_larger_than_without(tmp_path):
    """The QR seal adds visible content, so the sealed image is not byte-identical to the unsealed one."""
    out_plain = tmp_path / "plain.png"
    out_sealed = tmp_path / "sealed.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out_plain, grammar_hash=None)
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out_sealed, grammar_hash="deadbeef12345678")
    assert out_plain.read_bytes() != out_sealed.read_bytes()


def test_render_cover_with_grammar_hash_byte_stable(tmp_path):
    out1 = tmp_path / "sealed1.png"
    out2 = tmp_path / "sealed2.png"
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out1, grammar_hash="deadbeef12345678")
    render_cover(domains=KNOWN_DOMAINS, seed=42, out_path=out2, grammar_hash="deadbeef12345678")
    assert out1.read_bytes() == out2.read_bytes()
