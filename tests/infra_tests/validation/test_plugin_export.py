#!/usr/bin/env python3
"""Tests for infrastructure.validation.plugin_export."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.plugin_export import compare_directories


def test_compare_directories_finds_only_in_first(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "only_left.txt").write_text("a\n")
    (left / "both.txt").write_text("same\n")
    (right / "both.txt").write_text("same\n")

    only1, only2, diff = compare_directories(left, right)
    assert only1 == {Path("only_left.txt")}
    assert only2 == set()
    assert diff == set()


def test_compare_directories_finds_content_diff(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "file.txt").write_text("one\n")
    (right / "file.txt").write_text("two\n")

    only1, only2, diff = compare_directories(left, right)
    assert only1 == set()
    assert only2 == set()
    assert diff == {Path("file.txt")}


def test_compare_directories_when_right_missing(tmp_path: Path) -> None:
    left = tmp_path / "left"
    left.mkdir()
    (left / "a.txt").write_text("x\n")
    right = tmp_path / "missing"

    only1, only2, diff = compare_directories(left, right)
    assert only1 == {Path("a.txt")}
    assert only2 == set()
    assert diff == set()
