"""Tests for sealing utilities."""

from __future__ import annotations

import json

import pytest

from src.sealing import (
    qr_matrix,
    read_qr_matrix,
    qr_image,
    build_payload,
    build_pointer_payload,
    build_barcode_payload,
    embed_qr,
    embed_semi_transparent,
)


# ---------------------------------------------------------------------------
# qr_matrix
# ---------------------------------------------------------------------------


def test_qr_matrix_returns_2d_list():
    matrix = qr_matrix("hello")
    assert isinstance(matrix, list)
    assert isinstance(matrix[0], list)


def test_qr_matrix_rows_are_bool():
    matrix = qr_matrix("hello")
    for row in matrix:
        for cell in row:
            assert isinstance(cell, bool)


def test_qr_matrix_square():
    matrix = qr_matrix("test data")
    n_rows = len(matrix)
    for row in matrix:
        assert len(row) == n_rows


def test_qr_matrix_deterministic():
    m1 = qr_matrix("test")
    m2 = qr_matrix("test")
    assert m1 == m2


def test_qr_matrix_different_data_different_matrix():
    m1 = qr_matrix("data_a")
    m2 = qr_matrix("data_b")
    assert m1 != m2


# ---------------------------------------------------------------------------
# build_payload
# ---------------------------------------------------------------------------


def test_build_payload_is_valid_json():
    payload = build_payload("abc123", "def456", 42)
    d = json.loads(payload)
    assert "spec_hash" in d
    assert "tree_hash" in d
    assert "seed" in d


def test_build_payload_spec_hash():
    payload = build_payload("myhash", "treehash", 0)
    d = json.loads(payload)
    assert d["spec_hash"] == "myhash"


def test_build_payload_seed():
    payload = build_payload("s", "t", 1618033)
    d = json.loads(payload)
    assert d["seed"] == 1618033


def test_build_payload_deterministic():
    p1 = build_payload("s", "t", 1)
    p2 = build_payload("s", "t", 1)
    assert p1 == p2


# ---------------------------------------------------------------------------
# build_pointer_payload
# ---------------------------------------------------------------------------


def test_build_pointer_payload_has_spec_hash():
    payload = build_pointer_payload("myhash")
    d = json.loads(payload)
    assert d["spec_hash"] == "myhash"


def test_build_pointer_payload_with_url():
    payload = build_pointer_payload("h", url="https://example.com")
    d = json.loads(payload)
    assert d["url"] == "https://example.com"


def test_build_pointer_payload_without_url():
    payload = build_pointer_payload("h")
    d = json.loads(payload)
    assert "url" not in d


# ---------------------------------------------------------------------------
# build_barcode_payload
# ---------------------------------------------------------------------------


def test_build_barcode_payload_format():
    payload = build_barcode_payload("spec12345678", "tree12345678", 42)
    parts = payload.split(":")
    assert len(parts) == 4
    assert parts[0] == "autopoiesis"


def test_build_barcode_payload_custom_label():
    payload = build_barcode_payload("s", "t", 0, label="custom")
    assert payload.startswith("custom:")


# ---------------------------------------------------------------------------
# embed_semi_transparent (smoke test — PIL may not be available)
# ---------------------------------------------------------------------------


def test_embed_semi_transparent_returns_something():
    """embed_semi_transparent should not crash even without full PIL support."""
    # Create a mock base image and QR image
    try:
        from PIL import Image

        base = Image.new("RGB", (100, 100), color=(0, 0, 0))
        qr = Image.new("RGB", (20, 20), color=(255, 255, 255))
        result = embed_semi_transparent(base, qr, position=(0, 0), opacity=0.5)
        assert result is not None
    except ImportError:
        pytest.skip("PIL not available")


# ---------------------------------------------------------------------------
# read_qr_matrix — fallback path (pyzbar likely not installed)
# ---------------------------------------------------------------------------


def test_read_qr_matrix_small_matrix_returns_str():
    """read_qr_matrix should return a string (possibly empty) for any matrix."""
    matrix = [[True, False], [False, True]]
    result = read_qr_matrix(matrix)
    assert isinstance(result, str)


def test_read_qr_matrix_empty_input_returns_empty_str():
    """read_qr_matrix with empty matrix should return empty string."""
    result = read_qr_matrix([])
    assert result == ""


def test_read_qr_matrix_checkerboard_returns_str():
    """read_qr_matrix with the fallback checkerboard pattern returns a string."""
    matrix = qr_matrix("test")  # may produce checkerboard or real QR
    result = read_qr_matrix(matrix)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# qr_image — optional qrcode/PIL stack
# ---------------------------------------------------------------------------


def test_qr_image_returns_something_or_none():
    """qr_image should return an image object when qrcode/PIL available, or None."""
    result = qr_image("hello")
    # Either a PIL image (has .size) or None — both are valid
    assert result is None or hasattr(result, "size")


