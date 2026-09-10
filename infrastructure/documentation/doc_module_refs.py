"""Documentation ``infrastructure.*`` module-reference resolution.

Resolves every ``infrastructure.*`` dotted path referenced in ``docs/``,
``README.md``, and ``AGENTS.md`` to a real module on disk, so a module split
or rename cannot silently stale documentation references. The thin CLI that
runs this logic lives in ``scripts/audit/check_doc_module_refs.py``.

Resolution rules (documented contract):

- A dotted reference resolves by walking its segments from ``infrastructure/``:
  module files (``<prefix>.py``), packages (``<prefix>/__init__.py``), and
  attribute tails whose final name is defined or imported in the deepest
  module (see :func:`dotted_ref_resolves`). CLI-subcommand words after the
  module (``infrastructure.project.public_scope lint-paths``) never join the
  dotted path. Anything unresolvable is a finding.
- Only ``infrastructure.*`` references with at least one dotted segment are
  scanned; parameter flags such as ``--cov=infrastructure`` and slash-style
  paths such as ``infrastructure/core/files.py`` are not module references and
  never match. A ``.py`` suffix on a dotted reference is a file-extension
  mention of the module (``infrastructure.mcp_server.py``) and is stripped
  before resolution.
- ``docs/audit/`` and ``docs/_generated/`` are skipped: the former holds
  dated point-in-time audit receipts that are historical evidence rather
  than maintained documentation (per docs/audit/README.md), the latter is
  generator-owned — the same exclusion classes as the docs-lint scan scope.
  Every other ``docs/**/*.md`` plus the root ``README.md`` and ``AGENTS.md``
  are scanned.
- A small explicit allowlist covers the generic placeholder names and
  historical remediation records the current tree uses; every entry carries
  a reason comment.
- The existing repo-wide ``# noqa: docs-lint`` line suppression is honored so
  this gate shares the documentation escape hatch instead of inventing a new
  suppression format.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# ``infrastructure`` followed by at least one dotted identifier segment.
# Word-character segments stop at punctuation, so trailing sentence periods,
# ``-`` in subcommand names (``link-projects``), and ``(`` are excluded.
_MODULE_REF_RE = re.compile(r"infrastructure(?:\.[A-Za-z_][A-Za-z0-9_]*)+")

# Shared repo-wide documentation escape hatch (see scripts/audit/lint_docs.py).
_NOQA_RE = re.compile(r"noqa:\s*docs-lint")

_ROOT_DOC_NAMES = ("README.md", "AGENTS.md")
_GENERATED_SEGMENT = "_generated"
# Dated point-in-time audit receipts (see docs/audit/README.md policy).
_RECEIPTS_DIR_PARTS = ("docs", "audit")

# Generic placeholder names and historical records the current tree forces;
# every entry needs a reason comment.
_ALLOWED_REFS = {
    # Illustrative import-convention placeholder in the two-layer comparison
    # table (docs/architecture/two-layer-architecture.md); never a real module.
    "infrastructure.module",
    # Symptom name in the environment-setup troubleshooting playbook
    # (docs/operational/troubleshooting/environment-setup.md) explaining the
    # ModuleNotFoundError for scripts' graceful-fallback stubs.
    "infrastructure.build",
    # Docstring/doctest template placeholder in the module-authoring rules
    # (docs/rules/infrastructure_modules.md); never a real module.
    "infrastructure.example_module",
    # Historical remediation record (docs/guides/new-project-setup.md) that
    # quotes a fixed past defect verbatim: the symbol never existed and the
    # record documents exactly that.
    "infrastructure.core.logging.logging_utils",
    # Historical remediation record (docs/maintenance/review-remediation-
    # 2026-07.md) describing a guarded non-existent import that was removed;
    # kept verbatim as point-in-time history.
    "infrastructure.core.config.dotenv",
}

__all__ = [
    "Finding",
    "collect_findings",
    "dotted_ref_resolves",
    "iter_doc_files",
    "scan_repo",
]


@dataclass(frozen=True)
class Finding:
    """One unresolved ``infrastructure.*`` reference in documentation."""

    path: str
    line: int
    ref: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: unresolved infrastructure module reference: {self.ref}"


def iter_doc_files(repo_root: Path) -> list[Path]:
    """Deterministically list the documentation files in the gate's scope."""
    files: list[Path] = []
    for name in _ROOT_DOC_NAMES:
        candidate = repo_root / name
        if candidate.is_file():
            files.append(candidate)
    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        for path in sorted(docs_dir.rglob("*.md")):
            relative_parts = path.relative_to(repo_root).parts
            if _GENERATED_SEGMENT in relative_parts:
                continue
            if tuple(relative_parts[:2]) == _RECEIPTS_DIR_PARTS:
                continue
            files.append(path)
    return files


