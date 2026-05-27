"""Pre-render validation helpers for combined PDF rendering."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging import DiagnosticSeverity
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_preflight import check_brace_balance
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.content.markdown_validator import (
    validate_citations,
    validate_pandoc_pitfalls,
)

logger = get_logger(__name__)


def verify_figure_references(tex_content: str, figures_dir: Path) -> None:
    """Verify that all \\includegraphics references resolve to existing files."""
    fig_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"
    referenced_figures = re.findall(fig_pattern, tex_content)

    if not referenced_figures:
        return

    logger.info(f"Verifying {len(referenced_figures)} figure reference(s)...")
    missing_figures: list[str] = []
    found_figures: list[str] = []

    def _figure_candidates(fig_ref: str) -> list[Path]:
        ref = fig_ref.strip()
        if ref.startswith(r"\detokenize{"):
            ref = ref.removeprefix(r"\detokenize{").rstrip("}")
        ref_path = Path(ref)
        candidates: list[Path] = []
        if ref_path.is_absolute():
            candidates.append(ref_path)
        parts = ref_path.parts
        if "figures" in parts:
            figure_index = parts.index("figures")
            candidates.append(figures_dir.joinpath(*parts[figure_index + 1 :]))
        candidates.extend([figures_dir / ref_path, figures_dir / ref_path.name])
        return [Path(unicodedata.normalize("NFC", str(candidate))) for candidate in candidates]

    for fig_ref in referenced_figures:
        display_name = fig_ref.split("/")[-1].rstrip("}")
        existing_path = next((candidate for candidate in _figure_candidates(fig_ref) if candidate.exists()), None)

        if existing_path is not None:
            found_figures.append(display_name)
            logger.debug(f"  ✓ Found: {display_name}")
        else:
            missing_figures.append(display_name)
            logger.warning(f"  ✗ Missing: {display_name}")
            if figures_dir.exists():
                similar = [
                    f.name
                    for f in figures_dir.rglob("*")
                    if f.name.lower().startswith(display_name.split(".")[0].lower())
                ]
                if similar:
                    logger.debug(f"    Similar files found: {', '.join(similar)}")

    logger.info(f"  Found: {len(found_figures)}/{len(referenced_figures)} figures")
    if missing_figures:
        logger.warning(f"  Missing {len(missing_figures)} figure(s): {', '.join(missing_figures[:5])}")
        if len(missing_figures) > 5:
            logger.warning(f"  ... and {len(missing_figures) - 5} more missing figures")


def prevalidate_markdown(combined_md: Path) -> tuple[list[str], str]:
    """Pre-validate combined markdown for common issues.

    Returns:
        Tuple of (validation_errors, md_content)
    """
    validation_errors: list[str] = []
    md_content = ""
    if combined_md.exists():
        try:
            md_content = combined_md.read_text(encoding="utf-8")
            validation_errors = check_brace_balance(md_content)
            if validation_errors:
                logger.warning(f"Pre-validation found {len(validation_errors)} potential issue(s):")
                for err in validation_errors:
                    logger.warning(f"  • {err}")
                logger.info("  (These are warnings - PDF generation will proceed)")
        except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001
            logger.debug(f"Pre-validation check failed: {e}")
    return validation_errors, md_content


def prevalidate_source_markdown(
    source: Path | list[Path] | list[str],
    repo_root: Path | None = None,
    bib_file: str | Path | list[str | Path] | None = None,
) -> None:
    """Hard-gate the combined-PDF render on source-markdown integrity.

    Runs the two render-blocking checks against the actual files about to
    be combined and rendered (not the post-Pandoc ``.tex``), so file paths
    in error messages point to the editable sources:

    * :func:`validate_pandoc_pitfalls` — bare ``|word|`` in prose and
      ``\\|`` inside Markdown table cells (Pandoc converts both to
      ``\\mid`` which fails to render U+2223 in text mode).
    * :func:`validate_citations` — every ``[@key]`` resolves in the manuscript
      ``*.bib`` union (or the explicit ``bib_file`` list when supplied).

    Both classes of finding block the render under the strict gate;
    pitfall WARNINGS are promoted to blockers here because they
    materialise downstream as silent ``Missing character`` warnings +
    ``U+FFFD`` glyphs in the rendered PDF — exactly the class of failure
    this gate exists to prevent.

    Args:
        source: Either a manuscript directory (``Path``) — scanned with
            :func:`discover_markdown_files` (``scope='tree'``) — or an explicit iterable of
            markdown file paths.
        repo_root: Repository root for relative-path display in error
            messages. Defaults to a best-effort guess based on the first
            source path.
        bib_file: Explicit BibTeX path(s). ``None`` unions every ``*.bib`` next
            to the first markdown source (same default as combined-PDF render).

    Raises:
        RenderingError: When any pitfall or undefined citation is found.
            The exception message lists every blocker with its file path.
    """
    if isinstance(source, Path):
        if not source.exists():
            return
        paths: list[str] = [str(path) for path in discover_markdown_files(source, scope="tree")]
        anchor_dir = source
    else:
        paths = [str(p) for p in source]
        anchor_dir = Path(paths[0]).parent if paths else Path.cwd()

    if not paths:
        return

    if repo_root is None:
        repo_root = anchor_dir.parents[2] if len(anchor_dir.parents) >= 3 else anchor_dir

    problems = validate_pandoc_pitfalls(paths, repo_root) + validate_citations(paths, repo_root, bib_file=bib_file)
    if not problems:
        return

    # Promote everything to render-blocker under the strict gate.
    blockers = problems
    rendered = "\n".join(f"  [{p.file_path}] {p.message}" for p in blockers)
    by_severity = {
        DiagnosticSeverity.ERROR: sum(1 for p in blockers if p.severity == DiagnosticSeverity.ERROR),
        DiagnosticSeverity.WARNING: sum(1 for p in blockers if p.severity == DiagnosticSeverity.WARNING),
    }
    raise RenderingError(
        f"Pre-render validation failed with {len(blockers)} blocker(s) "
        f"({by_severity[DiagnosticSeverity.ERROR]} error / "
        f"{by_severity[DiagnosticSeverity.WARNING]} warning) before "
        f"Pandoc/xelatex runs:\n{rendered}\n"
        "Fix each occurrence in the listed source markdown file(s) and re-run."
    )
