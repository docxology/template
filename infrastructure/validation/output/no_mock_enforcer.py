"""Lexical mock-framework gate and semantic stand-in inventory.

Detects prohibited mock-framework syntax in tests and inventories separate
``pytest.monkeypatch`` operations for policy review.

Detection is two-pass and deliberately hard to bypass:

1. **Imports** are found with :mod:`ast`, so ``from unittest import mock``,
   ``import unittest.mock``, ``from unittest.mock import …``, ``import mock``,
   and ``import pytest_mock`` are all caught regardless of surrounding text.
2. **Call / decorator usage** is matched against comment-stripped source with
   word-boundary patterns, so a trailing ``# comment`` or a ``mock_``-prefixed
   variable name can no longer hide a real ``MagicMock()`` (the historical
   bypass: the old skip list treated a bare ``#`` or the substring ``mock_``
   appearing *anywhere* on the line as a reason to skip it entirely).

The lexical gate deliberately does **not** claim that a clean result proves all
tests exercise real dependencies. ``pytest.monkeypatch`` is a distinct token
from ``patch`` and is therefore outside that gate. The semantic inventory in
this module records monkeypatch operations separately: environment isolation
(``setenv``/``delenv``/``chdir``), import-path isolation, dependency
replacement (``setattr``/``setitem`` and deletion variants), and other scope
management. Dependency replacement remains migration debt even though it does
not make the lexical gate fail.

A line may opt out of the usage-pattern pass explicitly with a
``# no-mocks-ok:`` trailing comment when a forbidden token legitimately appears
in non-test scaffolding.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.public_scope import public_project_infos

logger = get_logger(__name__)

# Explicit opt-out token (kept narrow — not a bare ``#``).
_SUPPRESSION_TOKEN = "# no-mocks-ok:"  # nosec B105

# Modules whose import is, by itself, a no-mocks violation.
_FORBIDDEN_IMPORT_ROOTS = frozenset({"mock", "pytest_mock"})
_FORBIDDEN_UNITTEST_SUBMODULE = "mock"  # unittest.mock
_FORBIDDEN_DYNAMIC_MODULES = frozenset({"mock", "pytest_mock", "unittest.mock"})
_FORBIDDEN_DYNAMIC_ATTRIBUTES = frozenset({"Mock", "MagicMock", "create_autospec", "patch"})

# Call / decorator usage patterns, matched against comment-stripped lines.
# Word boundaries keep ``monkeypatch`` (allowed) distinct from ``patch``.
_USAGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bMagicMock\s*\("),
    re.compile(r"\bMock\s*\("),
    re.compile(r"\bcreate_autospec\s*\("),
    re.compile(r"@\s*patch\b"),
    re.compile(r"@\s*mock\.patch\b"),
    re.compile(r"\bpatch\s*\("),
    re.compile(r"\bpatch\.object\s*\("),
    re.compile(r"\bmocker\.patch\b"),
    re.compile(r"\bmock\.patch\b"),
    re.compile(r"\bmock\.MagicMock\b"),
)

# Token types whose content is not code (comments, string bodies, layout).
# f-string component tokens only exist on Python 3.12+; resolve defensively so
# the module imports on 3.10/3.11 too.
_NON_CODE_TOKENS: frozenset[int] = frozenset(
    t
    for t in (
        getattr(tokenize, name, None)
        for name in (
            "COMMENT",
            "STRING",
            "FSTRING_START",
            "FSTRING_MIDDLE",
            "FSTRING_END",
            "NL",
            "NEWLINE",
            "INDENT",
            "DEDENT",
            "ENDMARKER",
            "ENCODING",
        )
    )
    if t is not None
)

_ENVIRONMENT_ISOLATION_METHODS = frozenset({"setenv", "delenv", "chdir"})
_IMPORT_PATH_ISOLATION_METHODS = frozenset({"syspath_prepend"})
_DEPENDENCY_REPLACEMENT_METHODS = frozenset({"setattr", "delattr", "setitem", "delitem"})


class StandInCategory(str, Enum):
    """Syntactic monkeypatch-use categories used by the advisory inventory."""

    environment_isolation = "environment_isolation"
    import_path_isolation = "import_path_isolation"
    dependency_replacement = "dependency_replacement"
    other = "other"


@dataclass(frozen=True)
class LexicalMockScanResult:
    """Deterministic result from scanning one tests tree for banned frameworks."""

    files_scanned: int
    violations: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class SemanticStandInUse:
    """One syntactically identified monkeypatch operation."""

    path: str
    line: int
    column: int
    method: str
    category: StandInCategory
    source: str

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-safe representation."""
        return {
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "method": self.method,
            "category": self.category.value,
            "source": self.source,
        }


