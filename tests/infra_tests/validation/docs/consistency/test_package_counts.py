"""Tests for module-count and canonical-count consistency checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import (
    Inconsistency,
    check_canonical_count_singularity,
    check_module_count_claims,
)

from .conftest import scaffold_repo, write_doc


def test_module_count_claim_matches_reality(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "Layer 1 has 15 Python packages.\n")
    assert check_module_count_claims(repo) == []


def test_module_count_claim_mismatch_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "There are 17 Python subpackages here.\n")
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert isinstance(issues[0], Inconsistency)
    assert issues[0].category == "module-count"
    assert "17" in issues[0].detail
    assert "15" in issues[0].detail


def test_module_count_importable_packages_mismatch_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "Docs list **17** importable packages.\n")
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert issues[0].category == "module-count"


def test_module_count_infrastructure_subpackages_mismatch_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "Core systems: 17 `infrastructure/` Python subpackages.\n")
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert issues[0].category == "module-count"


def test_module_count_documented_infrastructure_areas_mismatch_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "Modules guide covers **17** documented infrastructure areas.\n")
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert issues[0].category == "module-count"


def test_historical_plain_infrastructure_packages_note_is_not_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "CHANGELOG.md", "Historical release note: all 8 infrastructure packages passed mypy.\n")
    assert check_module_count_claims(repo) == []


def test_module_count_singular_is_not_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "guide.md", "Each Layer-1 Python package ships AGENTS.md.\n")
    assert check_module_count_claims(repo) == []


def test_module_count_inside_fenced_code_is_ignored(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        """Real claim: 15 Python packages.

```text
Old claim: 99 Python packages
```
""",
    )
    assert check_module_count_claims(repo) == []


def test_module_count_noqa_suppresses_warning(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "guide.md",
        "Historical: 99 Python packages. <!-- noqa: docs-lint -->\n",
    )
    assert check_module_count_claims(repo) == []


def test_quoted_correction_record_is_not_flagged(tmp_path: Path) -> None:
    """A changelog ``"old" -> "new"`` edit record is history, not a live claim."""
    repo = scaffold_repo(tmp_path, n_packages=25)
    write_doc(
        repo / "CHANGELOG.md",
        'docs table; fixed stale "19 Python packages" -> "25" in two mermaid diagrams;\n',
    )
    assert check_module_count_claims(repo) == []


def test_correction_record_exempts_both_operands(tmp_path: Path) -> None:
    """Neither side of a recorded correction is measured against today's count."""
    repo = scaffold_repo(tmp_path, n_packages=30)
    write_doc(repo / "CHANGELOG.md", 'fixed "19 Python packages" -> "25" in the diagram;\n')
    assert check_module_count_claims(repo) == []


def test_correction_record_requires_quotes(tmp_path: Path) -> None:
    """An unquoted arrow is not an edit record and stays subject to the gate."""
    repo = scaffold_repo(tmp_path, n_packages=25)
    write_doc(repo / "CHANGELOG.md", "Layer 1 grew: 19 Python packages -> 25 today.\n")
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert issues[0].category == "module-count"


def test_correction_record_does_not_launder_other_claims_on_same_line(tmp_path: Path) -> None:
    """A live wrong claim beside a correction record is still flagged."""
    repo = scaffold_repo(tmp_path, n_packages=25)
    write_doc(
        repo / "docs" / "guide.md",
        'Note "19 Python packages" -> "25" was fixed.\n\nToday there are 17 Python subpackages.\n',
    )
    issues = check_module_count_claims(repo)
    assert len(issues) == 1
    assert "17" in issues[0].detail


def test_count_singularity_outside_canonical_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "g.md", "The repo has 345 .py files in infrastructure.\n")
    issues = check_canonical_count_singularity(repo)
    assert len(issues) == 1
    assert issues[0].category == "count-singularity"


def test_count_singularity_COUNTS_is_exempt(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(repo / "docs" / "_generated" / "COUNTS.md", "Measured: 345 .py files.\n")
    assert check_canonical_count_singularity(repo) == []


def test_count_singularity_noqa_suppresses(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=15)
    write_doc(
        repo / "docs" / "g.md",
        "Historical note: 345 Python files (2026-05-15). <!-- noqa: docs-lint -->\n",
    )
    assert check_canonical_count_singularity(repo) == []


def test_canonical_exemplar_markdown_is_in_scope(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=17)
    write_doc(
        repo / "projects" / "templates" / "template_code_project" / "manuscript" / "01_intro.md",
        "The infrastructure layer has 15 Python subpackages.\n",
    )
    issues = check_module_count_claims(repo)
    assert any(
        "projects/templates/template_code_project/manuscript/01_intro.md" in str(i.file)
        and i.category == "module-count"
        for i in issues
    )


def test_inconsistency_format_contains_file_and_line() -> None:
    inc = Inconsistency(file=Path("/a/b.md"), line=7, category="module-count", detail="x")
    s = inc.format()
    assert "/a/b.md:7" in s
    assert "[module-count]" in s
    assert "x" in s
