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

import json
import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace

import defusedxml.ElementTree as safe_et
import pytest

from infrastructure.core.exceptions import CompilationError, RenderingError, TemplateError
from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.publishing.transmission_bookends import BEGIN_FILENAME, END_FILENAME
from infrastructure.rendering._bibliography import BibliographyConflictError, pandoc_bibliography_args
from infrastructure.rendering._combined_exports import (
    combined_source_files,
    prepare_shared_combined_markdown,
    render_combined_docx,
    render_combined_epub,
    render_combined_outputs,
    resolve_bibliography,
    resolve_combined_markdown,
    rewrite_pdf_figure_refs_to_raster,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reporter(tmp_path: Path) -> DiagnosticReporter:
    """Build a DiagnosticReporter backed by tmp_path."""
    return DiagnosticReporter("test_project")


def _make_manager(tmp_path: Path, **overrides: object) -> RenderManager:
    """Create a RenderManager with all output dirs under tmp_path."""
    cfg = RenderingConfig(
        pdf_dir=str(tmp_path / "output/pdf"),
        docx_dir=str(tmp_path / "output/docx"),
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
        output_dir=str(tmp_path / "output"),
    )
    for attr, val in overrides.items():
        setattr(cfg, attr, val)
    return RenderManager(config=cfg)


def _epub_package_identifiers(path: Path) -> tuple[str, str]:
    """Read the OPF and NCX identities from one real combined export."""

    with zipfile.ZipFile(path) as archive:
        opf_name = next(name for name in archive.namelist() if name.endswith(".opf"))
        ncx_name = next(name for name in archive.namelist() if name.endswith(".ncx"))
        opf = safe_et.fromstring(archive.read(opf_name))
        ncx = safe_et.fromstring(archive.read(ncx_name))
    package_identifier = opf.find(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert package_identifier is not None and package_identifier.text is not None
    navigation_identifier = next(
        node.get("content")
        for node in ncx.findall(".//{http://www.daisy.org/z3986/2005/ncx/}meta")
        if node.get("name") == "dtb:uid"
    )
    assert navigation_identifier is not None
    return package_identifier.text, navigation_identifier


# ---------------------------------------------------------------------------
# combined_source_files
# ---------------------------------------------------------------------------


def test_combined_source_files_includes_existing_path(tmp_path: Path) -> None:
    """A file that exists on disk is always included regardless of bookend status."""
    existing = tmp_path / "01_intro.md"
    existing.write_text("# Intro\n")

    result = combined_source_files([existing])

    assert result == [existing]


def test_combined_source_files_excludes_missing_bookend(tmp_path: Path) -> None:
    """A missing transmission bookend (by filename) is excluded from the output list."""
    missing_bookend = tmp_path / BEGIN_FILENAME
    # Do NOT create the file — it is missing AND is_transmission_bookend => exclude

    result = combined_source_files([missing_bookend])

    assert result == []


def test_prepare_shared_combined_markdown_supports_docs_manuscript_root(tmp_path: Path) -> None:
    """The shared producer writes to project output for docs/manuscript layouts."""

    manuscript_dir = tmp_path / "docs" / "manuscript"
    manuscript_dir.mkdir(parents=True)
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Docs manuscript\n", encoding="utf-8")
    manager = _make_manager(tmp_path)

    result = prepare_shared_combined_markdown(
        manager,
        [source],
        manuscript_dir,
        "templates/docs_project",
    )

    assert result == tmp_path / "output" / "web" / "_combined_manuscript.md"
    assert result.is_file()
    assert (tmp_path / "output" / "reports" / "manuscript_composition.json").is_file()


def test_slides_only_combined_stage_writes_current_composition_evidence(tmp_path: Path) -> None:
    """Without HTML, a slides-only run still binds its current manuscript inputs."""

    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Slides manuscript\n", encoding="utf-8")
    manager = _make_manager(
        tmp_path,
        enable_pdf=False,
        enable_html=False,
        enable_slides=True,
        enable_docx=False,
        enable_epub=False,
    )

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/slides_project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    combined = tmp_path / "output" / "web" / "_combined_manuscript.md"
    receipt = json.loads((tmp_path / "output" / "reports" / "manuscript_composition.json").read_text())
    assert combined.is_file()
    assert receipt["algorithm"] == "shared-combined-markdown-v1"


def test_combined_source_files_includes_missing_non_bookend(tmp_path: Path) -> None:
    """A missing non-bookend file is still included (caller is responsible for it)."""
    missing_regular = tmp_path / "05_discussion.md"
    # Do NOT create the file — missing AND NOT is_transmission_bookend => include

    result = combined_source_files([missing_regular])

    assert result == [missing_regular]


def test_combined_source_files_mixed_list(tmp_path: Path) -> None:
    """Mixed list: existing, missing-regular, and missing-bookend handled correctly."""
    existing = tmp_path / "01_intro.md"
    existing.write_text("# Intro\n")
    missing_regular = tmp_path / "02_methods.md"
    missing_end_bookend = tmp_path / END_FILENAME  # missing

    result = combined_source_files([existing, missing_regular, missing_end_bookend])

    assert existing in result
    assert missing_regular in result
    assert missing_end_bookend not in result


# ---------------------------------------------------------------------------
# resolve_combined_markdown
# ---------------------------------------------------------------------------


def test_resolve_combined_markdown_pdf_candidate(tmp_path: Path) -> None:
    """Returns the pdf/_combined_manuscript.md when it exists and is non-empty."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    pdf_candidate = project_root / "output" / "pdf" / "_combined_manuscript.md"
    pdf_candidate.parent.mkdir(parents=True)
    pdf_candidate.write_text("# Combined\n\nSome content.\n")

    result = resolve_combined_markdown(manuscript_dir)

    assert result == pdf_candidate


def test_resolve_combined_markdown_tex_candidate_fallback(tmp_path: Path) -> None:
    """Returns tex/_combined_manuscript.md when the pdf candidate is absent."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    tex_candidate = project_root / "output" / "tex" / "_combined_manuscript.md"
    tex_candidate.parent.mkdir(parents=True)
    tex_candidate.write_text("# Combined TeX\n")

    result = resolve_combined_markdown(manuscript_dir)

    assert result == tex_candidate


def test_resolve_combined_markdown_returns_none_when_both_missing(tmp_path: Path) -> None:
    """Returns None when neither pdf nor tex combined markdown exists."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    result = resolve_combined_markdown(manuscript_dir)

    assert result is None


def test_resolve_combined_markdown_empty_file_skipped(tmp_path: Path) -> None:
    """An empty _combined_manuscript.md is skipped; None returned if no non-empty candidate."""
    project_root = tmp_path / "myproject"
    manuscript_dir = project_root / "output" / "manuscript"
    manuscript_dir.mkdir(parents=True)

    pdf_candidate = project_root / "output" / "pdf" / "_combined_manuscript.md"
    pdf_candidate.parent.mkdir(parents=True)
    pdf_candidate.write_text("")  # empty

    result = resolve_combined_markdown(manuscript_dir)

    assert result is None


def test_resolve_combined_markdown_other_dir_layout(tmp_path: Path) -> None:
    """When manuscript_dir is NOT inside an 'output' dir, project_root = parent."""
    # Layout: tmp_path/manuscript -> project_root = tmp_path
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    pdf_candidate = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    pdf_candidate.parent.mkdir(parents=True)
    pdf_candidate.write_text("# Content\n")

    result = resolve_combined_markdown(manuscript_dir)

    assert result == pdf_candidate


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


# ---------------------------------------------------------------------------
# render_combined_docx
# ---------------------------------------------------------------------------


def test_render_combined_docx_skips_when_no_combined_md(tmp_path: Path) -> None:
    """render_combined_docx returns early (no error) when no combined markdown exists."""
    manager = _make_manager(tmp_path)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # No combined markdown => early return, no exception
    render_combined_docx(manager, manuscript_dir, "myproject", reporter)


def test_render_combined_epub_skips_when_no_combined_md(tmp_path: Path) -> None:
    """render_combined_epub returns early (no error) when no combined markdown exists."""
    manager = _make_manager(tmp_path)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)


def test_render_combined_docx_with_bibliography(tmp_path: Path) -> None:
    """render_combined_docx adds citeproc args when a .bib file is present."""
    # Set up project structure with combined markdown and bib
    project_root = tmp_path
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()

    # Place combined markdown where resolve_combined_markdown will find it
    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    combined_md = pdf_dir / "_combined_manuscript.md"
    combined_md.write_text("# Test combined\n\nContent here.\n")

    # Add a bib file
    bib = manuscript_dir / "references.bib"
    bib.write_text("@article{test, title={Test}}\n")

    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)

    # Should not raise — may fail pandoc call (missing docx template etc.) but
    # that is caught inside render_combined_docx and logged as a warning.
    render_combined_docx(manager, manuscript_dir, "myproject", reporter)


def test_render_combined_epub_with_bibliography(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()

    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    combined_md = pdf_dir / "_combined_manuscript.md"
    combined_md.write_text("# Combined EPUB test\n\nContent.\n")

    bib = manuscript_dir / "references.bib"
    bib.write_text("@article{x, title={X}}\n")
    supplemental_bib = manuscript_dir / "z_supplemental.bib"
    supplemental_bib.write_text("@article{y, title={Y}}\n")
    (manuscript_dir / "cover.png").write_bytes(b"cover fixture")
    (manuscript_dir / "config.yaml").write_text(
        "paper:\n"
        "  title: Test EPUB\n"
        "  cover:\n"
        "    image: cover.png\n"
        "    alt: A source-owned cover description.\n"
        "authors:\n"
        "  - name: Ada Lovelace\n"
        "metadata:\n"
        "  language: en-GB\n"
    )

    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)
    captured: dict[str, object] = {}

    def fake_render_epub(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(output_path=Path("test.epub"), size_bytes=1024)

    render_combined_epub(
        manager,
        manuscript_dir,
        "myproject",
        reporter,
        epub_renderer=fake_render_epub,
    )

    assert captured["bibliography"] is None
    assert captured["title"] == "Test EPUB"
    assert captured["author"] == "Ada Lovelace"
    assert captured["language"] == "en-GB"
    assert captured["cover_image"] == manuscript_dir / "cover.png"
    assert captured["cover_alt"] == "A source-owned cover description."
    extra_args = captured["extra_args"]
    assert isinstance(extra_args, list)
    assert "--citeproc" in extra_args
    assert f"--bibliography={bib}" in extra_args
    assert f"--bibliography={supplemental_bib}" in extra_args
    assert extra_args.index(f"--bibliography={bib}") < extra_args.index(f"--bibliography={supplemental_bib}")


def test_render_combined_epub_without_bibliography(tmp_path: Path) -> None:
    """render_combined_epub uses bibliography=None when no .bib file is present."""
    project_root = tmp_path
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir()

    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    combined_md = pdf_dir / "_combined_manuscript.md"
    combined_md.write_text("# Combined EPUB test\n\nContent.\n")

    # No .bib file present
    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_render_combined_epub_identifier_tracks_effective_bibliography(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production bibliography extras participate in effective-package identity."""

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    combined_md = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir(parents=True)
    combined_md.write_text("# Evidence\n\nThe result follows prior work [@binding2026].\n", encoding="utf-8")
    bibliography = manuscript_dir / "references.bib"
    bibliography.write_text(
        "@article{binding2026,\n"
        "  author={Binder, Ada},\n"
        "  title={First Effective Bibliography Revision},\n"
        "  journal={Determinism Quarterly},\n"
        "  year={2026}\n"
        "}\n",
        encoding="utf-8",
    )
    manager = _make_manager(tmp_path)
    reporter = _make_reporter(tmp_path)
    output = tmp_path / "output" / "epub" / "myproject_combined.epub"

    render_combined_epub(manager, manuscript_dir, "myproject", reporter)
    first_package_id, first_navigation_id = _epub_package_identifiers(output)
    with zipfile.ZipFile(output) as archive:
        first_text = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith((".xhtml", ".html"))
        )
    assert first_package_id == first_navigation_id
    assert "First Effective Bibliography Revision" in first_text

    bibliography.write_text(
        "@article{binding2026,\n"
        "  author={Binder, Ada},\n"
        "  title={Second Effective Bibliography Revision},\n"
        "  journal={Determinism Quarterly},\n"
        "  year={2026}\n"
        "}\n",
        encoding="utf-8",
    )
    render_combined_epub(manager, manuscript_dir, "myproject", reporter)
    changed_package_id, changed_navigation_id = _epub_package_identifiers(output)

    assert changed_package_id == changed_navigation_id
    assert changed_package_id != first_package_id


# ---------------------------------------------------------------------------
# render_combined_outputs — config toggle branches
# ---------------------------------------------------------------------------


class _FailingRenderManager(RenderManager):
    """RenderManager subclass that raises on render calls to exercise error paths."""

    def __init__(self, cfg: RenderingConfig, *, raise_with: Exception) -> None:
        super().__init__(config=cfg)
        self._raise_with = raise_with

    def render_combined_pdf(
        self, source_files: list[Path], manuscript_dir: Path, project_name: str = "project"
    ) -> Path:  # type: ignore[override]
        """Always raises the configured exception."""
        raise self._raise_with

    def render_combined_web(
        self, source_files: list[Path], manuscript_dir: Path, project_name: str = "project"
    ) -> Path:  # type: ignore[override]
        """Always raises the configured exception."""
        raise self._raise_with


class _AuxRefreshManager(RenderManager):
    """Test manager that produces a real AUX map before exercising the slide resolver."""

    def __init__(
        self,
        tmp_path: Path,
        *,
        aux_text: str | None,
        slide_error: type[TemplateError] | None = None,
    ) -> None:
        cfg = RenderingConfig(
            enable_pdf=True,
            enable_html=False,
            enable_slides=True,
            enable_docx=False,
            enable_epub=False,
            pdf_dir=str(tmp_path / "output/pdf"),
            slides_dir=str(tmp_path / "output/slides"),
            figures_dir=str(tmp_path / "output/figures"),
            web_dir=str(tmp_path / "output/web"),
        )
        super().__init__(config=cfg)
        self.aux_text = aux_text
        self.slide_error = slide_error
        self.events: list[str] = []
        self.strict_refresh_flags: list[bool] = []

    def render_combined_pdf(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path:  # type: ignore[override]
        self.events.append("combined")
        aux_path = Path(self.config.pdf_dir) / "_combined_manuscript.aux"
        assert not aux_path.exists(), "the orchestration boundary must remove stale AUX state"
        aux_path.parent.mkdir(parents=True, exist_ok=True)
        if self.aux_text is not None:
            aux_path.write_text(self.aux_text, encoding="utf-8")
        output = Path(self.config.pdf_dir) / "project_combined.pdf"
        output.write_bytes(b"%PDF-1.7\n")
        return output

    def render_slides(
        self,
        source_file: Path,
        output_format: str = "beamer",
        *,
        strict_cross_deck_refs: bool = False,
    ) -> Path:  # type: ignore[override]
        self.events.append(f"slides:{source_file.stem}")
        self.strict_refresh_flags.append(strict_cross_deck_refs)
        output = Path(self.config.slides_dir) / f"{source_file.stem}_slides.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        if self.slide_error is not None and source_file.stem == "01_intro":
            output.write_bytes(b"partial refreshed deck")
            raise self.slide_error("forced Beamer refresh failure")
        post_pandoc_tex = (
            r"See Equation \eqref{eq:foreign}."
            if source_file.stem == "01_intro"
            else r"\begin{equation}\label{eq:foreign}x=1\end{equation}"
        )
        resolved = self.slides_renderer._resolve_cross_deck_refs(
            post_pandoc_tex,
            strict_cross_deck_refs=strict_cross_deck_refs,
        )
        output.write_text(resolved, encoding="utf-8")
        return output


def _write_foreign_ref_sources(manuscript_dir: Path) -> tuple[Path, Path]:
    """Write two decks with one canonical Pandoc cross-deck equation reference."""
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n\nSee [@eq:foreign].\n", encoding="utf-8")
    definition = manuscript_dir / "03_results.md"
    definition.write_text("# Results\n\n$$x = 1$$ {#eq:foreign}\n", encoding="utf-8")
    return source, definition


def test_render_combined_outputs_pdf_disabled_skips(tmp_path: Path) -> None:
    """When enable_pdf is False, the PDF render path is skipped without error."""
    cfg = RenderingConfig(enable_pdf=False, enable_html=False, enable_docx=False, enable_epub=False)
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # No exception expected
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_html_disabled_skips(tmp_path: Path) -> None:
    """When enable_html is False, the HTML render path is skipped without error."""
    cfg = RenderingConfig(enable_pdf=False, enable_html=False, enable_docx=False, enable_epub=False)
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_refreshes_slides_after_current_aux_exists(tmp_path: Path) -> None:
    """The current combined AUX exists before the real slide resolver runs."""
    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}{Foreign equation}{equation.7}{}}\n",
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source, definition = _write_foreign_ref_sources(manuscript_dir)
    bookend = manuscript_dir / BEGIN_FILENAME
    bookend.write_text("# Generated transmission boundary\n", encoding="utf-8")
    skipped = manuscript_dir / "02_appendix.md"
    skipped.write_text("<!-- render:skip-beamer -->\n# Appendix\n", encoding="utf-8")
    aux_path = Path(manager.config.pdf_dir) / "_combined_manuscript.aux"
    aux_path.parent.mkdir(parents=True)
    aux_path.write_text("\\relax\n\\newlabel{eq:foreign}{{99}{1}}\n", encoding="utf-8")

    render_combined_outputs(
        manager,
        [bookend, source, skipped, definition],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.events == ["combined", "slides:01_intro", "slides:03_results"]
    assert manager.strict_refresh_flags == [True, True]
    refreshed = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    assert "See Equation (7)." in refreshed.read_text(encoding="utf-8")


def test_render_combined_outputs_pdf_disabled_does_not_refresh_slides(tmp_path: Path) -> None:
    """A slides-enabled run cannot refresh from AUX when combined PDF is disabled."""

    class _NoRefreshManager(RenderManager):
        def __init__(self) -> None:
            super().__init__(
                config=RenderingConfig(
                    enable_pdf=False,
                    enable_html=False,
                    enable_slides=True,
                    enable_docx=False,
                    enable_epub=False,
                    figures_dir=str(tmp_path / "output/figures"),
                    slides_dir=str(tmp_path / "output/slides"),
                    web_dir=str(tmp_path / "output/web"),
                )
            )
            self.slide_calls = 0

        def render_slides(
            self,
            source_file: Path,
            output_format: str = "beamer",
            *,
            strict_cross_deck_refs: bool = False,
        ) -> Path:  # type: ignore[override]
            self.slide_calls += 1
            raise AssertionError("disabled combined PDF must not trigger a refresh")

    manager = _NoRefreshManager()
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n", encoding="utf-8")

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.slide_calls == 0


def test_render_combined_outputs_pdf_failure_does_not_refresh_slides(tmp_path: Path) -> None:
    """A failed combined PDF never dispatches the dependent Beamer refresh."""

    class _NoRefreshManager(_FailingRenderManager):
        def __init__(self) -> None:
            cfg = RenderingConfig(
                enable_pdf=True,
                enable_html=False,
                enable_slides=True,
                enable_docx=False,
                enable_epub=False,
                pdf_dir=str(tmp_path / "output/pdf"),
                figures_dir=str(tmp_path / "output/figures"),
                slides_dir=str(tmp_path / "output/slides"),
                web_dir=str(tmp_path / "output/web"),
            )
            super().__init__(cfg, raise_with=RenderingError("forced combined failure"))
            self.slide_calls = 0

        def render_slides(
            self,
            source_file: Path,
            output_format: str = "beamer",
            *,
            strict_cross_deck_refs: bool = False,
        ) -> Path:  # type: ignore[override]
            self.slide_calls += 1
            raise AssertionError("failed combined PDF must not trigger a refresh")

    manager = _NoRefreshManager()
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Intro\n", encoding="utf-8")
    aux_path = Path(manager.config.pdf_dir) / "_combined_manuscript.aux"
    aux_path.parent.mkdir(parents=True)
    aux_path.write_text("stale aux\n", encoding="utf-8")

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    assert manager.slide_calls == 0
    assert not aux_path.exists()


@pytest.mark.parametrize(
    ("aux_text", "message"),
    [
        (None, "without producing the AUX"),
        ("not a LaTeX AUX\n", "no parseable LaTeX structure"),
        ("\\relax\n\\newlabel{broken}{{1}{2}\n", "no parseable LaTeX structure"),
    ],
)
def test_render_combined_outputs_rejects_unusable_current_aux_and_removes_first_pass_decks(
    tmp_path: Path,
    aux_text: str | None,
    message: str,
) -> None:
    """Missing, malformed, or incomplete current AUX state cannot leave first-pass decks."""
    manager = _AuxRefreshManager(tmp_path, aux_text=aux_text)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    slides_dir = Path(manager.config.slides_dir)
    slides_dir.mkdir(parents=True)
    for source in sources:
        (slides_dir / f"{source.stem}_slides.pdf").write_bytes(b"unresolved first pass")

    with pytest.raises(RenderingError, match=message):
        render_combined_outputs(
            manager,
            list(sources),
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=2,
        )

    assert manager.events == ["combined"]
    assert not list(slides_dir.glob("*_slides.pdf"))


def test_render_combined_outputs_strict_post_pandoc_refs_remove_unresolved_deck(tmp_path: Path) -> None:
    """A valid AUX without the canonical foreign label fails after Pandoc and cleans the deck."""
    manager = _AuxRefreshManager(tmp_path, aux_text=r"\relax" + "\n")
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    failed_output = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    failed_output.parent.mkdir(parents=True)
    failed_output.write_bytes(b"unresolved first pass")

    with pytest.raises(RenderingError, match="refusing to publish stale standalone decks"):
        render_combined_outputs(
            manager,
            list(sources),
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=2,
        )

    assert manager.strict_refresh_flags == [True, True]
    assert not failed_output.exists()


@pytest.mark.parametrize("error_type", [CompilationError, TemplateError])
def test_render_combined_outputs_removes_failed_refresh_deck(
    tmp_path: Path,
    error_type: type[TemplateError],
) -> None:
    """Compiler and renderer-domain failures cannot preserve the unresolved first pass."""
    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}}\n",
        slide_error=error_type,
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    failed_output = Path(manager.config.slides_dir) / "01_intro_slides.pdf"
    failed_output.parent.mkdir(parents=True)
    failed_output.write_bytes(b"unresolved first pass")

    with pytest.raises(RenderingError, match="refusing to publish stale standalone decks"):
        render_combined_outputs(
            manager,
            list(sources),
            manuscript_dir,
            "templates/project",
            _make_reporter(tmp_path),
            rendered_count=2,
        )

    assert not failed_output.exists()
    assert (Path(manager.config.slides_dir) / "03_results_slides.pdf").is_file()


