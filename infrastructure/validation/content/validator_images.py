"""Markdown image reference validation."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging import DiagnosticEvent, DiagnosticSeverity
from infrastructure.validation.content.diagnostic_codes import MarkdownCode

IMG_PATTERN = re.compile(r"!\[[^\]]*\]\(([^\)]+)\)")


def validate_images(
    md_paths: list[str],
    repo_root: str | Path,
    extra_search_dirs: list[str | Path] | None = None,
) -> list[DiagnosticEvent]:
    """Validate that all referenced images exist in the filesystem."""
    repo_root_path = Path(repo_root)
    problems: list[DiagnosticEvent] = []

    search_dirs: list[Path] = []
    if extra_search_dirs:
        search_dirs.extend(Path(d) for d in extra_search_dirs)

    if md_paths:
        md_dir = Path(md_paths[0]).parent
        project_root = md_dir.parent
        for candidate in [
            project_root / "output" / "figures",
            project_root / "figures",
        ]:
            if candidate.is_dir() and candidate not in search_dirs:
                search_dirs.append(candidate)

    for path in md_paths:
        path_obj = Path(path)
        text = path_obj.read_text(encoding="utf-8")
        for img in IMG_PATTERN.findall(text):
            img_clean = img.split()[0]
            abs_path = (path_obj.parent / img_clean).resolve()
            if abs_path.exists():
                continue

            img_basename = Path(img_clean).name
            found = False
            for search_dir in search_dirs:
                if (search_dir / img_basename).exists():
                    found = True
                    break
            if not found:
                display_path: Path
                try:
                    display_path = Path(path).relative_to(repo_root_path)
                except ValueError:
                    display_path = path_obj
                problems.append(
                    DiagnosticEvent(
                        severity=DiagnosticSeverity.ERROR,
                        category="MARKDOWN_IMAGE",
                        message=f"Missing referenced image: '{img_clean}'",
                        code=MarkdownCode.IMG_MISSING,
                        file_path=str(display_path),
                        fix_suggestion="Ensure the image file exists in the specified relative path or figures directory.",
                    )
                )
    return problems
