"""Shared manuscript variable substitution utilities.

Provides the canonical implementation of the ``{{TOKEN}}`` injection pattern
used by every project in this repository to hydrate manuscript markdown with
computed values before PDF rendering.

Usage pattern (project-level)::

    from infrastructure.rendering.manuscript_injection import (
        substitute_manuscript_text,
        write_resolved_manuscript_tree,
    )

    variables: dict[str, str] = {"TOTAL_PAPERS": "42", "QUERY": "fep"}
    resolved, unresolved = substitute_manuscript_text(raw_text, variables)
    write_resolved_manuscript_tree(project_root, variables)

The PDF-rendering pipeline reads from ``output/manuscript/`` when that
directory contains markdown (see
:func:`infrastructure.rendering.pipeline._resolve_manuscript_dir`).
"""

import re
import shutil
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.project_paths import resolve_source_manuscript_dir

logger = get_logger(__name__)

# Matches ``{{UPPERCASE_KEY}}`` tokens only.
# Requires an uppercase ASCII letter as the first character so Mermaid-diagram
# node labels such as ``KW{{For each keyword}}`` and documentation examples
# such as ``{{CONFIG_*}}`` are never matched.
_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# Markdown files that live in ``manuscript/`` for developer / agent guidance
# only.  They intentionally contain literal ``{{TOKEN}}`` examples and must
# not be substituted or copied to ``output/manuscript/`` where the PDF
# renderer would treat their example tokens as rendering targets.
EXCLUDED_DOC_FILENAMES: frozenset[str] = frozenset({"AGENTS.md", "README.md", "SYNTAX.md"})


def substitute_manuscript_text(
    text: str,
    variables: dict[str, str],
) -> tuple[str, list[str]]:
    """Replace ``{{KEY}}`` placeholders in *text* with values from *variables*.

    Args:
        text: Markdown text containing ``{{UPPERCASE_KEY}}`` markers.
        variables: Mapping from plain UPPERCASE_KEY strings (without braces)
            to their replacement values.

    Returns:
        ``(resolved_text, unresolved_keys)`` — *unresolved_keys* lists every
        token name whose ``{{KEY}}`` marker had no matching entry in
        *variables* and was therefore left unchanged in the output.
    """
    unresolved: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        unresolved.append(key)
        return match.group(0)

    resolved = _TOKEN_RE.sub(_replace, text)
    return resolved, unresolved


def write_resolved_manuscript_tree(
    project_root: Path | str,
    variables: dict[str, str],
) -> Path:
    """Write resolved copies of ``manuscript/*.md`` into ``output/manuscript/``.

    Each ``.md`` file in ``manuscript/`` is written to ``output/manuscript/``
    with all ``{{TOKEN}}`` placeholders replaced from *variables*.
    Files listed in :data:`EXCLUDED_DOC_FILENAMES` are excluded — they contain
    literal token examples that must not be modified.  Auxiliary files
    (``config.yaml``, ``*.bib``) are copied verbatim.

    Unresolved tokens are logged as warnings and preserved literally in the
    output so they remain visible if the rendered PDF is inspected.

    The PDF-rendering pipeline prefers ``output/manuscript/`` when it contains
    markdown (see :func:`infrastructure.rendering.pipeline._resolve_manuscript_dir`).

    Args:
        project_root: Root directory of the project (contains ``manuscript/``
            and ``output/``).
        variables: Mapping from plain UPPERCASE_KEY strings to replacement
            values.

    Returns:
        Path to the ``output/manuscript/`` directory.
    """
    root = Path(project_root)
    manuscript_dir = resolve_source_manuscript_dir(root)
    out_dir = root / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_unresolved: list[str] = []
    files_written = 0

    for stale in list(out_dir.glob("*.md")) + list(out_dir.glob("*.bib")):
        stale.unlink()
    for stale_name in ("config.yaml", "preamble.md"):
        stale = out_dir / stale_name
        if stale.exists():
            stale.unlink()

    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name in EXCLUDED_DOC_FILENAMES:
            logger.debug("Skipping documentation file: %s", md_file.name)
            continue
        text = md_file.read_text(encoding="utf-8")
        resolved, unresolved = substitute_manuscript_text(text, variables)
        if unresolved:
            logger.warning(
                "Unresolved {{TOKEN}} in %s: %s",
                md_file.name,
                ", ".join(unresolved),
            )
            all_unresolved.extend(unresolved)
        out_dir.joinpath(md_file.name).write_text(resolved, encoding="utf-8")
        files_written += 1

    for aux in ("config.yaml", "preamble.md"):
        src = manuscript_dir / aux
        if src.is_file():
            shutil.copy2(src, out_dir / aux)

    for bib in sorted(manuscript_dir.glob("*.bib")):
        shutil.copy2(bib, out_dir / bib.name)

    logger.info(
        "Resolved %d manuscript file(s) to %s%s",
        files_written,
        out_dir,
        f"; {len(all_unresolved)} unresolved token(s)" if all_unresolved else "",
    )

    try:
        from infrastructure.publishing.transmission_bookends import write_transmission_bookends

        repo_root = root.parent.parent if root.parent.name == "projects" else root.parent
        write_transmission_bookends(root, root.name, repo_root=repo_root)
    except Exception as exc:  # noqa: BLE001 — bookends must not block hydration
        logger.warning("Transmission bookend generation skipped: %s", exc)

    return out_dir
