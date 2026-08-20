"""Optional export: a conforming .docx that also carries the project that made it.

Every other renderer in this package produces a *view* of the manuscript — a PDF,
an EPUB, a plain DOCX. Each one leaves the reader holding the paper and nothing
else: the code, the data, and the commands that produced the figures stay wherever
the author left them, reachable only by a link that may already be dead.

This exporter produces a document that carries them. The output is a byte-valid
OOXML file that Word, LibreOffice, and Google Docs open as an ordinary document,
and that *also* holds the project's own source tree inside a signed manifest. The
format is docxplus (https://doi.org/10.5281/zenodo.21983949), imported from
upstream rather than vendored, so this repository stays the rendering engine and
the container specification stays the container project's business.

**Optional by construction.** The dependency is an extra, the stage is opt-in, and
the absence of either is a skip rather than a failure — the same contract the PPTX
and ebook renderers already follow. A template that hard-required a signing stack
to render a paper would have made a niche capability everyone's problem.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

#: The upstream import. Absent unless the `docxplus` extra is installed.
try:  # pragma: no cover - the installed branch is exercised by the opt-in job
    from docxplus.container import DocxPlusBuilder
    from docxplus.fileext import write_document

    _DOCXPLUS_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised whenever the extra is absent
    DocxPlusBuilder = None
    write_document = None
    _DOCXPLUS_AVAILABLE = False

#: Install line quoted verbatim in the skip message, so a reader never has to
#: guess which extra provides this.
INSTALL_HINT = "uv sync --extra docxplus"

#: Directories never carried into an exported document. Build products and
#: virtualenvs are reproducible from the source that *is* carried, and shipping
#: them would inflate a document that has to stay openable.
EXCLUDED_DIRS = frozenset({".git", ".venv", "__pycache__", "node_modules", "output"})


@dataclass
class ExportResult:
    """What the export produced, or why it produced nothing."""

    available: bool
    written: list[Path] = field(default_factory=list)
    carried_files: int = 0
    signed: bool = False
    skipped_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "written": [str(p) for p in self.written],
            "carried_files": self.carried_files,
            "signed": self.signed,
            "skipped_reason": self.skipped_reason,
        }


def is_available() -> bool:
    """True when the optional upstream package is importable."""
    return _DOCXPLUS_AVAILABLE


def _cover_paragraphs(project: str, title: str | None, author: str | None) -> list[str]:
    """The visible document, which is what most readers will ever see.

    Written as real prose rather than a placeholder: the surface of this file is a
    document in its own right, and a reader who never unpacks the intelligence
    layer should still be handed something that reads.
    """
    heading = title or project
    lines = [heading]
    if author:
        lines.append(author)
    lines.append(
        "This document is a conforming OOXML file and also a container. Alongside the "
        "text you are reading it carries the complete source tree of the project that "
        "produced it, bound by a manifest whose digest covers every part of this "
        "package. Opening it in any word processor shows this page; opening it with "
        "docxplus recovers the project."
    )
    lines.append(
        "The carried tree excludes build products and virtual environments, which are "
        "reproducible from the sources that are carried."
    )
    return lines


def export_project(
    project_root: Path,
    output_dir: Path,
    *,
    project: str,
    title: str | None = None,
    author: str | None = None,
    signing_key_hex: str | None = None,
    password: str | None = None,
) -> ExportResult:
    """Write ``<project>.docx`` and ``<project>.docxplus`` carrying ``project_root``.

    Both names hold identical bytes; the second exists so a reader can tell from a
    filename that the intelligence layer is there, without which the capability is
    discoverable only by trying. Returns an :class:`ExportResult` describing what
    happened, including the reason when nothing did.
    """
    if not _DOCXPLUS_AVAILABLE or DocxPlusBuilder is None or write_document is None:
        reason = f"docxplus is not installed; install the optional extra with: {INSTALL_HINT}"
        logger.info("Skipping docxplus export — %s", reason)
        return ExportResult(available=False, skipped_reason=reason)

    if not project_root.is_dir():
        reason = f"project root does not exist: {project_root}"
        logger.warning("Skipping docxplus export — %s", reason)
        return ExportResult(available=True, skipped_reason=reason)

    output_dir.mkdir(parents=True, exist_ok=True)

    builder = DocxPlusBuilder(
        paragraphs=_cover_paragraphs(project, title, author),
        title=title or project,
    )
    builder.add_project(
        project,
        project_root,
        **({"password": password} if password else {}),
    )

    signed = False
    if signing_key_hex:
        builder.sign(bytes.fromhex(signing_key_hex.strip()))
        signed = True

    written = write_document(builder.build(), output_dir / f"{project}.docx")

    carried = sum(
        1
        for path in project_root.rglob("*")
        if path.is_file() and not (EXCLUDED_DIRS & set(path.relative_to(project_root).parts))
    )
    result = ExportResult(available=True, written=list(written), carried_files=carried, signed=signed)
    (output_dir / "docxplus_export.json").write_text(json.dumps(result.to_dict(), indent=2) + "\n")
    logger.info(
        "docxplus export wrote %s carrying %d files (signed=%s)",
        ", ".join(p.name for p in written),
        carried,
        signed,
    )
    return result
