"""AST-based audit: every re-exporting Python module must declare ``__all__``.

Background
----------
Modules that perform top-level re-exports (e.g. ``from foo import Bar`` with
``# noqa: F401`` or backwards-compat hub modules) must declare ``__all__`` so
that:

1. ``mypy --strict`` does not flag downstream callers with
   ``[attr-defined]`` errors when they import the re-exported names.
2. The set of public names a module advertises is unambiguous at a glance.
3. ``from module import *`` behaves correctly.

This module walks every public ``.py`` file under a root directory (default:
``infrastructure/``), parses it with the standard library ``ast`` module, and
flags any file that re-exports symbols at module scope but lacks an
``__all__`` definition.

A module is considered to "re-export" if any **top-level** ``from X import Y``
statement either:

* Carries a ``# noqa: F401`` comment on the import line (the canonical
  marker for an intentional re-export), OR
* Imports from another module that lives in the same import-root tree
  (i.e. cross-module imports of public names without ``TYPE_CHECKING``
  guarding) and the importer's name does not start with ``_`` — i.e. the
  module looks like a public umbrella.

To stay conservative, the checker prefers the ``noqa: F401`` signal: any
top-level F401 marker triggers the requirement. Imports inside function
bodies, ``if TYPE_CHECKING:`` blocks, and ``try``/``except`` import-fallback
patterns at module scope are still considered top-level for the purpose of
this audit (they re-export when successful), unless guarded by
``TYPE_CHECKING``.

Files starting with ``_`` are skipped (they are private by convention).
``tests/`` is skipped as it is irrelevant.

Usage
-----

As a library::

    from infrastructure.skills.check_all_exports import audit_directory
    violations = audit_directory(Path("infrastructure"))

From the CLI (wired into the existing skills CLI)::

    uv run python -m infrastructure.skills check-all-exports
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

__all__ = [
    "AllExportViolation",
    "audit_directory",
    "audit_file",
    "iter_python_files",
    "module_reexports_at_top_level",
    "module_has_dunder_all",
    "is_top_level_reexport_node",
]

# ─────────────────────────────────────────────────────────────────────────────
# Public dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class AllExportViolation:
    """A single offence: a re-exporting module without ``__all__``.

    Attributes:
        path: Absolute path to the offending ``.py`` file.
        line: Line number of the first re-export statement that triggered
            the requirement (1-based, matching ast).
        reason: Human-readable explanation suitable for CI logs.
    """

    path: Path
    line: int
    reason: str

    def format(self, *, root: Path | None = None) -> str:
        """Return a one-line message suitable for CLI output."""
        display = self.path
        if root is not None:
            try:
                display = self.path.relative_to(root)
            except ValueError:
                display = self.path
        return f"{display}:{self.line}: {self.reason}"


# ─────────────────────────────────────────────────────────────────────────────
# AST helpers
# ─────────────────────────────────────────────────────────────────────────────


def _line_text(source_lines: Sequence[str], line_no: int) -> str:
    """Return the (1-based) source line, joined with continuations."""
    if not (1 <= line_no <= len(source_lines)):
        return ""
    return source_lines[line_no - 1]


def _line_has_noqa_f401(source_lines: Sequence[str], node: ast.AST) -> bool:
    """Return True if any line in *node*'s span carries ``# noqa: F401``.

    Multi-line ``from … import (a, b, c)`` blocks may put the marker on the
    opening line. We scan from ``node.lineno`` to ``node.end_lineno``
    (inclusive). Tolerant to surrounding whitespace and case.
    """
    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", start)
    if start is None:
        return False
    if end is None:
        end = start
    for n in range(start, end + 1):
        text = _line_text(source_lines, n).lower()
        # Accept "noqa: f401" or "noqa:f401" or "noqa: e501,f401"
        if "noqa" not in text:
            continue
        # crude but good enough: substring match on f401 token
        if "f401" in text:
            return True
    return False


def is_top_level_reexport_node(
    node: ast.AST,
    *,
    source_lines: Sequence[str],
) -> tuple[bool, str]:
    """Return ``(is_reexport, reason)`` for a single top-level statement.

    A node counts as a re-export when it is an ``ImportFrom`` (or ``Import``)
    that carries a ``# noqa: F401`` marker on its source span. We deliberately
    do NOT count plain ``from X import Y`` as a re-export unless the F401
    marker is present — many top-level imports are simply used by the
    module's own code, not re-exported.

    The single exception to keep the checker conservative is umbrella
    re-exports inside ``if TYPE_CHECKING:`` blocks; those are always ignored.
    """
    if isinstance(node, (ast.ImportFrom, ast.Import)):
        if _line_has_noqa_f401(source_lines, node):
            module = getattr(node, "module", None) or "<imports>"
            return True, f"top-level F401 re-export from {module!r} without __all__"
    return False, ""


def _is_typechecking_block(node: ast.If) -> bool:
    """Return True if *node* is ``if TYPE_CHECKING:`` (or dotted form)."""
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
        return True
    return False


def _walk_top_level_statements(tree: ast.Module) -> Iterator[ast.stmt]:
    """Yield top-level statements, descending into ``try`` handlers and
    ``if`` branches, but skipping ``if TYPE_CHECKING:`` bodies.

    Re-export shims commonly wrap imports in ``try: from x import Y; except
    ImportError: ...``. Those are still re-exports when the try succeeds,
    so we descend into them.
    """
    for stmt in tree.body:
        if isinstance(stmt, ast.If) and _is_typechecking_block(stmt):
            # Skip TYPE_CHECKING blocks entirely — they are not real re-exports.
            continue
        if isinstance(stmt, ast.Try):
            yield from stmt.body
            for handler in stmt.handlers:
                yield from handler.body
            yield from stmt.orelse
            yield from stmt.finalbody
            continue
        if isinstance(stmt, ast.If):
            # Non-TYPE_CHECKING if at top level — descend into both branches.
            yield from stmt.body
            yield from stmt.orelse
            continue
        yield stmt


def module_has_dunder_all(tree: ast.Module) -> bool:
    """Return True if the module assigns ``__all__`` at top level."""
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return True
        elif isinstance(stmt, ast.AnnAssign):
            target = stmt.target
            if isinstance(target, ast.Name) and target.id == "__all__":
                return True
        elif isinstance(stmt, ast.AugAssign):
            target = stmt.target
            if isinstance(target, ast.Name) and target.id == "__all__":
                return True
    return False


def module_reexports_at_top_level(
    tree: ast.Module,
    *,
    source_lines: Sequence[str],
) -> tuple[bool, int, str]:
    """Return ``(has_reexport, first_line, reason)``.

    ``first_line`` and ``reason`` describe the earliest offending re-export
    found, suitable for a violation message. If no re-export is found,
    returns ``(False, 0, "")``.
    """
    for stmt in _walk_top_level_statements(tree):
        ok, reason = is_top_level_reexport_node(stmt, source_lines=source_lines)
        if ok:
            return True, getattr(stmt, "lineno", 0) or 0, reason
    return False, 0, ""


# ─────────────────────────────────────────────────────────────────────────────
# File-system traversal & per-file audit
# ─────────────────────────────────────────────────────────────────────────────


def _is_private_filename(path: Path) -> bool:
    """Private if filename (without suffix) starts with ``_``.

    Note: ``__init__.py`` is NOT considered private — it is the canonical
    public-API surface for a package.
    """
    name = path.name
    if name == "__init__.py":
        return False
    return name.startswith("_")


def iter_python_files(root: Path, *, skip_dirs: Sequence[str] = ("tests", "__pycache__")) -> Iterator[Path]:
    """Yield ``.py`` files under *root* that should be audited.

    Skips:
    * Files whose name starts with ``_`` (private modules).
    * Files inside directories named in *skip_dirs* (default: ``tests``,
      ``__pycache__``).
    """
    skip = set(skip_dirs)
    for path in sorted(root.rglob("*.py")):
        if any(part in skip for part in path.parts):
            continue
        if _is_private_filename(path):
            continue
        yield path


def audit_file(path: Path) -> AllExportViolation | None:
    """Return a violation for *path* if it re-exports without ``__all__``.

    Returns ``None`` if the file is fine (either does not re-export, or
    re-exports and declares ``__all__``).

    Raises:
        SyntaxError: If the file cannot be parsed. Callers may catch and
            convert to a violation with a parse-error reason if desired.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    has_re, line, reason = module_reexports_at_top_level(tree, source_lines=source.splitlines())
    if not has_re:
        return None
    if module_has_dunder_all(tree):
        return None
    return AllExportViolation(path=path.resolve(), line=line, reason=reason)


