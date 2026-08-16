"""Every writer that gets pandoc-crossref must also get formalism.lua.

Numbering has to be identical across editions: a Definition that is number 3 in
the PDF must be number 3 in the DOCX, the EPUB and the web build. A writer that
quietly loses the filter would still render and still exit zero, so the loss is
only detectable by reading the command line pandoc was actually invoked with.

That is what these tests do. No mocking framework is involved: each test puts a
real executable named ``pandoc`` on PATH which records its own argv and then
produces the output file its caller expects. The recorded argv is the genuine
constructed command, so an edit that drops ``--lua-filter`` — or moves it after
``--filter pandoc-crossref`` or ``--citeproc`` — fails here.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering._combined_exports import render_combined_docx, render_combined_epub
from infrastructure.rendering._pandoc_filters import (
    FORMALISM_FILTER_NAME,
    FormalismFilterMissingError,
    formalism_filter_args,
    formalism_filter_path,
)
from infrastructure.rendering._pdf_combined_pandoc import build_pandoc_tex_command
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager

FILTER_ARG = "--lua-filter"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_pandoc(tmp_path: Path) -> tuple[Path, Path]:
    """Install a real executable named ``pandoc`` that records its argv.

    Returns ``(bin_dir, argv_log)``. The script appends its arguments to the log
    one per line, then creates whatever path followed ``-o`` so the calling
    renderer's success checks are satisfied by a real file.
    """
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    argv_log = tmp_path / "argv.log"
    epub_writer = bin_dir / "write-valid-epub.py"
    epub_writer.write_text(
        """import sys
import zipfile

output = sys.argv[1]
container = ('<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
             '<rootfiles><rootfile full-path="EPUB/content.opf" '
             'media-type="application/oebps-package+xml"/></rootfiles></container>')
package = ('<package xmlns="http://www.idpf.org/2007/opf"><manifest>'
           '<item id="chapter" href="text/chapter.xhtml" media-type="application/xhtml+xml"/>'
           '</manifest><spine><itemref idref="chapter"/></spine></package>')
chapter = ('<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Fixture</title></head>'
           '<body><p>Fixture</p></body></html>')
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    archive.writestr("META-INF/container.xml", container)
    archive.writestr("EPUB/content.opf", package)
    archive.writestr("EPUB/text/chapter.xhtml", chapter)
""",
        encoding="utf-8",
    )
    script = bin_dir / "pandoc"
    script.write_text(
        f"""#!/bin/sh
for a in "$@"; do printf '%s\\n' "$a" >> '{argv_log}'; done
printf '%s\\n' '--END--' >> '{argv_log}'
out=""
while [ $# -gt 0 ]; do
  if [ "$1" = "-o" ]; then out="$2"; fi
  shift
done
if [ -n "$out" ]; then
  mkdir -p "$(dirname "$out")"
  case "$out" in
    *.epub) '{sys.executable}' '{epub_writer}' "$out" ;;
    *) printf 'stub' > "$out" ;;
  esac
fi
exit 0
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir, argv_log


def _recorded_argv(argv_log: Path) -> list[str]:
    """Return the argv of the first recorded pandoc invocation."""
    assert argv_log.is_file(), "fake pandoc was never invoked"
    lines = argv_log.read_text(encoding="utf-8").splitlines()
    return lines[: lines.index("--END--")] if "--END--" in lines else lines


def _assert_filter_ordering(argv: list[str], writer: str) -> None:
    """Assert the formalism filter is present and precedes the citation machinery."""
    filter_path = str(formalism_filter_path())
    assert filter_path in argv, f"{writer}: formalism.lua missing from pandoc command: {argv}"

    index = argv.index(filter_path)
    assert argv[index - 1] == FILTER_ARG, f"{writer}: filter path not preceded by --lua-filter"

    for consumer in ("--citeproc",):
        if consumer in argv:
            assert index < argv.index(consumer), f"{writer}: formalism filter must precede {consumer}"

    crossref_positions = [i for i, arg in enumerate(argv) if "pandoc-crossref" in arg]
    for position in crossref_positions:
        assert index < position, f"{writer}: formalism filter must precede pandoc-crossref"


def _assert_bibliography_union(argv: list[str], manuscript_dir: Path, writer: str) -> None:
    """Assert citeproc receives every bibliography in deterministic order."""
    expected = [
        f"--bibliography={manuscript_dir / 'references.bib'}",
        f"--bibliography={manuscript_dir / 'z_supplemental.bib'}",
    ]
    positions = [argv.index(argument) for argument in expected]
    assert positions == sorted(positions), f"{writer}: bibliography order drifted: {argv}"
    assert "--citeproc" in argv, f"{writer}: citeproc missing from pandoc command: {argv}"
    assert argv.index("--citeproc") < positions[0]