def test_render_combined_outputs_aux_refresh_is_idempotent(tmp_path: Path) -> None:
    """Repeated current-AUX refreshes replace decks with identical resolved content."""
    manager = _AuxRefreshManager(
        tmp_path,
        aux_text="\\relax\n\\newlabel{eq:foreign}{{7}{2}}\n",
    )
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    sources = _write_foreign_ref_sources(manuscript_dir)
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(
        manager,
        list(sources),
        manuscript_dir,
        "templates/project",
        reporter,
        rendered_count=2,
    )
    slides_dir = Path(manager.config.slides_dir)
    first_bytes = {path.name: path.read_bytes() for path in sorted(slides_dir.glob("*_slides.pdf"))}

    render_combined_outputs(
        manager,
        list(sources),
        manuscript_dir,
        "templates/project",
        reporter,
        rendered_count=2,
    )
    second_bytes = {path.name: path.read_bytes() for path in sorted(slides_dir.glob("*_slides.pdf"))}

    assert first_bytes == second_bytes
    assert manager.events.count("combined") == 2
    assert manager.events.count("slides:01_intro") == 2
    assert manager.events.count("slides:03_results") == 2


def test_render_combined_outputs_pdf_rendering_error_with_rendered_count(tmp_path: Path) -> None:
    """A RenderingError during PDF with rendered_count>0 logs the individual-PDF note."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("simulated combined-PDF failure")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    # Must not propagate — caught and logged
    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=3)

    # The diagnostic event should be recorded
    assert len(reporter.events) >= 1


def test_render_combined_outputs_pdf_rendering_error_zero_rendered(tmp_path: Path) -> None:
    """A RenderingError during PDF with rendered_count=0 does NOT log the individual note."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("combined-PDF failure")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)

    # Error still recorded despite rendered_count=0
    assert len(reporter.events) >= 1