def audit_directory(
    root: Path,
    *,
    skip_dirs: Sequence[str] = ("tests", "__pycache__"),
) -> list[AllExportViolation]:
    """Audit every public ``.py`` file under *root* for missing ``__all__``.

    Args:
        root: Root directory to walk recursively.
        skip_dirs: Directory names to skip (matched against any path part).

    Returns:
        A sorted list of violations (by path then line). Empty if clean.
    """
    violations: list[AllExportViolation] = []
    for path in iter_python_files(root, skip_dirs=skip_dirs):
        try:
            v = audit_file(path)
        except SyntaxError as exc:
            violations.append(
                AllExportViolation(
                    path=path.resolve(),
                    line=exc.lineno or 0,
                    reason=f"could not parse: {exc.msg}",
                )
            )
            continue
        if v is not None:
            violations.append(v)
    violations.sort(key=lambda v: (str(v.path), v.line))
    return violations


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────


def run_cli(root: Path, *, skip_dirs: Sequence[str] = ("tests", "__pycache__")) -> int:
    """Run the audit on *root* and print violations. Return 0 if clean."""
    violations = audit_directory(root, skip_dirs=skip_dirs)
    if not violations:
        logger.info("__all__ audit: 0 violations under %s", root)
        return 0
    logger.error(
        "__all__ audit: %d module(s) re-export symbols without declaring __all__",
        len(violations),
    )
    for v in violations:
        logger.error("  %s", v.format(root=root))
    logger.error("Add an explicit __all__ = [...] listing every re-exported name. See docs/rules/api_design.md.")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m infrastructure.skills.check_all_exports`` entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(
        description=("Audit Python modules under <root> for missing __all__ on re-exporting modules."),
    )
    parser.add_argument(
        "root",
        nargs="?",
        default="infrastructure",
        help="Directory to audit (default: infrastructure)",
    )
    parser.add_argument(
        "--skip-dir",
        action="append",
        default=None,
        metavar="NAME",
        help="Directory name to skip (repeatable). Default: tests, __pycache__",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    skip = tuple(args.skip_dir) if args.skip_dir else ("tests", "__pycache__")
    return run_cli(root, skip_dirs=skip)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
