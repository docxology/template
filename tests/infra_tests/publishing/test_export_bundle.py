#!/usr/bin/env python3
"""Tests for infrastructure.publishing.export_bundle.

No mocks: every test builds real files under ``tmp_path`` and exercises the
export pipeline on those real bytes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from infrastructure.publishing.export_bundle import (
    _collect_artifacts,
    _make_bundle_dir,
    _read_config,
    _resolve_project_root,
    _sha256,
    export_for_publishing,
    main,
)
from tests._support.projects import make_project, write_doc


# ---------------------------------------------------------------------------
# 1. _sha256
# ---------------------------------------------------------------------------


def test_sha256_matches_hashlib(tmp_path: Path) -> None:
    """_sha256 returns the same digest as hashlib.sha256 on the raw bytes."""
    content = b"hello export bundle\n" * 100
    path = tmp_path / "data.bin"
    path.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert _sha256(path) == expected


def test_sha256_empty_file(tmp_path: Path) -> None:
    """_sha256 handles a zero-byte file."""
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")
    assert _sha256(path) == hashlib.sha256(b"").hexdigest()


# ---------------------------------------------------------------------------
# 2. _collect_artifacts
# ---------------------------------------------------------------------------


def test_collect_artifacts_structure_and_hashes(tmp_path: Path) -> None:
    """_collect_artifacts returns dict with pdf/epub/metadata, each carrying sha256 + size_bytes."""
    output_root = tmp_path / "output"
    (output_root / "pdf").mkdir(parents=True)
    (output_root / "ebook").mkdir(parents=True)
    (output_root / "metadata").mkdir(parents=True)

    pdf_bytes = b"%PDF-1.4 test content\n"
    epub_bytes = b"PK epub content\n"
    json_bytes = b'{"title": "Test"}\n'

    pdf_path = output_root / "pdf" / "test.pdf"
    epub_path = output_root / "ebook" / "test.epub"
    json_path = output_root / "metadata" / "test.json"

    pdf_path.write_bytes(pdf_bytes)
    epub_path.write_bytes(epub_bytes)
    json_path.write_bytes(json_bytes)

    result = _collect_artifacts(output_root)

    assert set(result.keys()) == {"pdf", "epub", "metadata"}
    assert len(result["pdf"]) == 1
    assert len(result["epub"]) == 1
    assert len(result["metadata"]) == 1

    pdf_entry = result["pdf"][0]
    assert pdf_entry["filename"] == "test.pdf"
    assert pdf_entry["sha256"] == hashlib.sha256(pdf_bytes).hexdigest()
    assert pdf_entry["size_bytes"] == len(pdf_bytes)
    assert pdf_entry["source_path"] == str(pdf_path)

    epub_entry = result["epub"][0]
    assert epub_entry["filename"] == "test.epub"
    assert epub_entry["sha256"] == hashlib.sha256(epub_bytes).hexdigest()
    assert epub_entry["size_bytes"] == len(epub_bytes)

    meta_entry = result["metadata"][0]
    assert meta_entry["filename"] == "test.json"
    assert meta_entry["sha256"] == hashlib.sha256(json_bytes).hexdigest()
    assert meta_entry["size_bytes"] == len(json_bytes)


def test_collect_artifacts_empty_directories(tmp_path: Path) -> None:
    """Empty (or non-existent) sub-directories yield empty lists."""
    output_root = tmp_path / "output"
    (output_root / "pdf").mkdir(parents=True)
    result = _collect_artifacts(output_root)
    assert result == {"pdf": [], "epub": [], "metadata": []}


def test_collect_artifacts_skips_empty_files(tmp_path: Path) -> None:
    """Zero-byte files are excluded from collection."""
    output_root = tmp_path / "output"
    (output_root / "pdf").mkdir(parents=True)
    (output_root / "pdf" / "empty.pdf").write_bytes(b"")
    result = _collect_artifacts(output_root)
    assert result["pdf"] == []


def test_collect_artifacts_skips_wrong_extensions(tmp_path: Path) -> None:
    """Files with non-matching extensions are excluded."""
    output_root = tmp_path / "output"
    (output_root / "pdf").mkdir(parents=True)
    (output_root / "pdf" / "notes.txt").write_bytes(b"not a pdf")
    result = _collect_artifacts(output_root)
    assert result["pdf"] == []


def test_collect_artifacts_collects_mobi_and_xml(tmp_path: Path) -> None:
    """mobi files go in the epub bucket; xml/opf go in metadata."""
    output_root = tmp_path / "output"
    (output_root / "ebook").mkdir(parents=True)
    (output_root / "metadata").mkdir(parents=True)
    (output_root / "ebook" / "book.mobi").write_bytes(b"MOBI")
    (output_root / "metadata" / "meta.xml").write_bytes(b"<xml/>")
    result = _collect_artifacts(output_root)
    assert len(result["epub"]) == 1
    assert result["epub"][0]["filename"] == "book.mobi"
    assert len(result["metadata"]) == 1
    assert result["metadata"][0]["filename"] == "meta.xml"


# ---------------------------------------------------------------------------
# 3. _read_config
# ---------------------------------------------------------------------------


def test_read_config_extracts_fields(tmp_path: Path) -> None:
    """Top-level fields are extracted from config.yaml."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    write_doc(
        manuscript_dir / "config.yaml",
        "title: My Book\nauthor: Jane Doe\nisbn: 978-1234567890\nversion: '1.0'\n",
    )
    config = _read_config(manuscript_dir)
    assert config["title"] == "My Book"
    assert config["author"] == "Jane Doe"
    assert config["isbn"] == "978-1234567890"
    assert config["version"] == "1.0"