def test_render_combined_outputs_pdf_oserror_with_existing_combined_md(tmp_path: Path) -> None:
    """An OSError during PDF render logs stderr/stdout attrs and stats the combined-md if present."""
    cfg = RenderingConfig(
        enable_pdf=True,
        enable_html=False,
        enable_docx=False,
        enable_epub=False,
        pdf_dir=str(tmp_path / "output/pdf"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )

    class _OSErrWithAttrs(OSError):
        stderr = "err output"
        stdout = "std output"

    err = _OSErrWithAttrs("disk full")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()

    # Create the combined markdown so the stat-log branch is exercised
    tex_dir = tmp_path / "output" / "tex"
    tex_dir.mkdir(parents=True)
    (tex_dir / "_combined_manuscript.md").write_text("content\n")

    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)


def test_render_combined_outputs_html_rendering_error_recorded(tmp_path: Path) -> None:
    """A RenderingError during HTML render is caught and recorded on the reporter."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=True,
        enable_docx=False,
        enable_epub=False,
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    err = RenderingError("html render failed")
    manager = _FailingRenderManager(cfg, raise_with=err)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [], manuscript_dir, "proj", reporter, rendered_count=0)

    assert len(reporter.events) >= 1


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is required for real DOCX rendering")
def test_render_combined_outputs_docx_is_independent_of_pdf(tmp_path: Path) -> None:
    """DOCX uses a fresh current combined source when PDF is disabled."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=False,
        enable_docx=True,
        enable_epub=False,
        docx_dir=str(tmp_path / "output/docx"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Current DOCX source\n\nCurrent content.\n", encoding="utf-8")
    stale_pdf_md = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    stale_pdf_md.parent.mkdir(parents=True)
    stale_pdf_md.write_text("# STALE PDF SOURCE\n", encoding="utf-8")
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [source], manuscript_dir, "templates/proj", reporter, rendered_count=0)

    output = tmp_path / "output" / "docx" / "proj_combined.docx"
    assert zipfile.is_zipfile(output)
    shared = tmp_path / "output" / "web" / "_combined_manuscript.md"
    assert "Current DOCX source" in shared.read_text(encoding="utf-8")
    assert "STALE PDF SOURCE" not in shared.read_text(encoding="utf-8")
    receipt = json.loads((tmp_path / "output" / "reports" / "manuscript_composition.json").read_text())
    assert receipt["algorithm"] == "shared-combined-markdown-v1"


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is required for real EPUB rendering")
def test_render_combined_outputs_epub_is_independent_of_pdf(tmp_path: Path) -> None:
    """EPUB uses a fresh current combined source when PDF is disabled."""
    cfg = RenderingConfig(
        enable_pdf=False,
        enable_html=False,
        enable_docx=False,
        enable_epub=True,
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
    )
    manager = RenderManager(config=cfg)
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Current EPUB source\n\nCurrent content.\n", encoding="utf-8")
    stale_pdf_md = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    stale_pdf_md.parent.mkdir(parents=True)
    stale_pdf_md.write_text("# STALE PDF SOURCE\n", encoding="utf-8")
    reporter = _make_reporter(tmp_path)

    render_combined_outputs(manager, [source], manuscript_dir, "templates/proj", reporter, rendered_count=0)

    output = tmp_path / "output" / "epub" / "proj_combined.epub"
    assert zipfile.is_zipfile(output)
    shared = tmp_path / "output" / "web" / "_combined_manuscript.md"
    assert "Current EPUB source" in shared.read_text(encoding="utf-8")
    assert "STALE PDF SOURCE" not in shared.read_text(encoding="utf-8")
    receipt = json.loads((tmp_path / "output" / "reports" / "manuscript_composition.json").read_text())
    assert receipt["algorithm"] == "shared-combined-markdown-v1"