@dataclass(frozen=True)
class SemanticStandInScanResult:
    """Deterministic result from inventorying one tests tree."""

    files_scanned: int
    uses: tuple[SemanticStandInUse, ...]
    errors: tuple[str, ...]


def _import_violations(tree: ast.AST) -> set[int]:
    """Return line numbers of static and dynamic mock-framework imports."""
    flagged: set[int] = set()
    importlib_aliases = {"importlib"}
    import_module_aliases: set[str] = set()
    forbidden_module_variables: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_IMPORT_ROOTS or alias.name == "unittest.mock":
                    flagged.add(node.lineno)
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # from unittest import mock  /  from unittest.mock import X
            if module == "unittest" and any(a.name == _FORBIDDEN_UNITTEST_SUBMODULE for a in node.names):
                flagged.add(node.lineno)
            elif module == "unittest.mock" or module.split(".")[0] in _FORBIDDEN_IMPORT_ROOTS:
                flagged.add(node.lineno)
            if module == "importlib":
                import_module_aliases.update(
                    alias.asname or alias.name for alias in node.names if alias.name == "import_module"
                )

    def dynamic_module(call: ast.Call) -> str | None:
        function = call.func
        is_import = isinstance(function, ast.Name) and function.id in {
            "__import__",
            *import_module_aliases,
        }
        if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            is_import = function.value.id in importlib_aliases and function.attr == "import_module"
        if not is_import or not call.args:
            return None
        module_arg = call.args[0]
        if isinstance(module_arg, ast.Constant) and isinstance(module_arg.value, str):
            return module_arg.value
        return None

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if isinstance(value, ast.Call) and dynamic_module(value) in _FORBIDDEN_DYNAMIC_MODULES:
                flagged.add(value.lineno)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                forbidden_module_variables.update(target.id for target in targets if isinstance(target, ast.Name))
        if not isinstance(node, ast.Call):
            continue
        module_name = dynamic_module(node)
        if module_name in _FORBIDDEN_DYNAMIC_MODULES:
            flagged.add(node.lineno)
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id in forbidden_module_variables
            and function.attr in _FORBIDDEN_DYNAMIC_ATTRIBUTES
        ):
            flagged.add(node.lineno)
        if (
            isinstance(function, ast.Name)
            and function.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in forbidden_module_variables
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value in _FORBIDDEN_DYNAMIC_ATTRIBUTES
        ):
            flagged.add(node.lineno)
    return flagged


def _code_only_lines(source: str) -> dict[int, str] | None:
    """Map line number → that line's code, with comments and strings removed.

    Tokenizing the whole file (not line-by-line) is what makes multi-line
    docstrings safe: the entire triple-quoted block is one STRING token and is
    dropped, so a forbidden name documented across several lines of a docstring
    never reaches the usage patterns. Comments are dropped for the same reason.
    Returns ``None`` if the file cannot be tokenized (caller falls back to the
    AST import pass, which is the load-bearing check).
    """
    code_by_line: dict[int, list[str]] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type in _NON_CODE_TOKENS:
                continue
            code_by_line.setdefault(tok.start[0], []).append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return {ln: " ".join(parts) for ln, parts in code_by_line.items()}