def test_read_config_missing_file_returns_empty(tmp_path: Path) -> None:
    """Missing config.yaml returns an empty dict."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    assert _read_config(manuscript_dir) == {}


def test_read_config_publication_subdict(tmp_path: Path) -> None:
    """The 'publication' sub-dict is merged into the flat result via setdefault."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    write_doc(
        manuscript_dir / "config.yaml",
        "title: Top Level Title\n"
        "publication:\n"
        "  isbn: 978-0000000000\n"
        "  doi: 10.5281/zenodo.12345\n"
        "  publisher: Zenodo\n",
    )
    config = _read_config(manuscript_dir)
    assert config["title"] == "Top Level Title"
    assert config["isbn"] == "978-0000000000"
    assert config["doi"] == "10.5281/zenodo.12345"
    assert config["publisher"] == "Zenodo"


def test_read_config_top_level_takes_precedence_over_publication(tmp_path: Path) -> None:
    """setdefault means a top-level key wins over the publication sub-dict."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    write_doc(
        manuscript_dir / "config.yaml",
        "title: Top Winner\nisbn: 978-top\npublication:\n  isbn: 978-sub\n  doi: 10.5281/zenodo.999\n",
    )
    config = _read_config(manuscript_dir)
    assert config["isbn"] == "978-top"
    assert config["doi"] == "10.5281/zenodo.999"


def test_read_config_non_dict_yaml(tmp_path: Path) -> None:
    """YAML that parses to a non-dict (e.g. a list) returns {}."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    write_doc(manuscript_dir / "config.yaml", "- item1\n- item2\n")
    assert _read_config(manuscript_dir) == {}


# ---------------------------------------------------------------------------
# 4. _resolve_project_root
# ---------------------------------------------------------------------------


def test_resolve_project_root_qualified(tmp_path: Path) -> None:
    """A qualified name templates/template_test resolves to projects/templates/template_test."""
    make_project(tmp_path, "template_test", program="templates")
    resolved = _resolve_project_root("templates/template_test", tmp_path)
    assert resolved == tmp_path / "projects" / "templates" / "template_test"
    assert resolved.is_dir()


def test_resolve_project_root_bare_name(tmp_path: Path) -> None:
    """A bare name resolves via the 'templates' prefix."""
    make_project(tmp_path, "mybook", program="templates")
    resolved = _resolve_project_root("mybook", tmp_path)
    assert resolved == tmp_path / "projects" / "templates" / "mybook"
    assert resolved.is_dir()


def test_resolve_project_root_bare_name_working_prefix(tmp_path: Path) -> None:
    """A bare name resolves via the 'working' prefix."""
    make_project(tmp_path, "draft", program="working")
    resolved = _resolve_project_root("draft", tmp_path)
    assert resolved == tmp_path / "projects" / "working" / "draft"


def test_resolve_project_root_nonexistent_raises(tmp_path: Path) -> None:
    """Nonexistent project raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        _resolve_project_root("templates/nonexistent", tmp_path)


def test_resolve_project_root_bare_nonexistent_raises(tmp_path: Path) -> None:
    """Bare name with no matching prefix raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        _resolve_project_root("nope", tmp_path)


# ---------------------------------------------------------------------------
# 5. _make_bundle_dir
# ---------------------------------------------------------------------------


def test_make_bundle_dir_created(tmp_path: Path) -> None:
    """_make_bundle_dir creates a directory with the flattened project name."""
    bundle_dir = _make_bundle_dir(tmp_path, "templates/my_book", "20250101T000000Z")
    assert bundle_dir.is_dir()
    assert bundle_dir.name == "templates_my_book-20250101T000000Z"


def test_make_bundle_dir_bare_name(tmp_path: Path) -> None:
    """A bare project name (no slash) is used as-is."""
    bundle_dir = _make_bundle_dir(tmp_path, "mybook", "20250101T000000Z")
    assert bundle_dir.is_dir()
    assert bundle_dir.name == "mybook-20250101T000000Z"


