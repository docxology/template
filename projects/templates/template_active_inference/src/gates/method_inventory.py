"""Inventory source and script definitions for documentation coverage."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOTS = ("src", "scripts")
DEFAULT_OUTPUT = Path("docs") / "reference" / "method-inventory.md"


@dataclass(frozen=True)
class MethodEntry:
    """A documented function, method, nested helper, or class definition."""

    path: str
    line: int
    kind: str
    qualname: str
    documentation_source: str
    summary: str


def _first_docstring_line(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Module) -> str | None:
    """Return a compact first docstring line when a definition has one."""
    docstring = ast.get_docstring(node)
    if not docstring:
        return None
    return docstring.strip().splitlines()[0].strip()


def _fallback_summary(path: str, line: int, kind: str, qualname: str) -> str:
    """Build an inventory-backed summary for a definition without a docstring."""
    return f"Inventory fallback for {kind} `{qualname}` defined at `{path}:{line}`."


def _definition_kind(node: ast.AST) -> str:
    """Normalize AST node types into report-friendly definition kinds."""
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async function"
    return "function"


class _DefinitionVisitor(ast.NodeVisitor):
    """Collect definitions while preserving nested qualified names."""

    def __init__(self, rel_path: str) -> None:
        self._rel_path = rel_path
        self._stack: list[str] = []
        self.entries: list[MethodEntry] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._record(node)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._record(node)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._record(node)
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def _record(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = _definition_kind(node)
        qualname = ".".join([*self._stack, node.name])
        docstring = _first_docstring_line(node)
        self.entries.append(
            MethodEntry(
                path=self._rel_path,
                line=node.lineno,
                kind=kind,
                qualname=qualname,
                documentation_source="docstring" if docstring else "inventory fallback",
                summary=docstring or _fallback_summary(self._rel_path, node.lineno, kind, qualname),
            )
        )


def _source_files(project_root: Path) -> list[Path]:
    """Return Python files in the documentation inventory scope."""
    files: list[Path] = []
    for root_name in SOURCE_ROOTS:
        root = project_root / root_name
        files.extend(
            path for path in root.rglob("*.py") if "__pycache__" not in path.parts and path.name != "__init__.py"
        )
    return sorted(files)


def _path_sort_key(path: str) -> tuple[int, str]:
    """Sort inventory paths by declared source-root order, then by path."""
    root = path.split("/", 1)[0]
    try:
        root_order = SOURCE_ROOTS.index(root)
    except ValueError:
        root_order = len(SOURCE_ROOTS)
    return root_order, path


def collect_method_entries(project_root: Path) -> list[MethodEntry]:
    """Collect every class/function definition under source modules and scripts."""
    root = Path(project_root)
    entries: list[MethodEntry] = []
    for path in _source_files(root):
        rel_path = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        visitor = _DefinitionVisitor(rel_path)
        visitor.visit(tree)
        entries.extend(visitor.entries)
    return sorted(entries, key=lambda entry: (*_path_sort_key(entry.path), entry.line, entry.qualname))


def _escape_cell(value: object) -> str:
    """Escape Markdown table cells without changing the underlying value."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def render_method_inventory_markdown(entries: list[MethodEntry]) -> str:
    """Render method inventory entries as a grouped Markdown reference."""
    grouped: dict[str, list[MethodEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.path, []).append(entry)

    lines = [
        "# Method Inventory",
        "",
        "Generated documentation coverage for every Python `def` and `class` under `src/` "
        "and `scripts/`. Entries marked `inventory fallback` have no inline docstring yet, "
        "but remain documented here by path, line, kind, and qualified name.",
        "",
        f"Total documented definitions: {len(entries)}",
        "",
    ]

    for path in sorted(grouped, key=_path_sort_key):
        lines.extend(
            [
                f"## `{path}`",
                "",
                "| line | kind | name | documentation source | summary |",
                "| ---: | --- | --- | --- | --- |",
            ]
        )
        for entry in grouped[path]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_cell(entry.line),
                        f"`{_escape_cell(entry.kind)}`",
                        f"`{_escape_cell(entry.qualname)}`",
                        _escape_cell(entry.documentation_source),
                        _escape_cell(entry.summary),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_method_inventory(
    project_root: Path,
    *,
    output_path: Path | None = None,
) -> Path:
    """Write the method inventory Markdown report and return its path."""
    root = Path(project_root)
    destination = output_path or root / DEFAULT_OUTPUT
    if not destination.is_absolute():
        destination = root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_method_inventory_markdown(collect_method_entries(root)),
        encoding="utf-8",
    )
    return destination
