"""Public repository documentation audit helpers.

This module is intentionally advisory. Strict pass/fail checks remain in
``lint_runner`` and ``consistency``; the audit here inventories the public
documentation surface and exposes RedTeam-style false-certification risks that
are too semantic to make blanket failures on the first pass.
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from infrastructure.project.public_scope import public_ci_source_paths
from infrastructure.validation.docs.consistency._shared import Inconsistency, blank_fences
from infrastructure.validation.docs.consistency.memory_decision import check_memory_decision_rule_links
from infrastructure.validation.docs.lint_runner import doc_roots
from infrastructure.validation.docs.scan_scope import DEFAULT_EXCLUDE_PARTS, iter_markdown_files, should_exclude_path

_TEMPLATE_SLUG_RE = re.compile(r"\btemplate_[A-Za-z0-9_]+\b")
_PROJECT_COUNT_RE = re.compile(
    r"\b(?:\d+|nine|ten)\s+"
    r"(?:current|active|rendered|public|permanent|canonical|template)\s+"
    r"(?:projects|exemplars|templates)\b"
    r"|"
    r"\b(?:current|active|rendered|public|permanent|canonical|template)\s+"
    r"(?:projects|exemplars|templates)\b.{0,80}\b(?:\d+|nine|ten)\b",
    re.IGNORECASE,
)
_GENERATED_FACT_LINK_RE = re.compile(
    r"docs/_generated/(?:active_projects|canonical_facts|publication_records)\.md|"
    r"_generated/|PUBLIC_PROJECT_NAMES|generate_publication_records_doc\.py|"
    r"\$\{public_exemplar_list\}|\$\{project_count\}",
    re.I,
)
_ROSTER_CONTEXT_RE = re.compile(
    r"\b(?:current|active|rendered|public|permanent|always-present|roster|set|all)\b|"
    r"under\s+`?projects/templates/?`?",
    re.IGNORECASE,
)

_GATE_CLAIM_RE = re.compile(
    r"\b(?:validator|verifier|schema|quality gate|gate|checker|linter|lint|rule)\b"
    r".{0,100}\b(?:must|requires?|enforces?|validates?|certifies?|proves?|guarantees?|blocks?|fails?)\b"
    r"|"
    r"\b(?:must|requires?|enforces?|validates?|certifies?|proves?|guarantees?|blocks?|fails?)\b"
    r".{0,100}\b(?:validator|verifier|schema|quality gate|gate|checker|linter|lint|rule)\b",
    re.IGNORECASE,
)
_NEGATIVE_CONTROL_RE = re.compile(
    r"negative[- ]control|known[- ]wrong|counterexample|fault[- ]inject|expected[- ]fail|bad fixture",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PublicDocRecord:
    """A public Markdown file included in the documentation audit."""

    path: str
    role: str
    line_count: int
    has_links: bool


@dataclass(frozen=True)
class SymbolDocRecord:
    """Documentation status for one Python ``def`` or ``class``."""

    path: str
    line: int
    kind: str
    qualname: str
    has_docstring: bool
    mentioned_in_adjacent_docs: bool


@dataclass(frozen=True)
class AuditFinding:
    """A source-backed documentation audit finding."""

    file: str
    line: int
    category: str
    severity: str
    detail: str


@dataclass(frozen=True)
class PublicDocumentationAudit:
    """Report payload for the public documentation audit."""

    doc_count: int
    doc_roles: dict[str, int]
    line_count: int
    symbol_count: int
    undocumented_symbol_count: int
    records: list[PublicDocRecord]
    symbol_records: list[SymbolDocRecord]
    findings: list[AuditFinding]


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _doc_role(path: Path, repo_root: Path) -> str:
    rel = _relative(path, repo_root)
    parts = Path(rel).parts
    if len(parts) == 1:
        return "root"
    if rel.startswith("docs/_generated/"):
        return "generated"
    if rel.startswith("docs/audit/archived/"):
        return "archived-audit"
    if rel.startswith("docs/audit/"):
        return "audit"
    if rel.startswith("docs/architecture/adrs/"):
        return "adr"
    if rel.startswith("projects/templates/"):
        if path.name == "AGENTS.md":
            return "project-agents"
        if path.name == "README.md":
            return "project-readme"
        return "project-doc"
    if path.name == "AGENTS.md":
        return "agents"
    if path.name == "README.md":
        return "readme"
    if path.name == "SKILL.md":
        return "skill"
    if parts and parts[0] == "docs":
        return "repo-doc"
    return "module-doc"


def collect_public_markdown(repo_root: Path) -> list[PublicDocRecord]:
    """Inventory public Markdown under the existing docs-lint roots."""
    records: list[PublicDocRecord] = []
    for path in iter_markdown_files(doc_roots(repo_root), exclude_parts=DEFAULT_EXCLUDE_PARTS):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        records.append(
            PublicDocRecord(
                path=_relative(path, repo_root),
                role=_doc_role(path, repo_root),
                line_count=len(text.splitlines()),
                has_links="](" in text,
            )
        )
    return records


def _iter_policy_docs(repo_root: Path) -> list[Path]:
    excluded = set(DEFAULT_EXCLUDE_PARTS) | {"_generated", "audit", "streams"}
    return iter_markdown_files(doc_roots(repo_root), exclude_parts=excluded)


def find_volatile_fact_claims(repo_root: Path) -> list[AuditFinding]:
    """Find drift-prone project roster/count claims without generated-source links."""
    findings: list[AuditFinding] = []
    for path in _iter_policy_docs(repo_root):
        try:
            lines = blank_fences(path.read_text(encoding="utf-8")).splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        in_generated_block = False
        for line_no, line in enumerate(lines, 1):
            if "<!-- BEGIN:" in line:
                in_generated_block = True
            if in_generated_block:
                if "<!-- END:" in line:
                    in_generated_block = False
                continue
            window = "\n".join(lines[max(0, line_no - 4) : min(len(lines), line_no + 5)])
            if _GENERATED_FACT_LINK_RE.search(window):
                continue
            slugs = _TEMPLATE_SLUG_RE.findall(line)
            roster_like = len(set(slugs)) >= 3 and bool(_ROSTER_CONTEXT_RE.search(line))
            count_like = bool(_PROJECT_COUNT_RE.search(line))
            if not (roster_like or count_like):
                continue
            findings.append(
                AuditFinding(
                    file=_relative(path, repo_root),
                    line=line_no,
                    category="volatile-fact",
                    severity="warning",
                    detail=(
                        "appears to hard-code a project roster or count without linking "
                        "to docs/_generated/active_projects.md or canonical_facts.md"
                    ),
                )
            )
    return findings


def find_gate_claims_without_negative_controls(repo_root: Path) -> list[AuditFinding]:
    """Find verifier/gate enforcement claims whose local context lacks a negative control."""
    findings: list[AuditFinding] = []
    for path in _iter_policy_docs(repo_root):
        try:
            lines = blank_fences(path.read_text(encoding="utf-8")).splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(lines, 1):
            if not _GATE_CLAIM_RE.search(line):
                continue
            window = "\n".join(lines[max(0, line_no - 4) : min(len(lines), line_no + 4)])
            if _NEGATIVE_CONTROL_RE.search(window):
                continue
            findings.append(
                AuditFinding(
                    file=_relative(path, repo_root),
                    line=line_no,
                    category="gate-negative-control",
                    severity="advisory",
                    detail=(
                        "claims a verifier, gate, schema, or rule enforces behavior, "
                        "but nearby prose does not name a negative control or known-wrong fixture"
                    ),
                )
            )
    return findings


def _iter_python_files(repo_root: Path) -> list[Path]:
    roots = [repo_root / path for path in public_ci_source_paths(repo_root)]
    scripts = repo_root / "scripts"
    if scripts.is_dir():
        roots.append(scripts)

    seen: set[Path] = set()
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if should_exclude_path(path, DEFAULT_EXCLUDE_PARTS):
                continue
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return sorted(files)


@lru_cache(maxsize=None)
def _adjacent_doc_text(directory: Path) -> str:
    parts: list[str] = []
    for name in ("AGENTS.md", "README.md", "SKILL.md"):
        path = directory / name
        if not path.is_file():
            continue
        try:
            parts.append(path.read_text(encoding="utf-8").lower())
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(parts)


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, path: Path, repo_root: Path) -> None:
        self.path = path
        self.repo_root = repo_root
        self.stack: list[str] = []
        self.records: list[SymbolDocRecord] = []

    def _record(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, kind: str) -> None:
        qualname = ".".join((*self.stack, node.name))
        adjacent = _adjacent_doc_text(self.path.parent)
        symbol_refs = {node.name.lower(), qualname.lower(), self.path.name.lower(), self.path.stem.lower()}
        self.records.append(
            SymbolDocRecord(
                path=_relative(self.path, self.repo_root),
                line=node.lineno,
                kind=kind,
                qualname=qualname,
                has_docstring=ast.get_docstring(node) is not None,
                mentioned_in_adjacent_docs=any(ref in adjacent for ref in symbol_refs),
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:  # noqa: N802
        self._record(node, "class")
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:  # noqa: N802
        self._record(node, "def")
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:  # noqa: N802
        self._record(node, "async def")
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()


def collect_symbol_documentation(repo_root: Path) -> list[SymbolDocRecord]:
    """Scan every public ``def`` and ``class`` for docstring and adjacent-doc coverage."""
    records: list[SymbolDocRecord] = []
    for path in _iter_python_files(repo_root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        visitor = _SymbolVisitor(path, repo_root)
        visitor.visit(tree)
        records.extend(visitor.records)
    return records


def _symbol_findings(symbols: list[SymbolDocRecord]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for record in symbols:
        leaf = record.qualname.rsplit(".", 1)[-1]
        if leaf.startswith("_"):
            continue
        if record.has_docstring or record.mentioned_in_adjacent_docs:
            continue
        findings.append(
            AuditFinding(
                file=record.path,
                line=record.line,
                category="symbol-documentation",
                severity="advisory",
                detail=(
                    f"{record.kind} `{record.qualname}` has no docstring and is not "
                    "mentioned in adjacent README/AGENTS/SKILL docs"
                ),
            )
        )
    return findings


def _from_inconsistency(issue: Inconsistency, repo_root: Path) -> AuditFinding:
    return AuditFinding(
        file=_relative(issue.file, repo_root),
        line=issue.line,
        category=issue.category,
        severity="error",
        detail=issue.detail,
    )


def build_public_documentation_audit(repo_root: Path) -> PublicDocumentationAudit:
    """Build a source-backed advisory audit for the public documentation surface."""
    repo_root = repo_root.resolve()
    records = collect_public_markdown(repo_root)
    symbols = collect_symbol_documentation(repo_root)

    findings = [
        *find_volatile_fact_claims(repo_root),
        *find_gate_claims_without_negative_controls(repo_root),
        *[_from_inconsistency(issue, repo_root) for issue in check_memory_decision_rule_links(repo_root)],
        *_symbol_findings(symbols),
    ]

    role_counts = Counter(record.role for record in records)
    undocumented = sum(1 for record in symbols if not record.has_docstring)
    return PublicDocumentationAudit(
        doc_count=len(records),
        doc_roles=dict(sorted(role_counts.items())),
        line_count=sum(record.line_count for record in records),
        symbol_count=len(symbols),
        undocumented_symbol_count=undocumented,
        records=records,
        symbol_records=symbols,
        findings=findings,
    )


def audit_to_dict(audit: PublicDocumentationAudit) -> dict[str, Any]:
    """Convert an audit payload to JSON-serializable dictionaries."""
    return asdict(audit)


def format_audit_json(audit: PublicDocumentationAudit) -> str:
    """Return the audit payload as pretty JSON."""
    return json.dumps(audit_to_dict(audit), indent=2, sort_keys=True) + "\n"


def format_audit_markdown(audit: PublicDocumentationAudit, *, max_findings: int = 80) -> str:
    """Return a compact source-backed Markdown report."""
    lines = [
        "# Public Documentation RedTeam Audit",
        "",
        "This report is advisory. Blocking checks remain in `scripts/lint_docs.py` and",
        "`scripts/check_template_drift.py`; this surface inventories documentation and",
        "highlights likely false-certification risks for follow-up hardening.",
        "",
        "## Inventory",
        "",
        f"- Markdown files: {audit.doc_count}",
        f"- Markdown lines: {audit.line_count}",
        f"- Python def/class records scanned: {audit.symbol_count}",
        f"- Symbols without docstrings: {audit.undocumented_symbol_count}",
        "",
        "## Documentation Roles",
        "",
    ]
    for role, count in audit.doc_roles.items():
        lines.append(f"- `{role}`: {count}")

    lines.extend(["", "## Findings", ""])
    if not audit.findings:
        lines.append("No advisory findings.")
    else:
        for finding in audit.findings[:max_findings]:
            lines.append(
                f"- `{finding.severity}` `{finding.category}` {finding.file}:{finding.line} - {finding.detail}"
            )
        if len(audit.findings) > max_findings:
            lines.append(f"- ... {len(audit.findings) - max_findings} additional findings omitted")

    lines.extend(
        [
            "",
            "## Scope",
            "",
            "Source roots come from `infrastructure.validation.docs.lint_runner.doc_roots()`.",
        ]
    )
    return "\n".join(lines) + "\n"


__all__ = [
    "AuditFinding",
    "PublicDocRecord",
    "PublicDocumentationAudit",
    "SymbolDocRecord",
    "audit_to_dict",
    "build_public_documentation_audit",
    "collect_public_markdown",
    "collect_symbol_documentation",
    "find_gate_claims_without_negative_controls",
    "find_volatile_fact_claims",
    "format_audit_json",
    "format_audit_markdown",
]
