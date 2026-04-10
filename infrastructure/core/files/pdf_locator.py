"""Locate combined-manuscript PDFs across the three canonical project output paths.

Stage 4 (validate) may run before or after Stage 5 (copy outputs), so the combined
PDF can legitimately live in any of three places. This helper is the single source
of truth for that search and is reused by output validators, reporters, and any
future consumer that needs the same resolution rule.
"""

from __future__ import annotations

from pathlib import Path


def find_last_output_segment_index(path_parts: tuple[str, ...]) -> int | None:
    """Return the index of the **last** ``"output"`` segment in *path_parts*.

    Uses the last occurrence (``rindex`` semantics) so that a parent directory
    named ``output`` cannot corrupt the derivation of the repository root.

    Args:
        path_parts: A tuple of path segments, e.g. ``Path(...).parts``.

    Returns:
        The zero-based index of the last ``"output"`` segment, or ``None`` if
        the tuple contains no segment literally equal to ``"output"``.
    """
    if "output" not in path_parts:
        return None
    return len(path_parts) - 1 - path_parts[::-1].index("output")


def find_combined_pdf(output_dir: Path, project_name: str) -> tuple[Path, float] | None:
    """Locate the combined PDF for *project_name*, checking three canonical locations.

    Search order:
    1. ``output_dir/{project_name}_combined.pdf`` (root, post-copy layout)
    2. ``output_dir/pdf/{project_name}_combined.pdf`` (original generation location)
    3. ``projects/{project_name}/output/pdf/{project_name}_combined.pdf`` (source,
       pre-copy — used by Stage 4 validation before Stage 5 runs)

    Args:
        output_dir: The output directory to search. May be either the top-level
            ``output/{project_name}`` (post-copy) or a source
            ``projects/{project_name}/output`` directory.
        project_name: The project slug used to construct the PDF filename.

    Returns:
        A ``(path, size_mb)`` tuple if a non-empty PDF is found, else ``None``.
    """
    filename = f"{project_name}_combined.pdf"

    # 1. Root directory (post-copy layout, e.g. output/{project_name}/foo_combined.pdf)
    root_pdf = output_dir / filename
    if root_pdf.exists() and root_pdf.stat().st_size > 0:
        return root_pdf, root_pdf.stat().st_size / (1024 * 1024)

    # 2. pdf/ subdirectory (original generation location)
    pdf_dir = output_dir / "pdf"
    if pdf_dir.exists():
        pdf_in_dir = pdf_dir / filename
        if pdf_in_dir.exists() and pdf_in_dir.stat().st_size > 0:
            return pdf_in_dir, pdf_in_dir.stat().st_size / (1024 * 1024)

    # 3. Source project directory (for Stage 4 validation before copy)
    path_parts = output_dir.parts
    output_idx = find_last_output_segment_index(path_parts)
    if output_idx is not None:
        repo_root = Path(*path_parts[:output_idx])
        # Preserve any sub-path qualifiers after the 'output' segment so a caller
        # like output/foo/bar maps to projects/foo/bar/output/pdf.
        qualified_path = "/".join(path_parts[output_idx + 1:])
        source_pdf_dir = repo_root / "projects" / qualified_path / "output" / "pdf"
    else:
        source_pdf_dir = output_dir.parent.parent / "projects" / project_name / "output" / "pdf"

    if source_pdf_dir.exists():
        source_pdf = source_pdf_dir / filename
        if source_pdf.exists() and source_pdf.stat().st_size > 0:
            return source_pdf, source_pdf.stat().st_size / (1024 * 1024)

    return None