def test_make_bundle_dir_creates_parents(tmp_path: Path) -> None:
    """Parent directories are created if they don't exist."""
    output_dir = tmp_path / "deeply" / "nested" / "exports"
    bundle_dir = _make_bundle_dir(output_dir, "templates/book", "20250101T000000Z")
    assert bundle_dir.is_dir()


# ---------------------------------------------------------------------------
# 6. export_for_publishing (full pipeline)
# ---------------------------------------------------------------------------


def test_export_for_publishing_creates_bundle_and_manifest(tmp_path: Path) -> None:
    """export_for_publishing builds bundle_dir, manifest.json, and latest symlink."""
    make_project(tmp_path, "template_test", program="templates", with_output=True)

    # Add real artifact files in output/pdf/ and output/ebook/ and output/metadata/
    project_root = tmp_path / "projects" / "templates" / "template_test"
    write_doc(project_root / "output" / "pdf" / "manuscript.pdf", "PDF" * 500)
    write_doc(project_root / "output" / "ebook" / "book.epub", "EPUB" * 200)
    write_doc(
        project_root / "output" / "metadata" / "meta.json",
        '{"title": "Test"}',
    )

    output_dir = tmp_path / "exports"
    bundle_dir = export_for_publishing(
        project="templates/template_test",
        output_dir=output_dir,
        repo_root=tmp_path,
    )

    assert bundle_dir.is_dir()
    assert bundle_dir.parent == output_dir

    manifest_path = bundle_dir / "manifest.json"
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema_version"] == "1.0"
    assert manifest["project"] == "templates/template_test"
    assert "artifacts" in manifest
    assert len(manifest["artifacts"]["pdf"]) == 1
    assert len(manifest["artifacts"]["epub"]) == 1
    assert len(manifest["artifacts"]["metadata"]) == 1

    # The copied PDF should exist in the bundle
    pdf_copy = bundle_dir / "pdf" / "manuscript.pdf"
    assert pdf_copy.is_file()

    # Latest symlink points to the bundle dir
    latest = output_dir / "latest"
    assert latest.is_symlink()
    assert latest.resolve() == bundle_dir.resolve()


def test_export_for_publishing_no_artifacts_raises(tmp_path: Path) -> None:
    """export_for_publishing raises SystemExit(1) when no artifacts are found."""
    make_project(tmp_path, "template_test", program="templates", with_output=True)
    with pytest.raises(SystemExit) as exc_info:
        export_for_publishing(
            project="templates/template_test",
            output_dir=tmp_path / "exports",
            repo_root=tmp_path,
        )
    assert exc_info.value.code == 1


def test_export_for_publishing_project_not_found(tmp_path: Path) -> None:
    """export_for_publishing raises FileNotFoundError for nonexistent project."""
    with pytest.raises(FileNotFoundError):
        export_for_publishing(
            project="templates/nonexistent",
            output_dir=tmp_path / "exports",
            repo_root=tmp_path,
        )


# ---------------------------------------------------------------------------
# 7. main — success
# ---------------------------------------------------------------------------


def test_main_success_returns_zero(tmp_path: Path) -> None:
    """main() returns 0 when artifacts are present."""
    make_project(tmp_path, "template_test", program="templates", with_output=True)
    project_root = tmp_path / "projects" / "templates" / "template_test"
    write_doc(project_root / "output" / "pdf" / "manuscript.pdf", "PDF" * 500)

    output_dir = tmp_path / "exports"
    ret = main(
        [
            "--project",
            "templates/template_test",
            "--output-dir",
            str(output_dir),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert ret == 0

    # Verify the bundle was actually written
    bundles = list(output_dir.iterdir())
    bundle_dirs = [d for d in bundles if d.is_dir() and not d.is_symlink()]
    assert len(bundle_dirs) == 1
    assert (bundle_dirs[0] / "manifest.json").is_file()
    assert (output_dir / "latest").is_symlink()


# ---------------------------------------------------------------------------
# 8. main — no artifacts
# ---------------------------------------------------------------------------


def test_main_no_artifacts_returns_one(tmp_path: Path) -> None:
    """main() returns 1 when the project has no output artifacts."""
    make_project(tmp_path, "template_test", program="templates", with_output=True)
    ret = main(
        [
            "--project",
            "templates/template_test",
            "--output-dir",
            str(tmp_path / "exports"),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert ret == 1


# ---------------------------------------------------------------------------
# 9. main — nonexistent project
# ---------------------------------------------------------------------------


def test_main_nonexistent_project_returns_one(tmp_path: Path) -> None:
    """main() returns 1 when the project cannot be resolved."""
    ret = main(
        [
            "--project",
            "templates/nonexistent",
            "--output-dir",
            str(tmp_path / "exports"),
            "--repo-root",
            str(tmp_path),
        ]
    )
    assert ret == 1
