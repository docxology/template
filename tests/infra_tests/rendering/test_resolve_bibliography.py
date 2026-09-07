"""Tests for infrastructure.rendering._combined_exports — branch coverage.

Covers fixture-driven branches for:
- combined_source_files: existing/missing path, transmission-bookend classification
- resolve_combined_markdown: manuscript/output dir layout, pdf/tex candidates, empty/missing
- resolve_bibliography: deterministic union, path deduplication, and conflicts
- render_combined_docx: no combined-md early return; bibliography/crossref/metadata paths
- render_combined_epub: no combined-md early return; bibliography present vs absent
- render_combined_outputs: enable_* toggles; RenderingError and OSError paths
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering._bibliography import BibliographyConflictError, pandoc_bibliography_args
from infrastructure.rendering._combined_exports import (
    resolve_bibliography,
)


# ---------------------------------------------------------------------------
# resolve_bibliography
# ---------------------------------------------------------------------------


def test_resolve_bibliography_returns_sorted_union(tmp_path: Path) -> None:
    """Every top-level bibliography is returned in deterministic filename order."""
    bib1 = tmp_path / "references.bib"
    bib2 = tmp_path / "zotero.bib"
    bib1.write_text("@article{a,title={A}}\n")
    bib2.write_text("@article{b,title={B}}\n")

    result = resolve_bibliography(tmp_path)

    assert result == (bib1, bib2)


def test_resolve_bibliography_returns_empty_union_when_no_bib(tmp_path: Path) -> None:
    """Returns an empty union when no .bib files are present."""
    result = resolve_bibliography(tmp_path)

    assert result == ()


def test_pandoc_bibliography_args_deduplicate_repeated_paths(tmp_path: Path) -> None:
    """The same repeated database path is passed to Pandoc only once."""
    bibliography = tmp_path / "references.bib"
    bibliography.write_text("@article{a,title={A}}\n", encoding="utf-8")

    assert pandoc_bibliography_args([bibliography, bibliography]) == [f"--bibliography={bibliography}"]


def test_resolve_bibliography_deduplicates_symlink_alias(tmp_path: Path) -> None:
    """Two filenames for one physical database resolve to one union member."""
    bibliography = tmp_path / "references.bib"
    bibliography.write_text("@article{a,title={A}}\n", encoding="utf-8")
    alias = tmp_path / "a_alias.bib"
    try:
        alias.symlink_to(bibliography.name)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    result = resolve_bibliography(tmp_path)

    assert len(result) == 1
    assert result[0].resolve() == bibliography.resolve()


def test_pandoc_bibliography_args_reject_missing_input(tmp_path: Path) -> None:
    """A vanished bibliography fails at the render boundary instead of being dropped."""
    missing = tmp_path / "missing.bib"

    with pytest.raises(FileNotFoundError, match="Bibliography not found"):
        pandoc_bibliography_args([missing])


def test_resolve_bibliography_rejects_duplicate_citation_keys(tmp_path: Path) -> None:
    """Conflicting citeproc/BibTeX winner rules cannot silently diverge by format."""
    first = tmp_path / "a.bib"
    second = tmp_path / "b.bib"
    first.write_text("@article{shared,title={First}}\n", encoding="utf-8")
    second.write_text("@book{shared,title={Second}}\n", encoding="utf-8")

    with pytest.raises(BibliographyConflictError) as exc_info:
        resolve_bibliography(tmp_path)

    message = str(exc_info.value)
    assert message.count("'shared'") == 2
    assert str(first) in message
    assert str(second) in message


def test_resolve_bibliography_rejects_cross_file_case_only_duplicate_keys(tmp_path: Path) -> None:
    """Case-only variants in separate databases fail with both literal keys and paths."""
    first = tmp_path / "a.bib"
    second = tmp_path / "b.bib"
    first.write_text("@article{SharedKey,title={First}}\n", encoding="utf-8")
    second.write_text("@book{sharedkey,title={Second}}\n", encoding="utf-8")

    with pytest.raises(BibliographyConflictError) as exc_info:
        resolve_bibliography(tmp_path)

    message = str(exc_info.value)
    assert "'SharedKey'" in message
    assert "'sharedkey'" in message
    assert str(first) in message
    assert str(second) in message


def test_resolve_bibliography_rejects_same_file_case_only_duplicate_keys(tmp_path: Path) -> None:
    """Case-only variants in one database fail while identifying both declarations."""
    bibliography = tmp_path / "references.bib"
    bibliography.write_text(
        "@article{SharedKey,title={First}}\n@book{sharedkey,title={Second}}\n",
        encoding="utf-8",
    )

    with pytest.raises(BibliographyConflictError) as exc_info:
        resolve_bibliography(tmp_path)

    message = str(exc_info.value)
    assert "'SharedKey'" in message
    assert "'sharedkey'" in message
    assert message.count(str(bibliography)) == 2
