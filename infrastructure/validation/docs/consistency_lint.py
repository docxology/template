"""Documentation consistency linter.

Two checks:

1. :func:`check_module_count_claims` — discovers the live count of Python packages
   under ``infrastructure/`` (directories that ship ``__init__.py``) and verifies
   every Markdown claim of the form ``N Python (sub)?packages?`` matches that count.

2. :func:`check_no_ghost_projects` — flags rotating project names that are
   referenced unconditionally as a path (``projects/<name>/...``) in long-lived docs
   when the project is not currently under ``projects/`` (per
   :func:`infrastructure.project.discovery.discover_projects`).

Both functions return :class:`Inconsistency` records and never mutate state.
"""

import ast
import importlib
import importlib.util
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.discovery import discover_projects
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS

logger = get_logger(__name__)


_DEFAULT_LONG_LIVED_DOC_ROOTS: tuple[str, ...] = (
    "docs",
    "infrastructure",
    ".github",
    "tests",
    "projects/template_code_project",
    "projects/template_prose_project",
)
"""Top-level dirs that contain long-lived docs subject to the consistency checks.

``tests`` was added 2026-05-15 after a repo-wide triple-check found real import
and command-convention rot in ``tests/**/AGENTS.md`` that this gate had never
covered (it was a structural scope blind spot). The two tracked exemplar
projects are included because their manuscripts/docs are public template
contracts; private symlinked projects, archives, WIP trees, and ``output/`` stay
outside this source-doc sweep. ``docs/_generated/``, ``docs/audit/``, and
``docs/streams/`` remain excluded by
:data:`_DEFAULT_GHOST_EXCLUDE_PARTS` by deliberate policy — they are
historical/audit/generated records, not authoritative current docs.
"""

_DEFAULT_GHOST_EXCLUDE_PARTS: frozenset[str] = DEFAULT_EXCLUDE_PARTS | frozenset({"_generated", "audit", "streams"})

# Phrases that contextualize a project mention as conditional/historical.
_CONDITIONAL_PHRASES: tuple[str, ...] = (
    "rotating",
    "rotate",
    "rotates",
    "in progress",
    "archived",
    "archive",
    "when present",
    "when checked out",
    "is checked out",
    "if exists",
    "if checked out",
    "if truthy",
    "in the working tree",
    "previously",
    "formerly",
    "absent",
    "may rotate",
    "no longer",
    "for example",
    "e.g.",
    "e.g ",
    "guard",
    "skipping",
    "skipped",
    "hashfiles",
    "promote",
    "promoted",
    "checked out under",
    "when the working tree",
    "when this tree",
    "is present",  # "when projects/fep_lean/ is present"
    "when ",  # broad — but combined with project paths this is conditional
    "only when",
    "only if",
    "conditional on",
    "if `",  # markdown shell snippets ("if `projects/foo/...` exists")
    "noqa: docs-lint",
)

# Tightened claim regex: must read "<N> Python (sub)packages" with N >= 2 (so we don't
# match generic singular phrasing like "Each Layer-1 Python package ships ...").
# Tolerates markdown bold/italic markers (``**N**``, ``__N__``) and matches both
# "Python packages" and "subpackages" (without "Python") when ``infrastructure``
# also appears on the same line.
_PACKAGE_COUNT_LINE_RE = re.compile(
    r"^.*?(?:\*\*|__|`)?(?P<n>\d{2,}|[2-9])(?:\*\*|__|`)?\s+(?:top-level\s+)?Python\s+(?:sub)?packages\b.*$",
    re.IGNORECASE | re.MULTILINE,
)
_SUBPACKAGE_COUNT_LINE_RE = re.compile(
    r"^.*?(?:\*\*|__|`)?(?P<n>\d{2,}|[2-9])(?:\*\*|__|`)?\s+subpackages\b.*?infrastructure.*$",
    re.IGNORECASE | re.MULTILINE,
)

# Fenced code blocks (``` or ~~~). Allow leading whitespace so indented fences match.
_FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,}).*?\n.*?\n[ \t]*(?P=fence)",
    re.MULTILINE | re.DOTALL,
)


