"""Tests for `scripts/audit/check_doc_module_refs.py`.

The gate resolves every ``infrastructure.*`` dotted path referenced in
docs/, README.md, and AGENTS.md to a real module so a module split cannot
silently stale documentation references. A gate that has never failed is
not a gate; the negative control below proves a doc snippet referencing a
nonexistent module produces a finding.

All inputs are real files written to `tmp_path` — no mocks.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from infrastructure.documentation import doc_module_refs

REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = REPO_ROOT / "scripts" / "audit" / "check_doc_module_refs.py"

_SPEC = importlib.util.spec_from_file_location("check_doc_module_refs", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
check_doc_module_refs = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = check_doc_module_refs
_SPEC.loader.exec_module(check_doc_module_refs)


def _make_repo(tmp_path: Path) -> Path:
    """Write a minimal repo: infrastructure/publishing package + docs/."""
    root = tmp_path / "repo"
    (root / "infrastructure" / "publishing").mkdir(parents=True)
    (root / "infrastructure" / "publishing" / "__init__.py").write_text("")
    (root / "docs").mkdir()
    return root


def _scan(root: Path):
    return doc_module_refs.scan_repo(root)


def test_nonexistent_module_reference_is_a_finding(tmp_path):
    """Negative control: infrastructure.publishing.nonexistent_module must fail."""
    root = _make_repo(tmp_path)
    doc = root / "docs" / "guide.md"
    doc.write_text("Run `uv run python -m infrastructure.publishing.nonexistent_module` to publish.\n")
    findings = _scan(root)
    assert findings == [
        doc_module_refs.Finding(
            path="docs/guide.md",
            line=1,
            ref="infrastructure.publishing.nonexistent_module",
        )
    ]


def test_real_module_reference_resolves(tmp_path):
    root = _make_repo(tmp_path)
    (root / "docs" / "guide.md").write_text("Run `uv run python -m infrastructure.publishing zenodo` to publish.\n")
    assert _scan(root) == []


def test_attribute_and_subcommand_tails_resolve_through_module_prefix(tmp_path):
    """`module.attr` and `module sub-command` references resolve; flags never match."""
    root = _make_repo(tmp_path)
    (root / "infrastructure" / "publishing" / "public_scope.py").write_text(
        "PUBLIC_PROJECT_NAMES = ['template_code_project']\n"
    )
    (root / "docs" / "guide.md").write_text(
        "Use `infrastructure.publishing.public_scope lint-paths` for scope.\n"
        "The export lives in `infrastructure.publishing.public_scope.PUBLIC_PROJECT_NAMES`.\n"
        "Coverage flag: `--cov=infrastructure` is not a module reference.\n"
    )
    assert _scan(root) == []


def test_dated_audit_receipts_directory_is_skipped(tmp_path):
    root = _make_repo(tmp_path)
    receipts = root / "docs" / "audit" / "RECEIPT_2026-01-01.md"
    receipts.parent.mkdir(parents=True)
    receipts.write_text("Historical: infrastructure.publishing.nonexistent_module.\n")
    assert _scan(root) == []


def test_missing_first_segment_is_a_finding_even_with_longer_path(tmp_path):
    """A ref whose first segment does not exist cannot be rescued by deeper segments."""
    root = _make_repo(tmp_path)
    (root / "docs" / "guide.md").write_text("See `infrastructure.publishing.deep.missing_thing` for details.\n")
    findings = _scan(root)
    assert [f.ref for f in findings] == ["infrastructure.publishing.deep.missing_thing"]


def test_noqa_docs_lint_line_is_suppressed(tmp_path):
    root = _make_repo(tmp_path)
    (root / "docs" / "guide.md").write_text(
        "from infrastructure.publishing.nonexistent_module import x  # noqa: docs-lint\n"
    )
    assert _scan(root) == []


def test_generated_docs_directory_is_skipped(tmp_path):
    root = _make_repo(tmp_path)
    generated = root / "docs" / "_generated" / "roster.md"
    generated.parent.mkdir(parents=True)
    generated.write_text("Auto-written from infrastructure.publishing.nonexistent_module.\n")
    assert _scan(root) == []


def test_root_readme_and_agents_are_scanned(tmp_path):
    root = _make_repo(tmp_path)
    (root / "README.md").write_text("Entry: `infrastructure.publishing.nonexistent_module`.\n")
    (root / "AGENTS.md").write_text("Entry: `infrastructure.publishing.missing_cli`.\n")
    findings = _scan(root)
    assert [(f.path, f.ref) for f in findings] == [
        ("AGENTS.md", "infrastructure.publishing.missing_cli"),
        ("README.md", "infrastructure.publishing.nonexistent_module"),
    ]


def test_findings_are_sorted_deterministically(tmp_path):
    root = _make_repo(tmp_path)
    (root / "docs" / "b.md").write_text("`infrastructure.publishing.zzz`\n`infrastructure.publishing.aaa`\n")
    (root / "docs" / "a.md").write_text("`infrastructure.publishing.mmm`\n")
    findings = _scan(root)
    assert [(f.path, f.line, f.ref) for f in findings] == [
        ("docs/a.md", 1, "infrastructure.publishing.mmm"),
        ("docs/b.md", 1, "infrastructure.publishing.zzz"),
        ("docs/b.md", 2, "infrastructure.publishing.aaa"),
    ]


def test_dotted_ref_resolves_distinguishes_file_and_package():
    assert doc_module_refs.dotted_ref_resolves(REPO_ROOT, "infrastructure.mcp_server")
    assert doc_module_refs.dotted_ref_resolves(REPO_ROOT, "infrastructure.skills")
    assert not doc_module_refs.dotted_ref_resolves(REPO_ROOT, "infrastructure.definitely_not_a_module")


def test_attribute_tail_resolves_when_symbol_is_defined_in_module(tmp_path):
    """`package.symbol` resolves when the symbol is defined in the package."""
    root = _make_repo(tmp_path)
    (root / "infrastructure" / "publishing" / "core.py").write_text("def publish(manuscript):\n    return manuscript\n")
    (root / "docs" / "guide.md").write_text("Call `infrastructure.publishing.publish(manuscript)` to publish.\n")
    assert _scan(root) == []


def test_attribute_tail_is_a_finding_when_symbol_is_undefined(tmp_path):
    root = _make_repo(tmp_path)
    (root / "docs" / "guide.md").write_text("Call `infrastructure.publishing.publish(manuscript)` to publish.\n")
    findings = _scan(root)
    assert [f.ref for f in findings] == ["infrastructure.publishing.publish"]


def test_main_exit_codes(tmp_path, capsys):
    root = _make_repo(tmp_path)
    (root / "docs" / "guide.md").write_text("`infrastructure.publishing.nonexistent_module`\n")
    argv = ["--repo-root", str(root)]
    assert check_doc_module_refs.main(argv) == 1
    assert "infrastructure.publishing.nonexistent_module" in capsys.readouterr().out
    (root / "docs" / "guide.md").write_text("`infrastructure.publishing`\n")
    assert check_doc_module_refs.main(argv) == 0
    capsys.readouterr()
