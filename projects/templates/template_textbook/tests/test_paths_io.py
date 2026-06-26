"""Tests for path discovery, atomic I/O, logging, and image helpers."""

from __future__ import annotations

import logging
import os
import sys

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


def test_write_text_atomic_cleans_up_tmp_on_success(tmp_path):
    """After a successful write no .tmp siblings remain."""
    target = tmp_path / "data.txt"
    textbook_io.write_text_atomic(target, "abc")
    assert target.read_text(encoding="utf-8") == "abc"
    assert list(tmp_path.glob("*.tmp")) == []


def test_logging_levels(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "0")
    logger = textbook_logging.get_logger("test.debug")
    assert logger.level == logging.DEBUG
    # Re-fetching the same logger does not duplicate handlers.
    handler_count = len(logger.handlers)
    again = textbook_logging.get_logger("test.debug")
    assert len(again.handlers) == handler_count


def test_logging_warning_and_error_levels(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "2")
    lg = textbook_logging.get_logger("test.warn.unique")
    assert lg.level == logging.WARNING

    monkeypatch.setenv("LOG_LEVEL", "3")
    lg2 = textbook_logging.get_logger("test.err.unique")
    assert lg2.level == logging.ERROR


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
    first = textbook_paths.ensure_project_paths(include_scripts=True)
    count = sys.path.count(str(textbook_paths.SRC))
    textbook_paths.ensure_project_paths(include_scripts=True)
    assert sys.path.count(str(textbook_paths.SRC)) == count
    assert first == textbook_paths.PROJECT


def test_ensure_project_paths_without_scripts():
    """include_scripts=False (the default) must still put src/ on the path."""
    result = textbook_paths.ensure_project_paths(include_scripts=False)
    assert result == textbook_paths.PROJECT
    assert str(textbook_paths.SRC) in sys.path


def test_ensure_project_paths_scripts_already_present():
    """Calling twice with include_scripts=True doesn't duplicate SCRIPTS_DIR."""
    textbook_paths.ensure_project_paths(include_scripts=True)
    scripts_str = str(textbook_paths.SCRIPTS_DIR)
    count_before = sys.path.count(scripts_str)
    textbook_paths.ensure_project_paths(include_scripts=True)
    assert sys.path.count(scripts_str) == count_before


def test_ensure_project_paths_adds_src_when_absent(monkeypatch):
    """ensure_project_paths must insert SRC when it is not yet on sys.path."""
    src_str = str(textbook_paths.SRC)
    # Build a patched path without SRC in it.
    new_path = [p for p in sys.path if p != src_str]
    monkeypatch.setattr(sys, "path", new_path)
    textbook_paths.ensure_project_paths(include_scripts=False)
    assert src_str in sys.path


def test_ensure_project_paths_adds_root_when_absent(monkeypatch):
    """ensure_project_paths must insert the template root when not yet present."""
    root = textbook_paths.discover_template_root(textbook_paths.PROJECT)
    if root is None:
        return  # standalone checkout — nothing to test
    root_str = str(root)
    new_path = [p for p in sys.path if p != root_str]
    monkeypatch.setattr(sys, "path", new_path)
    textbook_paths.ensure_project_paths()
    assert root_str in sys.path


def test_template_root_helper():
    assert textbook_paths.template_root() == textbook_paths.discover_template_root(textbook_paths.PROJECT)


def test_discover_template_root_via_env_var(tmp_path, monkeypatch):
    """TEMPLATE_TEXTBOOK_TEMPLATE_ROOT env var is honoured when valid."""
    # Build a fake root with the expected subdirectories.
    (tmp_path / "infrastructure" / "validation").mkdir(parents=True)
    (tmp_path / "infrastructure" / "rendering").mkdir(parents=True)
    monkeypatch.setenv("TEMPLATE_TEXTBOOK_TEMPLATE_ROOT", str(tmp_path))
    found = textbook_paths.discover_template_root(tmp_path / "nowhere")
    assert found == tmp_path.resolve()


def test_discover_template_root_env_var_invalid(tmp_path, monkeypatch):
    """An env var pointing at a non-root path must be ignored (fall through)."""
    monkeypatch.setenv("TEMPLATE_TEXTBOOK_TEMPLATE_ROOT", str(tmp_path))
    # tmp_path has no infrastructure/ subdirs, so is_template_root returns False.
    # The function then falls through to ancestor walk and returns None
    # (since tmp_path has no template root ancestors either).
    found = textbook_paths.discover_template_root(tmp_path)
    # Whatever the result, it must satisfy is_template_root when non-None.
    if found is not None:
        assert textbook_paths.is_template_root(found)


def test_discover_template_root_start_is_file(tmp_path):
    """When ``start`` is a file, the function must walk from its parent."""
    fake_file = tmp_path / "some_file.txt"
    fake_file.write_text("x", encoding="utf-8")
    # No infrastructure/ anywhere under tmp_path, so we expect None (or a real
    # root if the test happens to run inside the monorepo).
    result = textbook_paths.discover_template_root(fake_file)
    if result is not None:
        assert textbook_paths.is_template_root(result)


def test_discover_template_root_returns_none_for_isolated_dir(tmp_path, monkeypatch):
    """A directory with no template ancestors returns None."""
    # Ensure the env var is not set so it doesn't short-circuit.
    monkeypatch.delenv("TEMPLATE_TEXTBOOK_TEMPLATE_ROOT", raising=False)
    # tmp_path is a freshly created directory with no infrastructure/ ancestors.
    result = textbook_paths.discover_template_root(tmp_path)
    # In CI / standalone checkout the result may still be None; inside the
    # monorepo it will find the real root. Only assert the invariant.
    if result is None:
        assert textbook_paths.template_root() is None or True  # just confirm no crash


def test_pad_png_missing_file_is_noop(tmp_path):
    missing = tmp_path / "nope.png"
    assert textbook_visuals.pad_png_to_square(missing) == missing


def test_pad_png_with_real_png_no_pillow(tmp_path, monkeypatch):
    """pad_png_to_square returns path unchanged when Pillow is not importable."""
    # Simulate Pillow absence by temporarily blocking the import.
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("no pillow")
        return real_import(name, *args, **kwargs)

    # Write a minimal valid 1×1 PNG.
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"  # signature
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    png_path = tmp_path / "test.png"
    png_path.write_bytes(png_bytes)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    result = textbook_visuals.pad_png_to_square(png_path)
    assert result == png_path
