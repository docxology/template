"""Prepare a LaTeX-source tarball for manual arXiv upload."""

from __future__ import annotations

import shutil
import tarfile
from datetime import datetime
from pathlib import Path

from infrastructure.publishing.models import PublicationMetadata


def prepare_arxiv_submission(output_dir: Path, metadata: PublicationMetadata) -> Path:
    """Assemble a LaTeX-source submission package and tar it for manual arXiv upload.

    Collects, into ``output_dir/arxiv_submission/`` and then an
    ``arxiv_submission_YYYYMMDD.tar.gz`` tarball written under ``output_dir``:

    * ``.tex``, ``.bib``, ``.cls``, ``.bst`` files and any ``figures/`` directory
      from the sibling manuscript directory (``output_dir/../manuscript/``);
    * every rendered ``.tex`` found anywhere under ``output_dir`` (LaTeX produced
      at render time), and the optional ``.bbl`` under ``output_dir/pdf/``.

    .. warning::

       arXiv accepts **LaTeX source**, not a PDF. Template manuscripts are
       authored in Markdown and compiled straight to PDF, so ``manuscript/``
       usually contains **no** ``.tex`` and the render step does not persist one
       under ``output/`` by default. When no ``.tex`` is present in either
       location, the resulting tarball is a **references/figures-only partial
       package** (typically just ``references.bib``): you must add the compiled
       ``.tex`` yourself before arXiv will accept the submission. Inspect the
       returned tarball to confirm a ``.tex`` is present when you intend to
       upload directly.

    Returns the path to the created ``.tar.gz`` (always created, even when the
    package is partial).
    """
    submission_dir = output_dir / "arxiv_submission"
    if submission_dir.exists():
        shutil.rmtree(submission_dir)
    submission_dir.mkdir()

    tex_dir = output_dir.parent / "manuscript"
    if tex_dir.exists():
        for item in tex_dir.glob("*"):
            if item.is_file() and item.suffix in [".tex", ".bib", ".cls", ".bst"]:
                shutil.copy2(item, submission_dir)
            elif item.is_dir() and item.name in ["figures"]:
                shutil.copytree(item, submission_dir / item.name)

    # Include any LaTeX rendered at build time: Markdown manuscripts have no .tex
    # in manuscript/, but a rendered .tex may exist under output/ (e.g. output/pdf/).
    # Skip anything already inside the submission dir and never overwrite a file
    # already copied from manuscript/.
    for rendered_tex in sorted(output_dir.rglob("*.tex")):
        if submission_dir in rendered_tex.parents:
            continue
        target = submission_dir / rendered_tex.name
        if not target.exists():
            shutil.copy2(rendered_tex, target)

    bbl_file = output_dir / "pdf" / f"{metadata.title.replace(' ', '_')}.bbl"
    if bbl_file.exists():
        shutil.copy2(bbl_file, submission_dir)

    tar_path = output_dir / f"arxiv_submission_{datetime.now().strftime('%Y%m%d')}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(submission_dir, arcname="")

    return tar_path
