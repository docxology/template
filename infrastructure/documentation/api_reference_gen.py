"""Auto-generation of the public API reference markdown.

The hand-maintained ``docs/reference/api-reference.md`` drifts from the
real exports of each ``infrastructure/<pkg>/__init__.py``. This module
provides the **single source of truth** API reference: it parses each
package's ``__all__``, resolves each symbol to its source-module
definition, and emits a deterministic Markdown block.

Public entry points:

* :func:`walk_public_api` — for one package, return a list of
  :class:`ModuleAPI` records (one per ``__all__`` entry).
* :func:`build_api_reference_markdown` — render per-package sections
  for many packages.
* :func:`inject_api_reference` — round-trip the generated content
  between ``<!-- BEGIN:API_REFERENCE -->`` /
  ``<!-- END:API_REFERENCE -->`` markers in a Markdown file, reusing
  :func:`infrastructure.documentation.glossary_gen.inject_between_markers`.

Resolution strategy
-------------------

For each package root ``<pkg>/``:

1. Parse ``<pkg>/__init__.py`` with :mod:`ast`. Extract the literal
   ``__all__`` list and every ``ImportFrom`` statement of the form
   ``from <module> import A, B, C``. Build a ``symbol -> module`` map
   keyed by ``ast.alias.asname or ast.alias.name``.
2. For each name in ``__all__``:

   * Locate the source ``.py`` file by walking the dotted module path.
   * Parse that file with :mod:`ast` and find the matching ``FunctionDef``,
     ``AsyncFunctionDef``, or ``ClassDef``. Extract the signature using
     :func:`ast.unparse` on the arguments + return annotation, plus the
     first non-empty docstring line.

The generator never executes user code — pure AST parsing keeps the
``--check`` step fast and side-effect-free, satisfying the
"thin-orchestrator" constitution. Symbols whose definition cannot be
located are recorded with an empty signature; this is intentional so that
drift is visible in the rendered Markdown rather than swallowed.

Determinism
-----------

* Packages are processed in the order supplied by the caller. The CLI
  passes them sorted alphabetically.
* Symbols within a package are sorted alphabetically (case-insensitive).
* Empty packages (``__all__ == []``) are omitted from the output.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.documentation.glossary_gen import inject_between_markers

logger = get_logger(__name__)


@dataclass(frozen=True)
class ModuleAPI:
    """One public symbol exported from a package's ``__all__``.

    Attributes:
        package: Package import path (e.g. ``infrastructure.llm``).
        module: Source module where the symbol is **defined**
            (e.g. ``infrastructure.llm.core.client``). Best-effort —
            falls back to ``package`` if resolution fails.
        name: The symbol name as it appears in ``__all__``.
        kind: ``"function"``, ``"class"``, or ``"unknown"``.
        signature: The Python signature string (without the ``def`` /
            ``class`` keyword), e.g. ``foo(x: int) -> str`` or
            ``MyClass(*, name: str)``. Empty string if it could not be
            resolved.
        summary: First non-empty docstring line, or ``""``.
    """

    package: str
    module: str
    name: str
    kind: str
    signature: str
    summary: str


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _parse_init(init_path: Path) -> tuple[list[str], dict[str, str]]:
    """Return ``(__all__ list, symbol_name -> dotted_module)`` from an init file.

    Raises ``ValueError`` if the file cannot be parsed or has no
    literal ``__all__`` assignment.
    """
    source = init_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(init_path))

    all_list: list[str] | None = None
    symbol_to_module: dict[str, str] = {}

    for node in tree.body:
        # __all__ = [...]
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    all_list = _extract_string_list(node.value)
        # from X.Y.Z import A, B as C
        elif isinstance(node, ast.ImportFrom) and node.module:
            # Resolve relative imports against the package itself.
            if node.level:
                pkg = init_path.parent.name
                root_pkg = init_path.parent.parent.name
                # level==1 means "from .submodule import X" → infrastructure.<pkg>.submodule
                # level==2 (rare) → infrastructure.<root>.submodule (skip — uncommon here)
                if node.level == 1:
                    module_full = f"{root_pkg}.{pkg}.{node.module}"
                else:
                    # Fallback: use as-given (best-effort)
                    module_full = node.module
            else:
                module_full = node.module
            for alias in node.names:
                exposed = alias.asname or alias.name
                symbol_to_module[exposed] = module_full

    if all_list is None:
        raise ValueError(f"No literal __all__ list found in {init_path}")
    return all_list, symbol_to_module


def _extract_string_list(node: ast.expr) -> list[str]:
    """Return the list of string literals in ``[...]`` / ``(...)`` ; ignore non-strings."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    out: list[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            out.append(elt.value)
    return out