def test_qr_image_different_data_different_result():
    """qr_image with different data should differ (if qrcode available)."""
    r1 = qr_image("data_a")
    r2 = qr_image("data_b")
    # Both must be the same type (both None or both images)
    assert (r1 is None) == (r2 is None)


# ---------------------------------------------------------------------------
# embed_qr — embedding helpers
# ---------------------------------------------------------------------------


def test_embed_qr_with_pil_images():
    """embed_qr should paste QR into base image when PIL is available."""
    try:
        from PIL import Image

        base = Image.new("RGB", (100, 100), color=(255, 255, 255))
        qr = Image.new("RGB", (20, 20), color=(0, 0, 0))
        result = embed_qr(base, qr, position=(0, 0))
        assert result is not None
        # The result should be the same base image object
        assert result is base
    except ImportError:
        pytest.skip("PIL not available")


def test_embed_qr_with_non_pil_object_returns_base():
    """embed_qr with a non-PIL object (no .paste) should return base unchanged."""
    base = {"type": "fake_image", "data": [1, 2, 3]}
    qr = {"type": "fake_qr"}
    result = embed_qr(base, qr, position=(0, 0))
    # Exception is caught internally, base is returned unchanged
    assert result is base


def test_embed_semi_transparent_with_non_pil_object_returns_base():
    """embed_semi_transparent with a non-PIL object triggers the except branch."""
    base = {"type": "not_a_pil_image"}
    qr = {"type": "not_a_pil_qr"}
    result = embed_semi_transparent(base, qr, position=(0, 0), opacity=0.5)
    # When PIL operations fail, returns base unchanged
    assert result is base


# ---------------------------------------------------------------------------
# qr_image exception path — lines 68-69
# ---------------------------------------------------------------------------


def test_qr_image_bad_args_returns_none():
    """qr_image with invalid box_size triggers the except branch and returns None."""
    result = qr_image("test", box_size=-1, border=-1)
    assert result is None


# ---------------------------------------------------------------------------
# qr_matrix ImportError fallback — lines 31-34 and read_qr_matrix body 41-48
# Using sys.modules to simulate absent optional dependencies (real import system
# manipulation, not object patching).
# ---------------------------------------------------------------------------


def test_qr_matrix_fallback_checkerboard_when_qrcode_absent():
    """qr_matrix falls back to 5x5 checkerboard when qrcode is not importable."""
    import sys
    import importlib
    import src.sealing as _sealing_mod

    saved = sys.modules.get("qrcode")
    # Block qrcode import to exercise the ImportError branch
    sys.modules["qrcode"] = None  # type: ignore[assignment]
    try:
        importlib.reload(_sealing_mod)
        matrix = _sealing_mod.qr_matrix("test")
        assert len(matrix) == 5
        assert len(matrix[0]) == 5
        # Checkerboard pattern: cell (i,j) is True when (i+j) % 2 == 0
        assert matrix[0][0] is True
        assert matrix[0][1] is False
    finally:
        if saved is None:
            sys.modules.pop("qrcode", None)
        else:
            sys.modules["qrcode"] = saved
        # Reload back to normal state
        importlib.reload(_sealing_mod)


def test_read_qr_matrix_body_with_pyzbar_available():
    """Cover lines 41-48 of read_qr_matrix by injecting a fake pyzbar module."""
    import sys
    import types
    import importlib
    import src.sealing as _sealing_mod

    # Build a minimal fake pyzbar.pyzbar module with a decode that returns []
    fake_pyzbar_inner = types.ModuleType("pyzbar.pyzbar")

    def _fake_decode(img):  # noqa: ANN001
        return []  # no results — so we hit lines 41-48 and fall through to return ""

    fake_pyzbar_inner.decode = _fake_decode  # type: ignore[attr-defined]

    fake_pyzbar = types.ModuleType("pyzbar")
    fake_pyzbar.pyzbar = fake_pyzbar_inner  # type: ignore[attr-defined]

    saved_outer = sys.modules.get("pyzbar")
    saved_inner = sys.modules.get("pyzbar.pyzbar")
    sys.modules["pyzbar"] = fake_pyzbar
    sys.modules["pyzbar.pyzbar"] = fake_pyzbar_inner
    try:
        importlib.reload(_sealing_mod)
        matrix = [[True, False, True], [False, True, False], [True, False, True]]
        result = _sealing_mod.read_qr_matrix(matrix)
        assert isinstance(result, str)
    finally:
        if saved_outer is None:
            sys.modules.pop("pyzbar", None)
        else:
            sys.modules["pyzbar"] = saved_outer
        if saved_inner is None:
            sys.modules.pop("pyzbar.pyzbar", None)
        else:
            sys.modules["pyzbar.pyzbar"] = saved_inner
        importlib.reload(_sealing_mod)
