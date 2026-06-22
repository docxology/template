"""Machine-readable catalog of every agent-invocable CLI operation.

The skills module already proves the one discovery contract the whole package
should use — ``discover_* -> build_*_payload -> write_*_manifest ->
*_matches_discovery`` (see :mod:`infrastructure.skills.discovery`). That contract
covers ``SKILL.md`` *descriptors*, but it does not tell an agent **what it can
run**: which ``python -m infrastructure.<module>`` CLIs exist, what each is for,
which subcommands they expose, and what each package re-exports as its public
Python API. Today an agent must read prose (``AGENTS.md``) or scrape ``--help``.

This module closes that gap by cloning the exact same contract for *operations*:

* :func:`discover_operations` — enumerate invocable CLIs from the filesystem.
* :func:`build_operations_payload` — canonical JSON-serializable structure.
* :func:`write_operations_manifest` — write ``.cursor/operations_manifest.json``.
* :func:`operations_manifest_matches_discovery` — drift gate, identical in shape
  to :func:`infrastructure.skills.discovery.manifest_matches_discovery`.

Discovery is **purely static** — it parses source with :mod:`ast` and never
imports the target modules. That matters because many CLIs (rendering, llm,
steganography, …) only import cleanly when their optional dependency group is
installed; a registry that imported them would be fragile and environment
dependent. A CLI is "invocable via ``python -m X``" iff its package directory
contains ``__main__.py`` — a deterministic, dependency-free signal.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

__all__ = [
    "OperationDescriptor",
    "SubcommandInfo",
    "build_operations_payload",
    "discover_operations",
    "load_operations_manifest",
    "operation_descriptors_as_json_serializable",
    "operations_manifest_matches_discovery",
    "write_operations_manifest",
]

_MANIFEST_VERSION = 1

# Package roots scanned for ``__main__.py`` (relative to repo root).
DEFAULT_OPERATION_SEARCH_ROOTS: tuple[str, ...] = ("infrastructure",)


@dataclass(frozen=True, slots=True)
class SubcommandInfo:
    """One ``add_parser("name", help=...)`` subcommand discovered statically."""

    name: str
    help: str | None = None


@dataclass(frozen=True, slots=True)
class OperationDescriptor:
    """One agent-invocable CLI operation, discovered without importing it."""

    module: str
    """Dotted module path, e.g. ``infrastructure.validation.cli``."""
    invocation: str
    """How to run it, e.g. ``python -m infrastructure.validation.cli``."""
    source_path: str
    """Repo-relative POSIX path to the ``cli.py``/``__main__.py`` parsed."""
    purpose: str | None = None
    """First line of the CLI module docstring."""
    subcommands: tuple[SubcommandInfo, ...] = field(default_factory=tuple)
    exports: tuple[str, ...] = field(default_factory=tuple)
    """``__all__`` of the owning package's ``__init__.py`` (its public API)."""


def _dotted_path(repo_root: Path, package_dir: Path) -> str:
    """Return the dotted import path for a package directory under repo root."""
    rel = package_dir.resolve().relative_to(repo_root.resolve())
    return ".".join(rel.parts)


def _module_docstring_first_line(source: str) -> str | None:
    """Return the first non-empty line of a module docstring, if any."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    doc = ast.get_docstring(tree)
    if not doc:
        return None
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _extract_subcommands(source: str) -> tuple[SubcommandInfo, ...]:
    """Statically extract ``add_parser("name", help="...")`` subcommands."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()
    found: list[SubcommandInfo] = []
    seen: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "add_parser"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        name = first.value
        if name in seen:
            continue
        help_text: str | None = None
        for kw in node.keywords:
            if kw.arg == "help" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                help_text = kw.value.value
        seen.add(name)
        found.append(SubcommandInfo(name=name, help=help_text))
    return tuple(found)


def _extract_dunder_all(init_path: Path) -> tuple[str, ...]:
    """Return the ``__all__`` list declared in a package ``__init__.py`` (static)."""
    if not init_path.is_file():
        return ()
    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return ()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        names = [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]
                        return tuple(names)
    return ()


