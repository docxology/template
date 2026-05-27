"""Prepare a tarball for manual arXiv upload."""

from __future__ import annotations

import shutil
import tarfile
from datetime import datetime
from pathlib import Path

from infrastructure.publishing.models import PublicationMetadata


def prepare_arxiv_submission(output_dir: Path, metadata: PublicationMetadata) -> Path:
    """Prepare a submission package for arXiv upload."""
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

    bbl_file = output_dir / "pdf" / f"{metadata.title.replace(' ', '_')}.bbl"
    if bbl_file.exists():
        shutil.copy2(bbl_file, submission_dir)

    tar_path = output_dir / f"arxiv_submission_{datetime.now().strftime('%Y%m%d')}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(submission_dir, arcname="")

    return tar_path