def _blank_fences(text: str) -> str:
    """Replace fenced code blocks with same-shape whitespace so line numbers stay stable."""

    def _blank(match: re.Match[str]) -> str:
        s = match.group(0)
        return "".join("\n" if ch == "\n" else " " for ch in s)

    return _FENCE_RE.sub(_blank, text)


# Default Markdown sweep extensions.
_MD_GLOB = "*.md"


@dataclass(frozen=True)
class Inconsistency:
    """A single doc consistency issue."""

    file: Path
    line: int
    category: str  # e.g. "module-count", "ghost-project"
    detail: str

    def format(self) -> str:
        """Return a single-line summary."""
        return f"{self.file}:{self.line}: [{self.category}] {self.detail}"


def _discover_infra_packages(repo_root: Path) -> list[str]:
    """Return sorted package names directly under ``infrastructure/``.

    A "package" is a subdirectory of ``infrastructure/`` that ships ``__init__.py``.
    Mirrors how Python actually treats them (excludes config-only dirs like
    ``logrotate.d/`` and ``docker/`` that don't have ``__init__.py``).
    """
    infra_root = repo_root / "infrastructure"
    if not infra_root.is_dir():
        return []
    return sorted(
        d.name
        for d in infra_root.iterdir()
        if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_") and (d / "__init__.py").is_file()
    )


def _iter_long_lived_docs(
    repo_root: Path,
    extra_roots: Iterable[Path] | None = None,
    exclude_parts: Iterable[str] = _DEFAULT_GHOST_EXCLUDE_PARTS,
) -> list[Path]:
    """Yield Markdown files under long-lived doc roots."""
    roots: list[Path] = []
    for sub in _DEFAULT_LONG_LIVED_DOC_ROOTS:
        candidate = repo_root / sub
        if candidate.is_dir():
            roots.append(candidate)
    # Repo-root .md files (README, AGENTS, CLAUDE, TO-DO).
    if repo_root.is_dir():
        for md in repo_root.glob(_MD_GLOB):
            roots.append(md)
    if extra_roots:
        roots.extend(Path(p) for p in extra_roots)

    excluded = set(exclude_parts)
    out: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root.is_file() and root.suffix.lower() == ".md":
            if root not in seen:
                seen.add(root)
                out.append(root)
            continue
        if not root.is_dir():
            continue
        for md in root.rglob(_MD_GLOB):
            if any(part in excluded for part in md.parts):
                continue
            if md in seen:
                continue
            seen.add(md)
            out.append(md)
    return sorted(out)


def check_module_count_claims(repo_root: Path, expected_count: int | None = None) -> list[Inconsistency]:
    """Verify Markdown claims about ``N Python (sub)packages`` match reality.

    Args:
        repo_root: Repository root.
        expected_count: Override the discovered count (mostly for tests).

    Returns:
        One :class:`Inconsistency` per stale claim.
    """
    expected = expected_count if expected_count is not None else len(_discover_infra_packages(repo_root))
    issues: list[Inconsistency] = []
    for md in _iter_long_lived_docs(repo_root):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("skipping %s: %s", md, e)
            continue
        text = _blank_fences(raw)
        seen_lines: set[int] = set()
        for regex in (_PACKAGE_COUNT_LINE_RE, _SUBPACKAGE_COUNT_LINE_RE):
            for match in regex.finditer(text):
                claimed = int(match.group("n"))
                if claimed != expected:
                    line = text[: match.start()].count("\n") + 1
                    if line in seen_lines:
                        continue
                    seen_lines.add(line)
                    # Allow `<!-- noqa: docs-lint -->` on the same line.
                    line_text = text.splitlines()[line - 1] if 0 < line <= len(text.splitlines()) else ""
                    if _line_has_noqa(line_text):
                        continue
                    issues.append(
                        Inconsistency(
                            file=md,
                            line=line,
                            category="module-count",
                            detail=(f"claims {claimed} Python (sub)packages but infrastructure/ ships {expected}"),
                        )
                    )
    return issues