# ---------------------------------------------------------------------------
# rewrite_pdf_figure_refs_to_raster
# ---------------------------------------------------------------------------
# Regression coverage for a real failure: a combined manuscript's .pdf figure
# refs (correct for LaTeX) silently fail to embed in EPUB/MOBI/DOCX (PDF is
# not a valid inline-image media type there) — confirmed via epubcheck
# (RSC-007) on a real book, and the underlying cause of a real KDP "couldn't
# convert your HTML file to Kindle format" rejection.


def test_rewrite_pdf_figure_refs_swaps_to_png_when_sibling_exists(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "timeline_dark.png").write_bytes(b"fake-png")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![Caption](../figures/timeline_dark.pdf){#fig-timeline}\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert "../figures/timeline_dark.png" in result
    assert ".pdf" not in result


def test_rewrite_pdf_figure_refs_prefers_png_over_jpg(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "x.png").write_bytes(b"fake-png")
    (tmp_path / "figures" / "x.jpg").write_bytes(b"fake-jpg")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    result = rewrite_pdf_figure_refs_to_raster("![c](../figures/x.pdf)\n", combined_md)

    assert "../figures/x.png" in result


def test_rewrite_pdf_figure_refs_falls_back_to_jpg(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "x.jpg").write_bytes(b"fake-jpg")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    result = rewrite_pdf_figure_refs_to_raster("![c](../figures/x.pdf)\n", combined_md)

    assert "../figures/x.jpg" in result


def test_rewrite_pdf_figure_refs_leaves_unmatched_ref_untouched(tmp_path: Path) -> None:
    """No raster sibling on disk: leave the .pdf ref as-is (surfaces as a normal missing-resource error)."""
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![c](../figures/nonexistent.pdf)\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert result == text


def test_rewrite_pdf_figure_refs_ignores_non_pdf_images(tmp_path: Path) -> None:
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![c](../figures/already_raster.png)\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert result == text


def test_rewrite_pdf_figure_refs_handles_nested_citation_brackets(tmp_path: Path) -> None:
    """Regression: captions with inline citations like [@cite1; @cite2] nest brackets
    inside the alt text — a naive [^\\]]* class can't skip the inner ']' and silently
    fails to match at all, leaving the .pdf ref untouched (confirmed via epubcheck on
    a real manuscript: 3 of 7 figures kept failing after the first version of this fix
    specifically because their captions ended in a citation group)."""
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "historic_ratio_dark.png").write_bytes(b"fake-png")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = (
        "![Caption with sources [@flandreau1996bimetallism; @laughlin1898bimetallism]."
        "](../figures/historic_ratio_dark.pdf){#fig-historic-ratio}\n"
    )
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert "../figures/historic_ratio_dark.png" in result
    assert ".pdf" not in result


def test_rewrite_pdf_figure_refs_handles_multiple_refs(tmp_path: Path) -> None:
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "a.png").write_bytes(b"fake-png")
    (tmp_path / "figures" / "b.png").write_bytes(b"fake-png")
    combined_md = tmp_path / "pdf" / "_combined_manuscript.md"
    combined_md.parent.mkdir()

    text = "![one](../figures/a.pdf){#fig-a}\n\ntext between\n\n![two](../figures/b.pdf){#fig-b}\n"
    result = rewrite_pdf_figure_refs_to_raster(text, combined_md)

    assert "../figures/a.png" in result
    assert "../figures/b.png" in result
    assert ".pdf" not in result
