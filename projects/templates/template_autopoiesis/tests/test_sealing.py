"""Tests for sealing utilities."""
from __future__ import annotations

import json

import pytest

from src.sealing import (
    qr_matrix,
    build_payload,
    build_pointer_payload,
    build_barcode_payload,
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