def _make_manager(tmp_path: Path) -> RenderManager:
    cfg = RenderingConfig(
        pdf_dir=str(tmp_path / "output/pdf"),
        docx_dir=str(tmp_path / "output/docx"),
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
        output_dir=str(tmp_path / "output"),
    )
    return RenderManager(config=cfg)


MANUSCRIPT_BODY = "::: {.definition #def:a}\nBody.\n:::\n\nSee [@def:a].\n"


def _manuscript(tmp_path: Path) -> Path:
    """Lay out a project tree and return its manuscript dir.

    ``resolve_combined_markdown`` looks for ``<project>/output/pdf/`` or
    ``<project>/output/tex/``, so the combined markdown is written where the
    real combined-PDF stage puts it rather than somewhere convenient.
    """
    project_root = tmp_path / "proj"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    combined = project_root / "output" / "pdf" / "_combined_manuscript.md"
    combined.parent.mkdir(parents=True, exist_ok=True)
    combined.write_text(MANUSCRIPT_BODY, encoding="utf-8")
    (manuscript_dir / "references.bib").write_text("@article{alpha,title={Alpha}}\n", encoding="utf-8")
    (manuscript_dir / "z_supplemental.bib").write_text("@article{omega,title={Omega}}\n", encoding="utf-8")
    return manuscript_dir


# ---------------------------------------------------------------------------
# Writer 1 — combined PDF (natbib)
# ---------------------------------------------------------------------------


def test_combined_pdf_command_carries_the_filter(tmp_path: Path) -> None:
    """The combined PDF/LaTeX command applies formalism.lua."""
    manuscript_dir = _manuscript(tmp_path)
    cfg = RenderingConfig(figures_dir=str(tmp_path / "figures"))
    cmd = build_pandoc_tex_command(
        cfg,
        manuscript_dir / "_combined_manuscript.md",
        tmp_path / "out.tex",
        manuscript_dir,
    )

    _assert_filter_ordering(cmd, "combined PDF")
    # This is the writer where losing the filter is worst: --natbib turns a
    # surviving [@def:a] into \citep and ships "[?]".
    assert "--natbib" in cmd


# ---------------------------------------------------------------------------
# Writer 2 — combined DOCX
# ---------------------------------------------------------------------------


def test_combined_docx_command_carries_the_filter(tmp_path: Path) -> None:
    """render_combined_docx passes formalism.lua through to pandoc."""
    bin_dir, argv_log = _fake_pandoc(tmp_path)
    manuscript_dir = _manuscript(tmp_path)
    manager = _make_manager(tmp_path)
    manager.config.pandoc_path = str(bin_dir / "pandoc")

    render_combined_docx(manager, manuscript_dir, "proj", DiagnosticReporter("proj"))

    argv = _recorded_argv(argv_log)
    _assert_filter_ordering(argv, "combined DOCX")
    _assert_bibliography_union(argv, manuscript_dir, "combined DOCX")


# ---------------------------------------------------------------------------
# Writer 3 — combined EPUB
# ---------------------------------------------------------------------------


