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
dependent. A capability is "invocable via ``python -m X``" when either signal
holds, both statically detectable and dependency-free:

* a **package** whose directory contains ``__main__.py`` (e.g.
  ``infrastructure.validation.cli``); or
* a **single-file module** (``foo.py``) whose source contains a top-level
  ``if __name__ == "__main__":`` guard and whose directory is *not* itself an
  invocable package (so it is not redundant with a package entry point). This is
  what makes documented single-file CLIs — ``infrastructure.core.health``,
  ``infrastructure.project.public_scope``,
  ``infrastructure.documentation.generate_glossary_cli`` and
  ``infrastructure.reporting.release_readiness`` — reachable.

Each descriptor also carries an :attr:`OperationDescriptor.effect` tier
(``read_only`` by default, ``mutating`` for the small allowlist of publish /
upload / paid CLIs in :data:`MUTATING_OPERATIONS`) so an agent surface can refuse
side-effecting operations unless explicitly opted in.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Sequence

__all__ = [
    "MUTATING_OPERATIONS",
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

# Package roots scanned for invocable operations (relative to repo root).
DEFAULT_OPERATION_SEARCH_ROOTS: tuple[str, ...] = ("infrastructure",)

# Effect tier for the capability surface.
Effect = Literal["read_only", "mutating"]

# Explicit allowlist of dotted module paths whose CLIs write state, mutate
# external systems, or incur cost. Everything else is
# treated as ``read_only``. Kept deliberately small and hand-maintained — an
# agent surface may refuse these unless a caller explicitly opts in.
MUTATING_OPERATIONS: frozenset[str] = frozenset(
    {
        "infrastructure.core.health_benchmark",  # writes the requested evidence manifest
        "infrastructure.publishing",  # DOI / Zenodo / arXiv publish + archival CLIs
        "infrastructure.search.deep_research",  # PAID deep-research dispatch
        "infrastructure.skills",  # manifests plus user-level runtime links + backups
    }
)


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
    """``__all__`` of the owning package (or single-file module) — its public API."""
    effect: Effect = "read_only"
    """Capability tier: ``read_only`` (default) or ``mutating`` (see :data:`MUTATING_OPERATIONS`)."""


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


def _dunder_all_from_source(source: str) -> tuple[str, ...]:
    """Return the ``__all__`` list declared in module source (static)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
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


def _extract_dunder_all(init_path: Path) -> tuple[str, ...]:
    """Return the ``__all__`` list declared in a package ``__init__.py`` (static)."""
    if not init_path.is_file():
        return ()
    try:
        return _dunder_all_from_source(init_path.read_text(encoding="utf-8"))
    except OSError:
        return ()


def _has_main_guard(source: str) -> bool:
    """Return whether module source contains a top-level ``__name__ == "__main__"`` guard."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            continue
        left = node.test.left
        comparators = node.test.comparators
        if isinstance(left, ast.Name) and left.id == "__name__":
            if any(isinstance(c, ast.Constant) and c.value == "__main__" for c in comparators):
                return True
        if isinstance(left, ast.Constant) and left.value == "__main__":
            if any(isinstance(c, ast.Name) and c.id == "__name__" for c in comparators):
                return True
    return False


def _module_dotted_path(repo_root: Path, module_file: Path) -> str:
    """Return the dotted import path for a single-file ``.py`` module under repo root."""
    rel = module_file.resolve().relative_to(repo_root.resolve())
    return ".".join(rel.with_suffix("").parts)


def _cli_source_for(package_dir: Path) -> Path:
    """Pick the source file that best describes a package's CLI.

    Prefer a dedicated ``parser.py`` after orchestration has been split into
    parser/handler/interaction modules, then ``cli.py``, then ``__main__.py``.
    This keeps the generated operation manifest derived from the declarative
    command registry instead of losing subcommands when ``cli.py`` becomes a
    compatibility facade.
    """
    parser_py = package_dir / "parser.py"
    if parser_py.is_file():
        return parser_py
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

    Two invocation signals are recognised, both purely static:

    * a **package** directory containing ``__main__.py`` — its adjacent
      ``cli.py`` (or ``__main__.py``) is parsed for docstring purpose and
      ``add_parser`` subcommands, and the package ``__init__.py`` ``__all__`` is
      recorded as the public API; and
    * a **single-file module** (``foo.py``) with a top-level
      ``if __name__ == "__main__":`` guard whose directory is *not* itself an
      invocable package — parsed the same way, with the module's own ``__all__``.

    Each descriptor is tagged with an :attr:`OperationDescriptor.effect` tier from
    :data:`MUTATING_OPERATIONS`.
    """
    root = Path(repo_root).resolve()
    roots = tuple(search_roots) if search_roots is not None else DEFAULT_OPERATION_SEARCH_ROOTS
    descriptors: list[OperationDescriptor] = []
    package_dirs: set[Path] = set()
    for root_name in roots:
        base = root / root_name
        if not base.is_dir():
            continue
        # Pass 1: packages with __main__.py.
        for main_path in sorted(base.rglob("__main__.py")):
            if "__pycache__" in main_path.parts:
                continue
            package_dir = main_path.parent
            package_dirs.add(package_dir)
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
                    effect="mutating" if dotted in MUTATING_OPERATIONS else "read_only",
                )
            )
    for root_name in roots:
        base = root / root_name
        if not base.is_dir():
            continue
        # Pass 2: single-file modules with a __main__ guard, not shadowed by a
        # package entry point in the same directory.
        for py_path in sorted(base.rglob("*.py")):
            if "__pycache__" in py_path.parts:
                continue
            if py_path.name in {"__init__.py", "__main__.py"}:
                continue
            if py_path.parent in package_dirs:
                continue
            try:
                source = py_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if not _has_main_guard(source):
                continue
            dotted = _module_dotted_path(root, py_path)
            descriptors.append(
                OperationDescriptor(
                    module=dotted,
                    invocation=f"python -m {dotted}",
                    source_path=py_path.resolve().relative_to(root).as_posix(),
                    purpose=_module_docstring_first_line(source),
                    subcommands=_extract_subcommands(source),
                    exports=_dunder_all_from_source(source),
                    effect="mutating" if dotted in MUTATING_OPERATIONS else "read_only",
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
            "effect": op.effect,
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