def _line_is_conditional(line: str) -> bool:
    """True if *line* contains language that contextualizes a rotating-project mention."""
    low = line.lower()
    return any(phrase in low for phrase in _CONDITIONAL_PHRASES)


# Inline escape hatch — append `<!-- noqa: docs-lint -->` (optionally with a free-form
# explanatory comment) to a Markdown line to suppress both ghost-project and
# module-count warnings on that line. We only need to confirm the marker token
# ``noqa: docs-lint`` is present inside an HTML comment; we don't try to validate
# the comment's closing ``-->`` because doc authors often add an explanation that
# itself contains hyphens.
_NOQA_RE = re.compile(r"<!--\s*noqa:\s*docs-lint", re.IGNORECASE)


def _line_has_noqa(line: str) -> bool:
    """True if the line carries an inline ``<!-- noqa: docs-lint -->`` comment."""
    return bool(_NOQA_RE.search(line))


# Documentation placeholder names — common stand-ins in scaffold/migration guides.
# These are NOT real project names so they should never trigger ghost-project warnings.
_STATIC_PLACEHOLDER_NAMES: frozenset[str] = frozenset(
    {
        "biology_textbook",  # legacy migration-guide example
        "template",  # in-progress scaffold dir; not a real project
        "code_project",  # generic scaffolding example
        "prose_project",
        "search_project",
        "research",
        "myresearch",
        "name",
        "project",
        "project_name",
        "PROJECT",
        "PROJECT_NAME",
        "PROJECT_SLUG",
    }
)


def _is_placeholder_name(name: str) -> bool:
    """Return True if *name* looks like a template placeholder rather than a real project.

    Matches:
      - Anything containing ``<...>`` or ``{...}`` (placeholder syntax).
      - Names starting with ``my_``, ``your_``, ``example_``, ``sample_``,
        ``custom_``, ``foo``, ``bar``.
      - All-caps tokens (``PROJECT``, ``PROJECT_SLUG``).
      - Anything in :data:`_STATIC_PLACEHOLDER_NAMES`.
    """
    if "<" in name or "{" in name or ">" in name or "}" in name:
        return True
    if name.isupper():
        return True
    if name in _STATIC_PLACEHOLDER_NAMES:
        return True
    lower = name.lower()
    for prefix in ("my_", "your_", "example_", "sample_", "custom_", "foo", "bar"):
        if lower.startswith(prefix):
            return True
    return False


