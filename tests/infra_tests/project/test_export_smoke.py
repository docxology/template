"""Tests for clean exemplar export smoke helpers."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.export_smoke import discover_import_targets


def test_discover_import_targets_finds_modules_packages_and_namespaces(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "standalone.py").write_text("VALUE = 1\n", encoding="utf-8")
    package = src / "package"
    package.mkdir()
    (package / "__init__.py").write_text("\n", encoding="utf-8")
    namespace = src / "namespace"
    namespace.mkdir()
    (namespace / "module.py").write_text("\n", encoding="utf-8")
    (src / "_private.py").write_text("\n", encoding="utf-8")
    (src / "not-valid.py").write_text("\n", encoding="utf-8")

    assert discover_import_targets(src) == ("namespace", "package", "standalone")


def test_discover_import_targets_fails_closed_for_missing_src(tmp_path: Path) -> None:
    assert discover_import_targets(tmp_path / "missing") == ()


def test_discover_import_targets_preserves_src_package_relative_imports(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("\n", encoding="utf-8")
    (src / "analysis.py").write_text("\n", encoding="utf-8")

    assert discover_import_targets(src) == ("src",)