def _defines_symbol(text: str, name: str) -> bool:
    """True when ``name`` is defined or imported in a Python source text."""
    return bool(
        re.search(
            rf"(?m)^\s*(?:def\s+{name}\b|class\s+{name}\b|{name}\s*[:=]"
            rf"|from\s+[\w.]+\s+import\s+[^\n]*\b{name}\b"
            rf"|import\s+[^\n]*\b{name}\b|\b{name},?\s*$)",
            text,
        )
    )


def _package_defines_symbol(package: Path, name: str) -> bool:
    """True when any module under ``package`` defines or imports ``name``."""
    return any(
        _defines_symbol(path.read_text(encoding="utf-8"), name)
        for path in sorted(package.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def dotted_ref_resolves(repo_root: Path, dotted: str) -> bool:
    """True when a documented ``infrastructure.*`` dotted path resolves on disk.

    Walks the dotted segments from ``infrastructure/``:

    - A segment that is a module file (``<name>.py``) resolves the module;
      any remaining attribute tail resolves when its final attribute is
      defined or imported in that file
      (``infrastructure.project.discovery.discover_projects``).
    - A segment that is a package (``<name>/__init__.py``) advances the walk;
      consuming the whole path inside packages resolves
      (``infrastructure.skills``), and a trailing attribute resolves when it
      is defined or imported in one of the package's modules
      (``infrastructure.core.logging.get_logger``).
    - A non-final segment that is neither a module file nor a package is a
      finding, as is a final segment that is neither a module nor a defined
      symbol (``infrastructure.publishing.nonexistent_module``).
    """
    parts = dotted.split(".")
    current = repo_root / parts[0]
    for index, part in enumerate(parts[1:], start=1):
        module_file = current / f"{part}.py"
        if module_file.is_file():
            remaining = parts[index + 1 :]
            return not remaining or _defines_symbol(module_file.read_text(encoding="utf-8"), remaining[-1])
        package = current / part
        if (package / "__init__.py").is_file():
            current = package
            continue
        return index == len(parts) - 1 and _package_defines_symbol(current, part)
    return True


def collect_findings(repo_root: Path, documents: list[tuple[str, str]]) -> list[Finding]:
    """Findings for documents given as ``(display_path, text)`` pairs.

    Splitting traversal from matching keeps the finder testable against a
    caller-provided document list (real files, no mocks).
    """
    findings: list[Finding] = []
    for display_path, text in documents:
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _NOQA_RE.search(line):
                continue
            for match in _MODULE_REF_RE.finditer(line):
                ref = match.group(0)
                if ref.endswith(".py"):
                    ref = ref[:-3]
                if ref in _ALLOWED_REFS:
                    continue
                if not dotted_ref_resolves(repo_root, ref):
                    findings.append(Finding(path=display_path, line=lineno, ref=ref))
    findings.sort(key=lambda f: (f.path, f.line, f.ref))
    return findings


def scan_repo(repo_root: Path) -> list[Finding]:
    """Scan the gate's documentation scope and return sorted findings."""
    documents = [
        (str(path.relative_to(repo_root)), path.read_text(encoding="utf-8")) for path in iter_doc_files(repo_root)
    ]
    return collect_findings(repo_root, documents)