def scan_test_roots(repo_root: Path) -> list[Path]:
    """Return every tests/ dir the No Mocks Policy must cover.

    Always includes the repository-level ``tests/`` tree and, in addition,
    each public exemplar project's ``tests/`` directory (resolved via
    :func:`public_project_infos` so the enforcement surface stays in lockstep
    with the public CI scope). Project ``tests/`` dirs that do not exist in the
    current checkout are skipped silently; the repo-level ``tests/`` dir is
    required and its absence is treated as a failure by the caller.
    """
    roots = [repo_root / "tests"]
    if not (repo_root / "projects").is_dir():
        return roots
    for project in public_project_infos(repo_root):
        project_tests = (repo_root / project.path / "tests").resolve()
        if project_tests.exists():
            roots.append(project_tests)
    return roots


def _relative_path(path: Path, repo_root: Path) -> str:
    """Render *path* relative to the repository when possible."""
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_test_python_files(tests_dir: Path) -> tuple[Path, ...]:
    """Return in-scope Python test files in deterministic path order."""
    if not tests_dir.exists():
        return ()
    files = []
    for py_file in tests_dir.rglob("*.py"):
        relative_parts = py_file.relative_to(tests_dir).parts
        if "fixtures" not in relative_parts or py_file.name.startswith("test_"):
            files.append(py_file)
    return tuple(sorted(files, key=lambda path: path.as_posix()))


def scan_lexical_mock_policy(
    tests_dir: Path,
    repo_root: Path,
) -> LexicalMockScanResult:
    """Scan a tests tree for prohibited mock-framework imports and calls.

    This is the exact policy enforced by CI. A clean result proves only that
    the configured lexical imports/calls are absent. Scan/read/parse errors are
    returned separately so the CLI can fail closed rather than report a false
    pass.
    """
    violations: list[str] = []
    errors: list[str] = []
    py_files = _iter_test_python_files(tests_dir)

    for py_file in py_files:
        relative_path = _relative_path(py_file, repo_root)
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{relative_path}: read error: {exc}")
            continue

        flagged_lines: dict[int, str] = {}
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError as exc:
            tree = None
            errors.append(f"{relative_path}:{exc.lineno or 0}: syntax error: {exc.msg}")
        if tree is not None:
            lines = source.splitlines()
            for lineno in _import_violations(tree):
                if 1 <= lineno <= len(lines):
                    flagged_lines[lineno] = lines[lineno - 1].strip()

        raw_lines = source.splitlines()
        code_lines = _code_only_lines(source)
        if code_lines is None:
            errors.append(f"{relative_path}: tokenization failed")
            code_lines = {line_number: line.split("#", 1)[0] for line_number, line in enumerate(raw_lines, 1)}
        for line_num, code in code_lines.items():
            if line_num in flagged_lines:
                continue
            raw_line = raw_lines[line_num - 1] if 1 <= line_num <= len(raw_lines) else ""
            if _SUPPRESSION_TOKEN in raw_line or not code.strip():
                continue
            if any(pattern.search(code) for pattern in _USAGE_PATTERNS):
                flagged_lines[line_num] = raw_line.strip()

        violations.extend(
            f"{relative_path}:{line_num}: {flagged_lines[line_num]}" for line_num in sorted(flagged_lines)
        )

    return LexicalMockScanResult(
        files_scanned=len(py_files),
        violations=tuple(sorted(violations)),
        errors=tuple(sorted(errors)),
    )


