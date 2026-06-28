"""Mock validator module.

Validates that no mock objects or frameworks are used in tests,
enforcing the 'No Mocks Policy' for cognitive integrity.

Detection is two-pass and deliberately hard to bypass:

1. **Imports** are found with :mod:`ast`, so ``from unittest import mock``,
   ``import unittest.mock``, ``from unittest.mock import …``, ``import mock``,
   and ``import pytest_mock`` are all caught regardless of surrounding text.
2. **Call / decorator usage** is matched against comment-stripped source with
   word-boundary patterns, so a trailing ``# comment`` or a ``mock_``-prefixed
   variable name can no longer hide a real ``MagicMock()`` (the historical
   bypass: the old skip list treated a bare ``#`` or the substring ``mock_``
   appearing *anywhere* on the line as a reason to skip it entirely).

``pytest``'s ``monkeypatch`` fixture is permitted by policy and is never a
NAME collision with ``patch`` (distinct tokens). A line may opt out explicitly
with a ``# no-mocks-ok:`` trailing comment when a forbidden token legitimately
appears in non-test scaffolding.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Explicit opt-out token (kept narrow — not a bare ``#``).
_SUPPRESSION_TOKEN = "# no-mocks-ok:"  # nosec B105

# Modules whose import is, by itself, a no-mocks violation.
_FORBIDDEN_IMPORT_ROOTS = frozenset({"mock", "pytest_mock"})
_FORBIDDEN_UNITTEST_SUBMODULE = "mock"  # unittest.mock

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


def _import_violations(tree: ast.AST) -> set[int]:
    """Return line numbers of forbidden mock-framework imports."""
    flagged: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_IMPORT_ROOTS or alias.name == "unittest.mock":
                    flagged.add(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # from unittest import mock  /  from unittest.mock import X
            if module == "unittest" and any(a.name == _FORBIDDEN_UNITTEST_SUBMODULE for a in node.names):
                flagged.add(node.lineno)
            elif module == "unittest.mock" or module.split(".")[0] in _FORBIDDEN_IMPORT_ROOTS:
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


def validate_no_mocks(tests_dir: Path, repo_root: Path) -> list[str]:
    """Scan ``tests_dir`` for mock usage and return a list of violation messages.

    Args:
        tests_dir: The directory containing test files.
        repo_root: Repository root path to make output relative.

    Returns:
        List of formatted violation strings. Empty list means no violations.
    """
    violations: list[str] = []

    if not tests_dir.exists():
        return violations

    for py_file in tests_dir.rglob("*.py"):
        # ``fixtures/`` holds sample inputs and vendored real-codebase snapshots
        # (e.g. ``tests/fixtures/real_codebases/<project>/``) — not the project's
        # own test suite. Such third-party source legitimately contains tokens
        # like ``.patch(`` (HTTP verbs), so it is out of scope for the policy.
        if "fixtures" in py_file.relative_to(tests_dir).parts:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {py_file}: {e}")
            continue

        relative_path = py_file.relative_to(repo_root)
        flagged_lines: dict[int, str] = {}

        # Pass 1 — imports via AST (robust against comments/aliasing).
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            tree = None
        if tree is not None:
            lines = source.splitlines()
            for lineno in _import_violations(tree):
                if 1 <= lineno <= len(lines):
                    flagged_lines[lineno] = lines[lineno - 1].strip()

        # Pass 2 — call / decorator usage on comment-and-string-stripped code.
        raw_lines = source.splitlines()
        code_lines = _code_only_lines(source)
        if code_lines is None:
            # Tokenization failed; fall back to a per-line '#'-split (imperfect
            # for '#' inside strings, but the AST import pass already ran).
            code_lines = {i: ln.split("#", 1)[0] for i, ln in enumerate(raw_lines, 1)}
        for line_num, code in code_lines.items():
            if line_num in flagged_lines:
                continue
            raw_line = raw_lines[line_num - 1] if 1 <= line_num <= len(raw_lines) else ""
            if _SUPPRESSION_TOKEN in raw_line:
                continue
            if not code.strip():
                continue
            if any(pat.search(code) for pat in _USAGE_PATTERNS):
                flagged_lines[line_num] = raw_line.strip()

        for line_num in sorted(flagged_lines):
            violations.append(f"{relative_path}:{line_num}: {flagged_lines[line_num]}")

    return violations
