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
:func:`infrastructure.rendering.pipeline.resolve_manuscript_dir`).
"""

import re
import hashlib
import json
from collections.abc import Callable
import shutil
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined, unlink_confined
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
EXCLUDED_DOC_FILENAMES: frozenset[str] = frozenset({"AGENTS.md", "MANUSCRIPT_STATUS.md", "README.md", "SYNTAX.md"})
# MANUSCRIPT_STATUS.md (2026-08-30 convention): every manuscript directory
# carries a status ledger; it is repository documentation, never a
# rendered section.


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
    markdown (see :func:`infrastructure.rendering.pipeline.resolve_manuscript_dir`).

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
        from infrastructure.transmission.transmission_bookends import write_transmission_bookends

        repo_root = root.parent.parent if root.parent.name == "projects" else root.parent
        write_transmission_bookends(root, root.name, repo_root=repo_root)
    except Exception as exc:  # noqa: BLE001 — bookends must not block hydration
        logger.warning("Transmission bookend generation skipped: %s", exc)

    return out_dir


_HYDRATION_MANIFEST = "hydration_manifest.json"
_HYDRATION_SCHEMA = "template-hydrated-manuscript/v1"
_HYDRATION_FILE_BYTES = 8 * 1024 * 1024
_HYDRATION_TOTAL_BYTES = 64 * 1024 * 1024
_HYDRATION_MANIFEST_BYTES = 512 * 1024


def _hydration_member(name: str) -> bool:
    """Source code owns numbered sections and these finite rendering auxiliaries."""
    return (
        name in {"config.yaml", "preamble.md", "references.bib"}
        or re.fullmatch(r"[0-9]{2}[a-z]?_.+\.md", name) is not None
    )


def validate_project_selection(project_root: Path, supplied: str) -> Path:
    """Admit only the executing project, never a second project or path traversal."""
    root = project_root.absolute()
    if root.is_symlink() or root.resolve(strict=True) != root:
        raise ValueError("project selection requires its actual regular project root")
    allowed = {root.name, f"{root.parent.name}/{root.name}"}
    if supplied not in allowed:
        raise ValueError(f"this project-local entrypoint only supports {sorted(allowed)!r}; received {supplied!r}")
    return root


def validate_hydration_paths(project_root: Path) -> None:
    """Refuse linked input/output directories before project variable computation."""
    root = validate_project_selection(project_root, project_root.name)
    source = root / "manuscript"
    if not source.is_dir() or source.is_symlink():
        raise ValueError("hydration requires a regular source manuscript directory")
    entries = list(source.iterdir())
    if len(entries) > 512 or any(path.is_symlink() for path in entries):
        raise ValueError("hydration refuses linked or unbounded manuscript source entries")
    for directory in (root / "output", root / "output" / "manuscript"):
        if directory.is_symlink() or directory.exists() and not directory.is_dir():
            raise ValueError("hydration refuses linked or non-directory output paths")


def hydrate_manuscript_tree(
    project_root: Path,
    render: Callable[[str, str], str],
    *,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Prepare every source before confined writes; retain unrelated destination files.

    ``render(filename, content)`` owns the project's substitution and strictness.
    Source code admits numbered sections and config.yaml/preamble.md/references.bib;
    a manifest records their prior bytes but cannot grant new deletion authority.
    Legacy numbered sections are removed without a manifest; unknown files stay.
    Dry runs perform the same validation and never create output directories.
    """
    validate_hydration_paths(project_root)
    root = project_root.absolute()
    source = root / "manuscript"
    destination = root / "output" / "manuscript"
    entries = sorted(source.iterdir())
    if len(entries) > 512:
        raise ValueError("hydration source exceeds its file-count budget")
    prepared: dict[str, bytes] = {}
    originals: dict[str, bytes] = {}
    changed = injected = total = 0
    for path in entries:
        if path.is_symlink():
            raise ValueError("hydration refuses linked manuscript source entries")
        if not path.is_file() or path.name in EXCLUDED_DOC_FILENAMES or not _hydration_member(path.name):
            continue
        content = read_bytes_confined(root, path, max_bytes=_HYDRATION_FILE_BYTES)
        originals[path.name] = content
        if path.suffix == ".md":
            text = content.decode("utf-8")
            result = render(path.name, text)
            if not isinstance(result, str):
                raise ValueError("manuscript renderer must return text")
            changed += result != text
            injected += len(re.findall(r"\{\{(\w+)\}\}", text)) - len(re.findall(r"\{\{(\w+)\}\}", result))
            content = result.encode("utf-8")
        if len(content) > _HYDRATION_FILE_BYTES:
            raise ValueError("hydrated member exceeds its file-size budget")
        total += len(content) + len(originals[path.name])
        if total > _HYDRATION_TOTAL_BYTES:
            raise ValueError("hydration exceeds its aggregate byte budget")
        prepared[path.name] = content
    previous: dict[str, str] = {}
    manifest_path = destination / _HYDRATION_MANIFEST
    stale: list[tuple[Path, str]] = []
    if destination.exists():
        observed = sorted(destination.iterdir())
        if len(observed) > 1024:
            raise ValueError("hydration destination exceeds its file-count budget")
        if any(path.is_symlink() for path in observed):
            raise ValueError("hydration refuses linked destination entries")
        if manifest_path.exists():
            manifest = json.loads(read_bytes_confined(root, manifest_path, max_bytes=_HYDRATION_MANIFEST_BYTES))
            if (
                not isinstance(manifest, dict)
                or set(manifest) != {"schema_version", "files"}
                or manifest["schema_version"] != _HYDRATION_SCHEMA
                or not isinstance(manifest["files"], dict)
                or len(manifest["files"]) > 512
            ):
                raise ValueError("hydration ownership manifest is invalid")
            for name, digest in manifest["files"].items():
                if (
                    not isinstance(name, str)
                    or Path(name).name != name
                    or not _hydration_member(name)
                    or not isinstance(digest, str)
                    or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                ):
                    raise ValueError("hydration ownership manifest contains an invalid file binding")
                previous[name] = digest
        for path in observed:
            if path.name in prepared or path.name == _HYDRATION_MANIFEST:
                if not path.is_file():
                    raise ValueError("hydration target must be a regular file")
                continue
            if path.name in previous:
                content = read_bytes_confined(root, path, max_bytes=_HYDRATION_FILE_BYTES)
                if hashlib.sha256(content).hexdigest() != previous[path.name]:
                    raise ValueError("stale generated manuscript was edited; refusing removal")
                stale.append((path, previous[path.name]))
            elif not manifest_path.exists() and re.fullmatch(r"[0-9]{2}[a-z]?_.+\.md", path.name):
                content = read_bytes_confined(root, path, max_bytes=_HYDRATION_FILE_BYTES)
                stale.append((path, hashlib.sha256(content).hexdigest()))
    # Re-read through no-follow descriptors before any mutation, including dry runs.
    for name, content in originals.items():
        if read_bytes_confined(root, source / name, max_bytes=_HYDRATION_FILE_BYTES) != content:
            raise ValueError("manuscript source changed during hydration")
    manifest = {
        "schema_version": _HYDRATION_SCHEMA,
        "files": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(prepared.items())},
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    if len(manifest_bytes) > _HYDRATION_MANIFEST_BYTES:
        raise ValueError("hydration ownership manifest exceeds its byte budget")
    if dry_run:
        return changed, injected
    for name, content in prepared.items():
        atomic_write_bytes_confined(root, destination / name, content)
    for path, digest in stale:
        # This retains a late regular-file edit/replacement diagnostic. These
        # per-file writes/deletions are neither a tree transaction nor CAS.
        content = read_bytes_confined(root, path, max_bytes=_HYDRATION_FILE_BYTES)
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("stale generated manuscript changed before removal")
        unlink_confined(root, path)
    atomic_write_bytes_confined(root, manifest_path, manifest_bytes)
    return changed, injected