def _module_to_path(module: str, package_root: Path) -> Path | None:
    """Resolve a dotted module to a ``.py`` file relative to the repo root.

    ``infrastructure.llm.core.client`` → ``<repo_root>/infrastructure/llm/core/client.py``.
    Falls back to ``__init__.py`` if a directory is found instead. Uses
    ``package_root.parent.parent`` as the repo root anchor (since
    ``package_root`` always points at ``<repo_root>/infrastructure/<pkg>``).
    """
    repo_root = package_root.parent.parent
    return _module_dotted_to_path(module, repo_root)


def _find_definition(module_path: Path, name: str, repo_root: Path, *, _depth: int = 0) -> tuple[str, str, str, str]:
    """Return ``(kind, signature, summary, defining_module)`` for ``name``.

    ``kind`` is one of ``"function"``, ``"class"``, ``"unknown"``.
    ``defining_module`` is the dotted module path where the symbol is
    actually defined (may differ from ``module_path`` if the symbol is
    re-exported through one or more intermediate modules).

    Follows re-export chains up to 5 hops to handle cases like
    ``utils.py`` re-exporting from ``setup.py``. Pure AST — never imports.
    """
    if _depth > 5:
        return ("unknown", "", "", _path_to_dotted(module_path, repo_root))
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    except (SyntaxError, OSError, UnicodeDecodeError) as e:
        logger.debug(f"Skipping {module_path} (parse error): {e}")
        return ("unknown", "", "", _path_to_dotted(module_path, repo_root))

    # 1) Top-level definition match. Also flatten ``try`` blocks one level
    # deep so optional-import constants (``try: ...; X = True; except: X = False``)
    # are discoverable.
    flat_body: list[ast.stmt] = []
    for node in tree.body:
        flat_body.append(node)
        if isinstance(node, ast.Try):
            flat_body.extend(node.body)
            for handler in node.handlers:
                flat_body.extend(handler.body)
            flat_body.extend(node.orelse)
            flat_body.extend(node.finalbody)
    for node in flat_body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return (
                "function",
                _format_function_signature(node),
                _first_doc_line(node),
                _path_to_dotted(module_path, repo_root),
            )
        if isinstance(node, ast.ClassDef) and node.name == name:
            return (
                "class",
                _format_class_signature(node),
                _first_doc_line(node),
                _path_to_dotted(module_path, repo_root),
            )
        # Module-level constants: ``NAME = ...`` or ``NAME: type = ...``.
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return (
                        "constant",
                        f"{name} = {_safe_unparse(node.value)}",
                        "",
                        _path_to_dotted(module_path, repo_root),
                    )
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            value_repr = f" = {_safe_unparse(node.value)}" if node.value is not None else ""
            return (
                "constant",
                f"{name}: {_safe_unparse(node.annotation)}{value_repr}",
                "",
                _path_to_dotted(module_path, repo_root),
            )

    # 2) Re-export chain: follow ``from <other> import <name>`` one level deeper.
    for node in flat_body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        for alias in node.names:
            exposed = alias.asname or alias.name
            if exposed != name:
                continue
            # Resolve the target module of the re-export.
            if node.level:
                # Relative import resolution mirrors CPython:
                #  - in a package's __init__.py, the package itself is the
                #    anchor; level=1 strips zero parts.
                #  - in a regular module, level=1 strips the module name.
                this_dotted = _path_to_dotted(module_path, repo_root)
                strip = node.level - 1 if module_path.name == "__init__.py" else node.level
                if strip <= 0:
                    base_pkg = this_dotted
                else:
                    base_pkg = this_dotted.rsplit(".", strip)[0] if "." in this_dotted else ""
                target_module = f"{base_pkg}.{node.module}" if base_pkg else node.module
            else:
                target_module = node.module
            target_path = _module_dotted_to_path(target_module, repo_root)
            if target_path is None:
                continue
            real_name = alias.name  # Original name in the source module.
            return _find_definition(target_path, real_name, repo_root, _depth=_depth + 1)

    return ("unknown", "", "", _path_to_dotted(module_path, repo_root))