def check_no_ghost_projects(
    repo_root: Path,
    canonical: tuple[str, ...] = (
        "template_code_project",
        "template_prose_project",
        "template_search_project",
    ),
    extra_active: Iterable[str] | None = None,
) -> list[Inconsistency]:
    """Flag unconditional ``projects/<name>/...`` references for non-active projects.

    A reference is reported only if **all** of the following hold:
      - The line contains a literal ``projects/<name>/`` token.
      - ``<name>`` is **not** currently active per :func:`discover_projects`.
      - ``<name>`` is **not** in *canonical*.
      - The line does **not** contain a conditional / historical phrase
        (``"rotating"``, ``"when present"``, ``"in progress"``, ``"archived"``, …).

    This is conservative by design so the check passes on a clean repo where
    rotating-project mentions are properly contextualized.
    """
    active_names = {p.name for p in discover_projects(repo_root)}
    if extra_active:
        active_names.update(extra_active)
    allow = active_names | set(canonical)

    # Match `projects/<name>/` only when `projects` starts a path-like token (i.e.
    # is not preceded by an identifier char or `/`). This rules out
    # ``custom_projects/foo/`` and ``my_projects/bar/``. Allow ``{...}`` and
    # ``<...>`` placeholders for template-style paths.
    pattern = re.compile(r"(?<![A-Za-z0-9_/])projects/(?P<name>\{[^}]+\}|<[^>]+>|[A-Za-z0-9_][A-Za-z0-9_.-]*)/")

    issues: list[Inconsistency] = []
    for md in _iter_long_lived_docs(repo_root):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("skipping %s: %s", md, e)
            continue
        text = _blank_fences(raw)
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            if _line_is_conditional(raw_line) or _line_has_noqa(raw_line):
                continue
            for match in pattern.finditer(raw_line):
                name = match.group("name")
                if name in allow:
                    continue
                # Defensive: skip a few path tokens that aren't really project names.
                if name in {"AGENTS.md", "README.md"}:
                    continue
                # Skip template placeholders that show up in scaffolding/example docs.
                if _is_placeholder_name(name):
                    continue
                issues.append(
                    Inconsistency(
                        file=md,
                        line=line_no,
                        category="ghost-project",
                        detail=(
                            f"hard-codes 'projects/{name}/' but '{name}' is not in "
                            "docs/_generated/active_projects.md and is not a "
                            "canonical exemplar"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Command-convention check
#
# canonical_facts.md mandates `uv run` for reproducibility and explicitly says
# "Avoid raw `python3` or `pytest` in documentation." This was the one defect
# class the 2026-05-15 comprehensive audit found *recurring* and *not* caught by
# any existing harness rule (11 parallel zone agents still left 15 command-line
# `pytest` invocations). This rule closes that ingestion point.
#
# Scope is deliberately narrow to avoid false positives:
#   - only shell-tagged fences (```bash / sh / shell / console / zsh) are scanned;
#     prose and ```python blocks are ignored.
#   - only a command-line *invocation* (line's first token is `pytest`/`python3`,
#     optionally behind a `$ ` prompt) is flagged — not nouns like
#     `pytest-httpserver`, `pytest.ini`, or `# pytest ...` comments.
#   - an inline `noqa: docs-lint` comment on the line suppresses the finding
#     (for legitimate "BAD example" / contrast snippets).
# ---------------------------------------------------------------------------

_SHELL_FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[A-Za-z0-9_+-]*)[ \t]*\n"
    r"(?P<body>.*?)\n[ \t]*(?P=fence)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
_SHELL_LANGS: frozenset[str] = frozenset({"bash", "sh", "shell", "console", "zsh"})
_BARE_CMD_RE = re.compile(r"^\s*(?:\$\s+)?(?P<cmd>pytest|python3)(?:\s|$)")
# Inside a shell fence an HTML comment is impossible, so a shell-comment
# a `noqa: docs-lint` shell comment is the usable escape hatch for counter-examples.
_SHELL_NOQA_RE = re.compile(r"#\s*noqa:\s*docs-lint", re.IGNORECASE)


def check_command_conventions(repo_root: Path) -> list[Inconsistency]:
    """Flag command-line ``pytest``/``python3`` in shell fences lacking ``uv run``.

    Mirrors :func:`check_module_count_claims` shape; never mutates state.
    """
    issues: list[Inconsistency] = []
    for md in _iter_long_lived_docs(repo_root):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("skipping %s: %s", md, e)
            continue
        for fence in _SHELL_FENCE_RE.finditer(raw):
            if fence.group("lang").lower() not in _SHELL_LANGS:
                continue
            body_start_line = raw[: fence.start("body")].count("\n") + 1
            for offset, line in enumerate(fence.group("body").splitlines()):
                m = _BARE_CMD_RE.match(line)
                if not m or "uv run" in line or _line_has_noqa(line) or _SHELL_NOQA_RE.search(line):
                    continue
                issues.append(
                    Inconsistency(
                        file=md,
                        line=body_start_line + offset,
                        category="command-convention",
                        detail=(
                            f"command-line `{m.group('cmd')}` without `uv run` — "
                            "canonical_facts.md mandates `uv run` (append "
                            "`# noqa: docs-lint` to allow a deliberate counter-example)"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Executable-doc checks (NEW — "make the documentation true against the code")
#
# Every defect class the 2026-05-15 audit hit shared one root cause: docs assert
# things the code already knows and nothing executes the documentation. These
# two checks close that ingestion point deterministically:
#   * check_doc_imports_resolve  — every ``infrastructure...`` import shown in a
#     doc code-fence (and every ``-m infrastructure.X`` invocation) must resolve.
#   * check_readme_files_list    — every ``foo.py`` a package README/AGENTS lists
#     must exist somewhere in that package (kills the vanished-file class).
# Both honor a ``noqa: docs-lint`` shell/HTML comment for deliberate
# illustrative snippets.
# ---------------------------------------------------------------------------

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
    for md in _iter_long_lived_docs(repo_root):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.debug("skipping %s: %s", md, e)
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
                if _line_has_noqa(line) or _SHELL_NOQA_RE.search(line):
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
                    # stitch parenthesised / backslash multi-line imports
                    while ("(" in stmt and ")" not in stmt) or stmt.rstrip().endswith("\\"):
                        j += 1
                        if j >= len(body_lines):
                            break
                        stmt += "\n" + body_lines[j]
                    if not (_line_has_noqa(stmt) or _SHELL_NOQA_RE.search(stmt)):
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


_FILES_LIST_RE = re.compile(r"^\s*[-*]\s*`?(?P<f>[A-Za-z_]\w*\.py)`?\s*(?:[—:-].*)?$")


def check_readme_files_list(repo_root: Path) -> list[Inconsistency]:
    """Flag ``foo.py`` listed in a package README/AGENTS that exists nowhere in that package."""
    infra = repo_root / "infrastructure"
    if not infra.is_dir():
        return []
    issues: list[Inconsistency] = []
    for doc_name in ("README.md", "AGENTS.md"):
        for doc in infra.rglob(doc_name):
            pkg_dir = doc.parent
            if not (pkg_dir / "__init__.py").is_file():
                continue
            present = {p.name for p in pkg_dir.rglob("*.py")}
            try:
                lines = doc.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            in_fence = False
            for n, line in enumerate(lines, 1):
                if re.match(r"^[ \t]*(`{3,}|~{3,})", line):
                    in_fence = not in_fence
                    continue
                if in_fence or _line_has_noqa(line):
                    continue
                fm = _FILES_LIST_RE.match(line)
                if fm and fm.group("f") not in present:
                    issues.append(
                        Inconsistency(
                            file=doc,
                            line=n,
                            category="doc-files-list",
                            detail=(
                                f"lists `{fm.group('f')}` but no such file exists under "
                                f"{pkg_dir.relative_to(repo_root)}/ (vanished or renamed)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# SSOT count-singularity (Track 2 decay-proofing): the volatile infrastructure
# ``.py`` file-count literal may live only in docs/_generated/canonical_facts.md
# (the hand-maintained single source of truth). Anywhere else it must link, not
# duplicate — a hard-coded "NNN .py files" elsewhere is drift waiting to happen.
# ---------------------------------------------------------------------------

_PY_COUNT_RE = re.compile(r"\b\d{3}\s*(?:`?\.py`?|Python)\s+files\b", re.IGNORECASE)


def check_canonical_count_singularity(repo_root: Path) -> list[Inconsistency]:
    """Flag a bare ``NNN .py files`` literal outside canonical_facts.md."""
    canonical = repo_root / "docs" / "_generated" / "canonical_facts.md"
    issues: list[Inconsistency] = []
    for md in _iter_long_lived_docs(repo_root):
        if md.resolve() == canonical.resolve():
            continue
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(raw.splitlines(), 1):
            if _PY_COUNT_RE.search(line) and not (_line_has_noqa(line) or _SHELL_NOQA_RE.search(line)):
                issues.append(
                    Inconsistency(
                        file=md,
                        line=n,
                        category="count-singularity",
                        detail=(
                            "hard-codes a volatile infrastructure .py-file count — link to "
                            "docs/_generated/canonical_facts.md instead (it drifts as the tree "
                            "changes); add `# noqa: docs-lint` only for a measured, dated note"
                        ),
                    )
                )
    return issues


__all__ = [
    "Inconsistency",
    "check_canonical_count_singularity",
    "check_command_conventions",
    "check_doc_imports_resolve",
    "check_module_count_claims",
    "check_no_ghost_projects",
    "check_readme_files_list",
]
