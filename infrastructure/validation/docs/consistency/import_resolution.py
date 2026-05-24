"""Doc import resolution checks."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import re
from pathlib import Path

from infrastructure.validation.docs.consistency._shared import (
    Inconsistency,
    SHELL_NOQA_RE,
    iter_long_lived_docs,
    line_has_noqa,
    read_markdown,
)

_ANY_FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[A-Za-z0-9_+-]*)[ \t]*\n"
    r"(?P<body>.*?)\n[ \t]*(?P=fence)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
_CODE_LANGS: frozenset[str] = frozenset({"python", "py", "python3", "", "text", "console", "bash", "sh", "shell"})
_DASH_M_RE = re.compile(r"-m\s+(?P<mod>infrastructure(?:\.[A-Za-z_]\w*)+)")
_IMPORT_START_RE = re.compile(r"^\s*(?:from\s+infrastructure|import\s+infrastructure)\b")


def _module_member_exists(module: str, name: str) -> bool:
    """True if ``name`` is an attribute of ``module`` or an importable submodule."""
    try:
        mod = importlib.import_module(module)
    except BaseException:  # noqa: BLE001 - any import failure = unresolved
        return False
    if name == "*" or hasattr(mod, name):
        return True
    try:
        importlib.import_module(f"{module}.{name}")
        return True
    except BaseException:  # noqa: BLE001
        return False


def _resolve_import_statement(stmt: str) -> str | None:
    """Return an error string if an ``infrastructure`` import does not resolve, else None."""
    try:
        tree = ast.parse(stmt.strip())
    except SyntaxError as e:
        return f"unparseable import: {e.msg}"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if not mod.startswith("infrastructure"):
                continue
            try:
                importlib.import_module(mod)
            except BaseException as e:  # noqa: BLE001
                return f"module '{mod}' not importable ({type(e).__name__})"
            for alias in node.names:
                if not _module_member_exists(mod, alias.name):
                    return f"cannot import '{alias.name}' from '{mod}'"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("infrastructure"):
                    try:
                        importlib.import_module(alias.name)
                    except BaseException as e:  # noqa: BLE001
                        return f"module '{alias.name}' not importable ({type(e).__name__})"
    return None


def check_doc_imports_resolve(repo_root: Path) -> list[Inconsistency]:
    """Flag ``infrastructure`` imports / ``-m infrastructure.X`` in docs that don't resolve."""
    issues: list[Inconsistency] = []
    for md in iter_long_lived_docs(repo_root):
        raw = read_markdown(md)
        if raw is None:
            continue
        for fence in _ANY_FENCE_RE.finditer(raw):
            if fence.group("lang").lower() not in _CODE_LANGS:
                continue
            body = fence.group("body")
            base_line = raw[: fence.start("body")].count("\n") + 1
            body_lines = body.splitlines()
            i = 0
            while i < len(body_lines):
                line = body_lines[i]
                line_no = base_line + i
                if line_has_noqa(line) or SHELL_NOQA_RE.search(line):
                    i += 1
                    continue
                for m in _DASH_M_RE.finditer(line):
                    mod = m.group("mod")
                    try:
                        if importlib.util.find_spec(mod) is None:
                            raise ModuleNotFoundError(mod)
                    except BaseException:  # noqa: BLE001
                        issues.append(
                            Inconsistency(
                                file=md,
                                line=line_no,
                                category="doc-import",
                                detail=f"`-m {mod}` is not an importable module",
                            )
                        )
                if _IMPORT_START_RE.match(line):
                    stmt = line
                    j = i
                    while ("(" in stmt and ")" not in stmt) or stmt.rstrip().endswith("\\"):
                        j += 1
                        if j >= len(body_lines):
                            break
                        stmt += "\n" + body_lines[j]
                    if not (line_has_noqa(stmt) or SHELL_NOQA_RE.search(stmt)):
                        err = _resolve_import_statement(stmt.replace("\\\n", "\n"))
                        if err:
                            issues.append(
                                Inconsistency(
                                    file=md,
                                    line=line_no,
                                    category="doc-import",
                                    detail=f"{err} (append `# noqa: docs-lint` for an intentional example)",
                                )
                            )
                    i = j
                i += 1
    return issues
