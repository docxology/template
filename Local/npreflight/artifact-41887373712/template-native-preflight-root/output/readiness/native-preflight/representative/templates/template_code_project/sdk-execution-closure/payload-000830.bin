"""Shared pandoc argument assembly for the combined-edition writers.

The DOCX, EPUB, and ebook lanes must hand one manuscript to pandoc under the
same resource-path, numbering-filter, crossref, and citation contract, or the
same source acquires different images, numbers, or citations per edition.
Centralising the assembly means a lane that forgets one leg fails the wiring
tests instead of silently dropping images or renumbering a single edition.

Ordering contract
-----------------
Resource paths come first, then the formalism filter (which must consume
``[@def:x]`` citations before the citation machinery sees them), then
``--filter pandoc-crossref``, then ``--citeproc`` plus one ``--bibliography=``
argument per path. This matches the ordering contract documented in
``_pandoc_filters`` and keeps every edition's numbering identical.

Resource-path contract
----------------------
Combined manuscripts reference figures as ``figures/<name>`` relative to the
manuscript directory, so pandoc resolves them against the *parent* of the
figures dir — a resource path that lists only the figures dir itself makes
pandoc silently drop every image (confirmed against real manuscripts; see the
``rewrite_pdf_figure_refs_to_raster`` notes for the related EPUB hazard).
Every caller therefore passes the manuscript/combined-markdown directory,
the figures dir, **and** the figures dir's parent.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Sequence
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._bibliography import pandoc_bibliography_args
from infrastructure.rendering._pandoc_filters import formalism_filter_args

logger = get_logger(__name__)


def combined_pandoc_args(
    resource_dirs: Sequence[Path],
    bibliographies: Sequence[Path],
    *,
    edition: str,
    which: Callable[[str], str | None] | None = None,
) -> list[str]:
    """Assemble the shared combined-edition pandoc extra args.

    Args:
        resource_dirs: Pandoc resource-path directories, in order. Callers
            must include the manuscript (or combined-markdown) directory, the
            figures dir, and the figures dir's parent — see the module
            docstring for why the parent leg cannot be omitted.
        bibliographies: Resolved bibliography paths. When non-empty, the
            ``--citeproc`` flag plus one ``--bibliography=`` argument per
            path (in the resolver's canonical order) is appended.
        edition: Human-readable edition name used in the missing-crossref
            warning (``DOCX``, ``EPUB``, ``ebook``).
        which: Injectable ``shutil.which`` resolver. An injection seam for
            the missing-crossref test, mirroring the dependency-injection
            style ``render_combined_epub`` uses for its renderer; production
            callers omit it.

    Returns:
        The assembled arguments in the module-documented contract order.

    Raises:
        FormalismFilterMissingError: If the shipped formalism Lua filter is
            absent from the package (broken or partial installation).
    """
    args = [f"--resource-path={resource_dir}" for resource_dir in resource_dirs]
    args.extend(formalism_filter_args())

    # Without pandoc-crossref, {#fig-x}-style cross-reference targets (e.g. a
    # manual "[see Figure](#fig-x)" link) don't reliably resolve to a real
    # anchor — confirmed via epubcheck RSC-012 "Fragment identifier is not
    # defined" on a real manuscript. The binary is optional: warn and carry on
    # rather than fail, but name the affected edition so the degraded lane is
    # identifiable in logs.
    resolver = which or shutil.which
    crossref = resolver("pandoc-crossref")
    if crossref:
        args.extend(["--filter", crossref])
    else:
        logger.warning(
            "pandoc-crossref not on PATH; %s @fig:/@sec:/@tbl:/@eq: will not resolve.",
            edition,
        )

    if bibliographies:
        args.append("--citeproc")
        args.extend(pandoc_bibliography_args(bibliographies))
    return args


__all__ = ["combined_pandoc_args"]
