"""Tests for ``infrastructure.validation.docs.module_coverage``.

Real filesystem fixtures — no mocks. The final test asserts the live repo keeps
every public module referenced in its package docs (the regression gate).
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.module_coverage import (
    find_module_doc_gaps,
    is_public_module,
    iter_public_modules,
    module_is_referenced,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _make_pkg(root: Path, rel: str, *, modules: list[str], agents_text: str, readme: str = "stub") -> Path:
    pkg = root / rel
    pkg.mkdir(parents=True, exist_ok=True)
    for name in modules:
        (pkg / name).write_text("def f():\n    return 1\n", encoding="utf-8")
    (pkg / "AGENTS.md").write_text(agents_text, encoding="utf-8")
    (pkg / "README.md").write_text(readme, encoding="utf-8")
    return pkg


def test_is_public_module_classification() -> None:
    assert is_public_module("analysis.py")
    assert not is_public_module("_helper.py")
    assert not is_public_module("__init__.py")
    assert not is_public_module("__main__.py")
    assert not is_public_module("test_analysis.py")
    assert not is_public_module("README.md")


def test_iter_public_modules_sorted_and_filtered(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    for name in ("b.py", "a.py", "_priv.py", "__init__.py", "test_a.py"):
        (pkg / name).write_text("", encoding="utf-8")
    assert iter_public_modules(pkg) == ["a.py", "b.py"]


def test_module_is_referenced_is_word_bounded() -> None:
    docs = "the `control.py` module and the snapshot subsystem"
    assert module_is_referenced("control", docs)
    assert module_is_referenced("snapshot", docs)
    # a longer word that merely CONTAINS the stem must NOT count as documented
    assert not module_is_referenced("control", "the controller class")
    assert not module_is_referenced("snap", docs)


def test_documented_module_produces_no_gap(tmp_path: Path) -> None:
    _make_pkg(
        tmp_path,
        "infrastructure/demo",
        modules=["engine.py"],
        agents_text="# Demo\n\n**engine.py** — the core engine.\n",
    )
    gaps = find_module_doc_gaps(tmp_path, roots=("infrastructure",))
    assert gaps == []


def test_undocumented_public_module_is_flagged(tmp_path: Path) -> None:
    _make_pkg(
        tmp_path,
        "infrastructure/demo",
        modules=["engine.py", "widget.py"],
        agents_text="# Demo\n\n**engine.py** — the core engine.\n",
    )
    gaps = find_module_doc_gaps(tmp_path, roots=("infrastructure",))
    assert len(gaps) == 1
    assert gaps[0].undocumented == ("widget.py",)
    assert gaps[0].total == 2
    assert gaps[0].documented == 1
    assert "widget.py" in gaps[0].format()


def test_private_dunder_and_test_modules_are_not_required(tmp_path: Path) -> None:
    pkg = _make_pkg(
        tmp_path,
        "infrastructure/demo",
        modules=["engine.py"],
        agents_text="# Demo\n\n**engine.py** — the core engine.\n",
    )
    # These exist but are never required to be documented.
    for name in ("_internal.py", "__main__.py", "__init__.py", "test_engine.py"):
        (pkg / name).write_text("", encoding="utf-8")
    assert find_module_doc_gaps(tmp_path, roots=("infrastructure",)) == []


def test_reference_in_readme_counts_as_documented(tmp_path: Path) -> None:
    _make_pkg(
        tmp_path,
        "infrastructure/demo",
        modules=["engine.py"],
        agents_text="# Demo\n\nNo module list here.\n",
        readme="The `engine.py` module powers the demo.",
    )
    assert find_module_doc_gaps(tmp_path, roots=("infrastructure",)) == []


def test_directory_without_agents_md_is_skipped(tmp_path: Path) -> None:
    pkg = tmp_path / "infrastructure" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "engine.py").write_text("", encoding="utf-8")
    (pkg / "README.md").write_text("stub", encoding="utf-8")
    # No AGENTS.md → this gate does not apply (doc-pair linter owns that).
    assert find_module_doc_gaps(tmp_path, roots=("infrastructure",)) == []


def test_live_repo_has_full_public_module_doc_coverage() -> None:
    """Regression gate: every public infra/scripts module is referenced in its docs."""
    gaps = find_module_doc_gaps(REPO_ROOT)
    assert gaps == [], "Undocumented public modules:\n" + "\n".join(g.format() for g in gaps)