def _cli_source_for(package_dir: Path) -> Path:
    """Pick the source file that best describes a package's CLI.

    Prefer ``cli.py`` (where parsers/handlers live), fall back to ``__main__.py``.
    """
    cli_py = package_dir / "cli.py"
    if cli_py.is_file():
        return cli_py
    return package_dir / "__main__.py"


def discover_operations(
    repo_root: Path | str,
    *,
    search_roots: Sequence[str] | None = None,
) -> list[OperationDescriptor]:
    """Discover every ``python -m``-invocable CLI under the search roots.

    A package directory is invocable iff it contains ``__main__.py``. For each,
    the adjacent ``cli.py`` (or ``__main__.py``) is parsed statically for its
    docstring purpose and ``add_parser`` subcommands, and the package
    ``__init__.py`` ``__all__`` is recorded as the public Python API.
    """
    root = Path(repo_root).resolve()
    roots = tuple(search_roots) if search_roots is not None else DEFAULT_OPERATION_SEARCH_ROOTS
    descriptors: list[OperationDescriptor] = []
    for root_name in roots:
        base = root / root_name
        if not base.is_dir():
            continue
        for main_path in sorted(base.rglob("__main__.py")):
            if "__pycache__" in main_path.parts:
                continue
            package_dir = main_path.parent
            dotted = _dotted_path(root, package_dir)
            source_path = _cli_source_for(package_dir)
            source = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
            descriptors.append(
                OperationDescriptor(
                    module=dotted,
                    invocation=f"python -m {dotted}",
                    source_path=source_path.resolve().relative_to(root).as_posix(),
                    purpose=_module_docstring_first_line(source),
                    subcommands=_extract_subcommands(source),
                    exports=_extract_dunder_all(package_dir / "__init__.py"),
                )
            )
    descriptors.sort(key=lambda d: d.module)
    return descriptors


def operation_descriptors_as_json_serializable(
    ops: Sequence[OperationDescriptor],
) -> list[dict[str, Any]]:
    """Convert descriptors to plain JSON-serializable dicts."""
    return [
        {
            "module": op.module,
            "invocation": op.invocation,
            "source_path": op.source_path,
            "purpose": op.purpose,
            "subcommands": [{"name": s.name, "help": s.help} for s in op.subcommands],
            "exports": list(op.exports),
        }
        for op in ops
    ]


def build_operations_payload(ops: Sequence[OperationDescriptor]) -> dict[str, Any]:
    """Build the canonical JSON-serializable operations-manifest structure."""
    return {
        "version": _MANIFEST_VERSION,
        "operations": operation_descriptors_as_json_serializable(ops),
    }


def write_operations_manifest(
    repo_root: Path | str,
    output_path: Path | str | None = None,
    *,
    search_roots: Sequence[str] | None = None,
) -> Path:
    """Write the operations manifest JSON for editors and agents.

    Default output: ``<repo_root>/.cursor/operations_manifest.json``.

    Returns:
        Path to the written file.
    """
    root = Path(repo_root).resolve()
    if output_path is None:
        out = root / ".cursor" / "operations_manifest.json"
    else:
        out = Path(output_path)
        out = out.resolve() if out.is_absolute() else (root / out).resolve()
    ops = discover_operations(root, search_roots=search_roots)
    payload = build_operations_payload(ops)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def load_operations_manifest(manifest_path: Path | str) -> dict[str, Any]:
    """Load an operations manifest JSON file."""
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("operations manifest root must be a JSON object")
    return data


def operations_manifest_matches_discovery(
    repo_root: Path | str,
    manifest_path: Path | str,
    *,
    search_roots: Sequence[str] | None = None,
) -> tuple[bool, str]:
    """Return whether the manifest matches current :func:`discover_operations` output."""
    root = Path(repo_root).resolve()
    mpath = Path(manifest_path).resolve()
    expected = build_operations_payload(discover_operations(root, search_roots=search_roots))
    try:
        on_disk = load_operations_manifest(mpath)
    except FileNotFoundError:
        return False, f"operations manifest missing: {mpath}"
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        return False, f"operations manifest unreadable: {exc}"
    if on_disk.get("version") != expected["version"]:
        return False, "operations manifest version mismatch"
    if on_disk.get("operations") != expected["operations"]:
        return False, (
            "operations manifest out of date — run "
            "`uv run python -m infrastructure.skills operations-write` to regenerate"
        )
    return True, "ok"
