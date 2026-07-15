"""tools_invoker.py — Discover and validate tools from tools/templates/ exemplars.

All functions use graceful fallbacks when paths are absent.

Repo-root discovery: 4 levels up from this file.
"""

from __future__ import annotations

import logging
import pathlib

import yaml

from .type_defs import ToolEntry, ToolEntryWithValidation, ToolValidationResult

__all__ = [
    "discover_tools",
    "get_tool_entrypoints",
    "validate_tool_scripts_exist",
    "get_tools_root",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Repo-root resolution
# ---------------------------------------------------------------------------


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[4]


def _tools_root() -> pathlib.Path:
    bundled = (
        pathlib.Path(__file__).resolve().parents[1] / "_template_resources" / "tools" / "templates"
    )
    if bundled.is_dir():
        return bundled
    return _repo_root() / "tools" / "templates"


# Expose for test use (not part of the main public API)
get_tools_root = _tools_root


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_tools(*, templates_root: pathlib.Path | None = None) -> list[ToolEntry]:
    """Discover all tool manifests under ``tools/templates/``.

    Returns a list of :class:`ToolEntry` dicts, each with:

    - ``name``: str (directory name)
    - ``path``: :class:`pathlib.Path` (directory path)
    - ``manifest``: parsed tools.yaml dict, or ``None`` if unreadable
    """
    root = templates_root if templates_root is not None else _tools_root()
    if not root.is_dir():
        logger.warning("tools root not found: %s", root)
        return []

    results: list[ToolEntry] = []
    for tool_dir in sorted(root.iterdir()):
        if not tool_dir.is_dir():
            continue
        manifest_path = tool_dir / "tools.yaml"
        manifest: object | None = None
        if manifest_path.exists():
            try:
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
                logger.warning("tools_invoker: could not parse %s — %s", manifest_path, exc)
        else:
            logger.warning("tools_invoker: no tools.yaml in %s", tool_dir)

        results.append(ToolEntry(name=tool_dir.name, path=tool_dir, manifest=manifest))

    return results


def get_tool_entrypoints(
    tool_name: str,
    *,
    templates_root: pathlib.Path | None = None,
) -> list[str]:
    """Return the list of entrypoint script paths declared in a tool's manifest.

    Paths are relative to the tool directory (as declared in ``tools.yaml``).
    Returns an empty list if the tool or its manifest is absent.
    """
    tools_root = templates_root if templates_root is not None else _tools_root()
    tool_dir = tools_root / tool_name
    manifest_path = tool_dir / "tools.yaml"

    if not manifest_path.exists():
        logger.warning("get_tool_entrypoints: no tools.yaml for %s", tool_name)
        return []

    try:
        raw: object = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        logger.warning("get_tool_entrypoints: parse error — %s", exc)
        return []

    if not isinstance(raw, dict):
        return []
    return list(raw.get("entrypoints", []))


def validate_tool_scripts_exist(
    tool_name: str,
    *,
    templates_root: pathlib.Path | None = None,
) -> ToolValidationResult:
    """Verify that every entrypoint declared in a tool's manifest exists on disk.

    Returns a :class:`ToolValidationResult` with:

    - ``tool``: str
    - ``entrypoints``: list[str] declared entrypoints
    - ``missing``: list[str] missing scripts
    - ``valid``: ``True`` iff no scripts are missing
    """
    tools_root = templates_root if templates_root is not None else _tools_root()
    tool_dir = tools_root / tool_name
    entrypoints = get_tool_entrypoints(tool_name, templates_root=templates_root)
    missing: list[str] = []

    for ep in entrypoints:
        full_path = tool_dir / ep
        if not full_path.exists():
            missing.append(ep)

    return ToolValidationResult(
        tool=tool_name,
        entrypoints=entrypoints,
        missing=missing,
        valid=len(missing) == 0,
    )


def discover_tools_with_validation(
    *,
    templates_root: pathlib.Path | None = None,
) -> list[ToolEntryWithValidation]:
    """Discover all tools and attach validation results.

    Convenience wrapper that combines :func:`discover_tools` and
    :func:`validate_tool_scripts_exist` in a single pass.

    Returns a list of :class:`ToolEntryWithValidation` dicts.
    """
    results: list[ToolEntryWithValidation] = []
    for entry in discover_tools(templates_root=templates_root):
        validation = validate_tool_scripts_exist(
            entry["name"],
            templates_root=templates_root,
        )
        results.append(
            ToolEntryWithValidation(
                name=entry["name"],
                path=entry["path"],
                manifest=entry["manifest"],
                validation=validation,
            )
        )
    return results