def _path_to_dotted(module_path: Path, repo_root: Path) -> str:
    """Convert ``<repo_root>/foo/bar/baz.py`` → ``foo.bar.baz``."""
    try:
        rel = module_path.relative_to(repo_root)
    except ValueError:
        return module_path.stem
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _module_dotted_to_path(module: str, repo_root: Path) -> Path | None:
    """Resolve a dotted module name relative to ``repo_root`` to a ``.py`` file."""
    parts = module.split(".")
    candidate = repo_root.joinpath(*parts)
    py = candidate.with_suffix(".py")
    if py.is_file():
        return py
    if candidate.is_dir():
        init = candidate / "__init__.py"
        if init.is_file():
            return init
    return None


def _format_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render a function signature: ``name(args) -> Return``."""
    args_str = ast.unparse(node.args)
    sig = f"{node.name}({args_str})"
    if node.returns is not None:
        sig += f" -> {ast.unparse(node.returns)}"
    return sig


def _format_class_signature(node: ast.ClassDef) -> str:
    """Render a class signature.

    Prefers the ``__init__`` arguments if present; otherwise falls back
    to base classes ``MyClass(Base1, Base2)``. Dataclasses with no
    explicit ``__init__`` get just ``MyClass``.
    """
    for body_item in node.body:
        if isinstance(body_item, (ast.FunctionDef, ast.AsyncFunctionDef)) and body_item.name == "__init__":
            args_str = ast.unparse(body_item.args)
            # Drop leading ``self`` for readability.
            args_str = args_str.removeprefix("self, ").removeprefix("self")
            return f"{node.name}({args_str})"
    if node.bases:
        bases = ", ".join(ast.unparse(b) for b in node.bases)
        return f"{node.name}({bases})"
    return node.name


def _safe_unparse(node: ast.AST | None, max_len: int = 80) -> str:
    """Unparse an expression, truncating long literals for readability."""
    if node is None:
        return ""
    try:
        out = ast.unparse(node)
    except Exception:  # pragma: no cover — ast.unparse is robust
        return "..."
    if len(out) > max_len:
        return out[: max_len - 3] + "..."
    return out


def _first_doc_line(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> str:
    """First non-empty line of the docstring, stripped."""
    doc = ast.get_docstring(node) or ""
    for raw in doc.splitlines():
        line = raw.strip()
        if line:
            return line
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def discover_infrastructure_packages(infra_dir: Path) -> list[Path]:
    """Return alphabetically-sorted package roots under ``infra_dir``.

    Scans ``infra_dir`` for immediate subdirectories that contain an
    ``__init__.py`` and whose name does **not** start with an underscore,
    returning them sorted by name. This is the canonical package-discovery
    entry point used by ``scripts/docgen/api_reference.py``.

    Args:
        infra_dir: The ``infrastructure/`` directory to scan.

    Returns:
        Package root directories (each containing an ``__init__.py``),
        sorted alphabetically by directory name.
    """
    return sorted(
        (p.parent for p in infra_dir.glob("*/__init__.py") if not p.parent.name.startswith("_")),
        key=lambda p: p.name,
    )


def walk_public_api(package_root: Path) -> list[ModuleAPI]:
    """Walk one package's ``__init__.py`` and return :class:`ModuleAPI` records.

    Args:
        package_root: A directory whose ``__init__.py`` declares ``__all__``,
            e.g. ``infrastructure/llm``.

    Returns:
        A list of :class:`ModuleAPI` records, one per name in ``__all__``,
        sorted alphabetically (case-insensitive). Returns ``[]`` if the
        package has an empty ``__all__``.

    Raises:
        FileNotFoundError: If ``package_root/__init__.py`` does not exist.
        ValueError: If the package's ``__init__.py`` lacks a literal
            ``__all__`` list.
    """
    init_path = package_root / "__init__.py"
    if not init_path.is_file():
        raise FileNotFoundError(f"Package __init__.py not found: {init_path}")

    all_list, sym_to_module = _parse_init(init_path)
    package_dotted = (
        f"{package_root.parent.name}.{package_root.name}" if package_root.parent.name else package_root.name
    )
    records: list[ModuleAPI] = []
    for name in all_list:
        if name.startswith("_"):
            continue
        module_dotted = sym_to_module.get(name, package_dotted)
        module_path = _module_to_path(module_dotted, package_root)
        if module_path is None:
            records.append(
                ModuleAPI(
                    package=package_dotted,
                    module=module_dotted,
                    name=name,
                    kind="unknown",
                    signature="",
                    summary="",
                )
            )
            continue
        repo_root = package_root.parent.parent
        kind, signature, summary, defining_module = _find_definition(module_path, name, repo_root)
        records.append(
            ModuleAPI(
                package=package_dotted,
                module=defining_module or module_dotted,
                name=name,
                kind=kind,
                signature=signature,
                summary=summary,
            )
        )

    records.sort(key=lambda r: r.name.lower())
    return records


def build_api_reference_markdown(packages: list[Path]) -> str:
    """Render a deterministic Markdown block covering ``packages``.

    Output structure::

        <!-- generated caption -->

        ## Package: `<pkg>`

        ### `name`

        ```python
        signature
        ```

        First docstring line as prose.

    Args:
        packages: Package roots to document. Order is preserved as-given;
            callers should sort alphabetically for determinism.

    Returns:
        Markdown block (no surrounding marker comments). Always ends with
        a single trailing newline.
    """
    caption = (
        "<!-- This block is generated by "
        "`scripts/docgen/api_reference.py` from each package's "
        "`__init__.py` `__all__`. Do not hand-edit. "
        "Hand-written prose belongs **above** the markers. -->"
    )
    lines: list[str] = [caption, ""]

    documented_packages = 0
    for pkg_root in packages:
        records = walk_public_api(pkg_root)
        if not records:
            logger.debug(f"Skipping {pkg_root} (empty __all__)")
            continue
        documented_packages += 1
        package_dotted = f"{pkg_root.parent.name}.{pkg_root.name}" if pkg_root.parent.name else pkg_root.name
        lines.append(f"## Package: `{package_dotted}`")
        lines.append("")
        for rec in records:
            lines.append(f"### `{rec.name}`")
            lines.append("")
            kind_label = {
                "function": "function",
                "class": "class",
                "constant": "constant",
            }.get(rec.kind, "symbol")
            lines.append(f"*{kind_label} — defined in `{rec.module}`*")
            lines.append("")
            if rec.signature:
                prefix = "class " if rec.kind == "class" else "" if rec.kind == "constant" else ""
                lines.append("```python")
                lines.append(f"{prefix}{rec.signature}")
                lines.append("```")
                lines.append("")
            if rec.summary:
                lines.append(rec.summary)
                lines.append("")
        # Trailing blank already present from the per-symbol block.

    if documented_packages == 0:
        lines.append("_No packages with non-empty `__all__` found._")
        lines.append("")

    # Collapse trailing blank lines to exactly one terminating newline.
    while len(lines) > 1 and lines[-1] == "" and lines[-2] == "":
        lines.pop()
    return "\n".join(lines) + ("\n" if not lines or lines[-1] != "" else "")


def inject_api_reference(
    markdown_path: Path,
    content: str,
    marker: str = "API_REFERENCE",
) -> bool:
    """Inject ``content`` between ``<!-- BEGIN:{marker} -->`` markers.

    Idempotent: returns ``False`` if the file is already up-to-date.
    Reuses :func:`infrastructure.documentation.glossary_gen.inject_between_markers`
    so the marker semantics stay consistent across the doc-hygiene tooling.

    Args:
        markdown_path: Markdown file to mutate.
        content: Generated Markdown block (no marker comments).
        marker: Marker label. Defaults to ``"API_REFERENCE"``.

    Returns:
        ``True`` if the file was written, ``False`` otherwise.

    Raises:
        FileNotFoundError: If ``markdown_path`` does not exist.
    """
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown target not found: {markdown_path}")

    begin = f"<!-- BEGIN:{marker} -->"
    end = f"<!-- END:{marker} -->"

    text = markdown_path.read_text(encoding="utf-8")
    new_text = inject_between_markers(text, begin, end, content)
    if new_text == text:
        logger.debug(f"API reference up-to-date: {markdown_path}")
        return False

    tmp = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
    try:
        tmp.write_text(new_text, encoding="utf-8")
        tmp.replace(markdown_path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise
    logger.info(f"Updated API reference in {markdown_path}")
    return True


__all__ = [
    "ModuleAPI",
    "discover_infrastructure_packages",
    "walk_public_api",
    "build_api_reference_markdown",
    "inject_api_reference",
]