def _annotation_mentions_monkeypatch(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    try:
        return ast.unparse(annotation).split(".")[-1] == "MonkeyPatch"
    except (AttributeError, ValueError):
        return False


def _is_monkeypatch_constructor(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    function = node.func
    if isinstance(function, ast.Name):
        return function.id == "MonkeyPatch"
    return isinstance(function, ast.Attribute) and function.attr == "MonkeyPatch"


def _assigned_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in node.elts:
            names.update(_assigned_names(element))
        return names
    return set()


def _monkeypatch_aliases(tree: ast.AST) -> set[str]:
    """Return likely MonkeyPatch receiver names, including context aliases."""
    names = {"monkeypatch"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            for argument in args:
                if _annotation_mentions_monkeypatch(argument.annotation):
                    names.add(argument.arg)
        elif isinstance(node, ast.Assign) and _is_monkeypatch_constructor(node.value):
            for target in node.targets:
                names.update(_assigned_names(target))
        elif isinstance(node, ast.AnnAssign) and node.value is not None and _is_monkeypatch_constructor(node.value):
            names.update(_assigned_names(node.target))

    # ``with monkeypatch.context() as scoped:`` introduces another receiver.
    # Iterate because nested contexts may alias an alias.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.With, ast.AsyncWith)):
                continue
            for item in node.items:
                expression = item.context_expr
                if not isinstance(expression, ast.Call):
                    continue
                function = expression.func
                if (
                    isinstance(function, ast.Attribute)
                    and function.attr == "context"
                    and isinstance(function.value, ast.Name)
                    and function.value.id in names
                    and item.optional_vars is not None
                ):
                    before = len(names)
                    names.update(_assigned_names(item.optional_vars))
                    changed = changed or len(names) != before
    return names


def _stand_in_category(method: str) -> StandInCategory:
    if method in _ENVIRONMENT_ISOLATION_METHODS:
        return StandInCategory.environment_isolation
    if method in _IMPORT_PATH_ISOLATION_METHODS:
        return StandInCategory.import_path_isolation
    if method in _DEPENDENCY_REPLACEMENT_METHODS:
        return StandInCategory.dependency_replacement
    return StandInCategory.other


def scan_semantic_standins(
    tests_dir: Path,
    repo_root: Path,
) -> SemanticStandInScanResult:
    """Inventory monkeypatch operations without treating current debt as a gate.

    Classification is intentionally syntactic. In particular, every
    ``setattr``/``setitem`` call is recorded as dependency replacement even
    when a human review may later decide it only redirects a path. This gives
    migration work a conservative, reproducible starting inventory.
    """
    uses: list[SemanticStandInUse] = []
    errors: list[str] = []
    py_files = _iter_test_python_files(tests_dir)

    for py_file in py_files:
        relative_path = _relative_path(py_file, repo_root)
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{relative_path}: read error: {exc}")
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError as exc:
            errors.append(f"{relative_path}:{exc.lineno or 0}: syntax error: {exc.msg}")
            continue

        aliases = _monkeypatch_aliases(tree)
        raw_lines = source.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            receiver = node.func.value
            if not isinstance(receiver, ast.Name) or receiver.id not in aliases:
                continue
            line = node.lineno
            source_line = raw_lines[line - 1].strip() if 1 <= line <= len(raw_lines) else ""
            uses.append(
                SemanticStandInUse(
                    path=relative_path,
                    line=line,
                    column=node.col_offset,
                    method=node.func.attr,
                    category=_stand_in_category(node.func.attr),
                    source=source_line,
                )
            )

    return SemanticStandInScanResult(
        files_scanned=len(py_files),
        uses=tuple(
            sorted(
                uses,
                key=lambda use: (
                    use.path,
                    use.line,
                    use.column,
                    use.method,
                    use.source,
                ),
            )
        ),
        errors=tuple(sorted(errors)),
    )


def validate_no_mocks(tests_dir: Path, repo_root: Path) -> list[str]:
    """Return lexical mock-framework violations for backward compatibility.

    Args:
        tests_dir: The directory containing test files.
        repo_root: Repository root path to make output relative.

    Returns:
        List of formatted violation strings. Empty list means no violations.
    """
    result = scan_lexical_mock_policy(tests_dir, repo_root)
    for error in result.errors:
        logger.warning(error)
    return list(result.violations)


__all__ = [
    "LexicalMockScanResult",
    "SemanticStandInScanResult",
    "SemanticStandInUse",
    "StandInCategory",
    "scan_lexical_mock_policy",
    "scan_semantic_standins",
    "scan_test_roots",
    "validate_no_mocks",
]
