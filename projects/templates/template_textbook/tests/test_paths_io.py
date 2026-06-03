"""Tests for path discovery, atomic I/O, logging, and image helpers."""

from __future__ import annotations

import logging

import textbook_io
import textbook_logging
import textbook_paths
import textbook_visuals


def test_write_text_atomic_roundtrip(tmp_path):
    target = tmp_path / "nested" / "file.txt"
    written = textbook_io.write_text_atomic(target, "hello\nworld\n")
    assert written == target
    assert textbook_io.read_text(target) == "hello\nworld\n"
    # No leftover temp files.
    assert list(target.parent.glob("*.tmp")) == []


def test_write_text_atomic_overwrites(tmp_path):
    target = tmp_path / "f.txt"
    textbook_io.write_text_atomic(target, "one")
    textbook_io.write_text_atomic(target, "two")
    assert textbook_io.read_text(target) == "two"


def test_logging_levels(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "0")
    logger = textbook_logging.get_logger("test.debug")
    assert logger.level == logging.DEBUG
    # Re-fetching the same logger does not duplicate handlers.
    handler_count = len(logger.handlers)
    again = textbook_logging.get_logger("test.debug")
    assert len(again.handlers) == handler_count


def test_logging_default_level(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    logger = textbook_logging.get_logger("test.default")
    assert logger.level == logging.INFO


def test_is_template_root_and_discover():
    project = textbook_paths.PROJECT
    root = textbook_paths.discover_template_root(project)
    # Inside the template monorepo a root is discoverable; in a standalone
    # checkout there is no infrastructure/ parent and discovery returns None.
    # Both are valid — assert only that *when* a root is found it is a real one.
    if root is not None:
        assert textbook_paths.is_template_root(root)
        assert (root / "infrastructure" / "validation").is_dir()
    else:
        assert textbook_paths.template_root() is None


def test_is_template_root_false_for_tmp(tmp_path):
    assert textbook_paths.is_template_root(tmp_path) is False


def test_ensure_project_paths_idempotent():
    import sys

    first = textbook_paths.ensure_project_paths(include_scripts=True)
    count = sys.path.count(str(textbook_paths.SRC))
    textbook_paths.ensure_project_paths(include_scripts=True)
    assert sys.path.count(str(textbook_paths.SRC)) == count
    assert first == textbook_paths.PROJECT


def test_template_root_helper():
    assert textbook_paths.template_root() == textbook_paths.discover_template_root(textbook_paths.PROJECT)


def test_pad_png_missing_file_is_noop(tmp_path):
    missing = tmp_path / "nope.png"
    assert textbook_visuals.pad_png_to_square(missing) == missing
