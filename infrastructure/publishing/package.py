"""Publication package creation, submission checklists, and readiness validation.

This module serves as the entry point, re-exporting from focused submodules:
- checklist: Submission checklist generation
- announcement: DOI badges and publication announcements
- readiness: Publication readiness validation
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.files.operations import calculate_file_hash
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.models import PublicationMetadata

# Re-exports for backwards compatibility
from infrastructure.publishing.announcement import (  # noqa: F401
    create_publication_announcement,
    generate_doi_badge,
)
from infrastructure.publishing.checklist import (  # noqa: F401
    create_submission_checklist,
)
from infrastructure.publishing.readiness import (  # noqa: F401
    validate_publication_readiness,
)

logger = get_logger(__name__)


def create_publication_package(output_dir: Path, metadata: PublicationMetadata) -> dict[str, Any]:
    """Create a publication package with all necessary files.

    Args:
        output_dir: Output directory containing generated files
        metadata: Publication metadata

    Returns:
        Dictionary with package information
    """
    # Collect files to include
    package_files = []

    # PDF files
    pdf_dir = output_dir / "pdf"
    if pdf_dir.exists():
        for pdf_file in pdf_dir.glob("*.pdf"):
            package_files.append(pdf_file)

    # Source files
    source_files = ["README.md", "pyproject.toml", "LICENSE"]

    for source_file in source_files:
        file_path = Path(source_file)
        if file_path.exists():
            package_files.append(file_path)

    # Calculate package hash and collect included files
    file_hashes = []
    files_included = []
    for file_path in package_files:
        if file_path.exists():
            file_hash = calculate_file_hash(file_path)
            if file_hash:
                file_hashes.append(file_hash)
            files_included.append(str(file_path))

    package_hash = ""
    if file_hashes:
        combined_hash = "".join(sorted(file_hashes))
        package_hash = hashlib.sha256(combined_hash.encode()).hexdigest()

    return {
        "package_name": f"{metadata.title.replace(' ', '_').lower()}",
        "files_included": files_included,
        "metadata": asdict(metadata),
        "package_hash": package_hash,
        "created_at": datetime.now().isoformat(),
    }