def test_combined_epub_command_carries_the_filter(tmp_path: Path) -> None:
    """render_combined_epub passes formalism.lua through in extra_args."""
    captured: dict[str, object] = {}

    def recording_epub_renderer(*args: object, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(output_path=Path("out.epub"), size_bytes=1024)

    manuscript_dir = _manuscript(tmp_path)
    manager = _make_manager(tmp_path)

    render_combined_epub(
        manager,
        manuscript_dir,
        "proj",
        DiagnosticReporter("proj"),
        epub_renderer=recording_epub_renderer,
    )

    extra_args = captured["extra_args"]
    assert isinstance(extra_args, list)
    _assert_filter_ordering(extra_args, "combined EPUB")
    _assert_bibliography_union(extra_args, manuscript_dir, "combined EPUB")


# ---------------------------------------------------------------------------
# Writer 4 — combined HTML / web
# ---------------------------------------------------------------------------


def test_combined_html_command_carries_the_filter(tmp_path: Path) -> None:
    """The web renderer's combined-HTML command applies formalism.lua."""
    from infrastructure.rendering.web_renderer import WebRenderer

    bin_dir, argv_log = _fake_pandoc(tmp_path)
    manuscript_dir = _manuscript(tmp_path)
    section = manuscript_dir / "01_intro.md"
    section.write_text("# Intro\n\n::: {.definition #def:a}\nBody.\n:::\n", encoding="utf-8")

    cfg = RenderingConfig(
        web_dir=str(tmp_path / "proj/output/web"),
        output_dir=str(tmp_path / "proj/output"),
        figures_dir=str(tmp_path / "proj/output/figures"),
    )
    cfg.pandoc_path = str(bin_dir / "pandoc")
    renderer = WebRenderer(config=cfg)

    renderer.render_combined([section], manuscript_dir)

    argv = _recorded_argv(argv_log)
    _assert_filter_ordering(argv, "combined HTML")
    _assert_bibliography_union(argv, manuscript_dir, "combined HTML")


# ---------------------------------------------------------------------------
# Writer 5 — opt-in ebook stage
# ---------------------------------------------------------------------------


def test_ebook_stage_command_carries_the_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The ebook stage's EPUB/MOBI/DOCX renders apply formalism.lua.

    The stage imports its renderers at module scope and does not accept a
    pandoc path, so the fake binary is installed on PATH — environment
    isolation, not a mocking framework.
    """
    from infrastructure.rendering import ebook_stage

    bin_dir, argv_log = _fake_pandoc(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

    repo_root = tmp_path / "repo"
    project_root = repo_root / "projects" / "working" / "proj"
    (project_root / "manuscript").mkdir(parents=True)
    (project_root / "manuscript" / "references.bib").write_text("@article{alpha,title={Alpha}}\n", encoding="utf-8")
    (project_root / "manuscript" / "z_supplemental.bib").write_text("@article{omega,title={Omega}}\n", encoding="utf-8")
    combined = project_root / "output" / "pdf" / "_combined_manuscript.md"
    combined.parent.mkdir(parents=True, exist_ok=True)
    combined.write_text(MANUSCRIPT_BODY, encoding="utf-8")

    exit_code = ebook_stage.run_ebook_generation(repo_root, "proj", skip_formats_arg="mobi,docx")
    assert exit_code == 0

    argv = _recorded_argv(argv_log)
    _assert_filter_ordering(argv, "ebook stage")
    _assert_bibliography_union(argv, project_root / "manuscript", "ebook stage")


# ---------------------------------------------------------------------------
# The wiring test itself must be able to fail
# ---------------------------------------------------------------------------


def test_ordering_assertion_rejects_a_command_missing_the_filter() -> None:
    """Negative control: the shared assertion fails on an unfiltered command."""
    with pytest.raises(AssertionError, match="formalism.lua missing"):
        _assert_filter_ordering(["pandoc", "--natbib", "--citeproc"], "control")


def test_ordering_assertion_rejects_a_filter_placed_after_citeproc() -> None:
    """Negative control: ordering is enforced, not just presence."""
    argv = ["pandoc", "--citeproc", FILTER_ARG, str(formalism_filter_path())]
    with pytest.raises(AssertionError, match="must precede --citeproc"):
        _assert_filter_ordering(argv, "control")


def test_ordering_assertion_rejects_a_filter_placed_after_crossref() -> None:
    """Negative control: crossref ordering is enforced too."""
    argv = ["pandoc", "--filter", "/usr/bin/pandoc-crossref", FILTER_ARG, str(formalism_filter_path())]
    with pytest.raises(AssertionError, match="must precede pandoc-crossref"):
        _assert_filter_ordering(argv, "control")


# ---------------------------------------------------------------------------
# Missing-filter policy
# ---------------------------------------------------------------------------


def test_filter_ships_with_the_repository() -> None:
    """The Lua filter is a tracked file inside the rendering package."""
    path = formalism_filter_path()
    assert path.is_file()
    assert path.name == FORMALISM_FILTER_NAME
    assert path.parent.name == "rendering"


def test_missing_filter_raises_rather_than_degrading(tmp_path: Path) -> None:
    """A missing filter is a broken install, not a silent fallback to unnumbered.

    The renderers must not be able to report success while shipping a manuscript
    whose Definitions lost their numbers. A real empty directory is passed in, so
    this exercises the production lookup against a real filesystem.
    """
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(FormalismFilterMissingError) as excinfo:
        formalism_filter_path(package_dir=empty)

    message = str(excinfo.value)
    assert FORMALISM_FILTER_NAME in message
    assert "broken or" in message


def test_missing_filter_error_escapes_the_docx_and_epub_warning_handlers() -> None:
    """The error type must not be swallowed by the writers' warning handlers.

    render_combined_docx/epub catch RenderingError and (OSError,
    SubprocessError, ValueError, FileNotFoundError) and downgrade them to a
    logged warning. A missing shipped filter must propagate instead.
    """
    from infrastructure.core.exceptions import RenderingError

    assert issubclass(FormalismFilterMissingError, RuntimeError)
    for swallowed in (RenderingError, OSError, subprocess.SubprocessError, ValueError, FileNotFoundError):
        assert not issubclass(FormalismFilterMissingError, swallowed)


def test_filter_args_are_a_lua_filter_pair() -> None:
    """formalism_filter_args returns exactly the pandoc flag pair."""
    args = formalism_filter_args()
    assert args == [FILTER_ARG, str(formalism_filter_path())]
