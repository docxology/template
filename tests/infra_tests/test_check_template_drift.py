"""Tests for `scripts/check_template_drift.py`.

The drift checker is the audit-as-gate that converts the May 2026
template-hardening audit findings into a recurring CI check. A gate
that has never failed is not a gate; this file is the proof that each
detector actually catches the class of bug it was built for.

Every test follows the same shape:

    1. Create a tiny synthetic project layout under `tmp_path` that
       reproduces the bug class.
    2. Run the detector against that layout.
    3. Assert the detector raised an ERROR or WARNING of the expected
       rule name.

All inputs are real files written to `tmp_path` — no mocks.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def drift_module():
    """Load `scripts/check_template_drift.py` as a module so we can call
    individual detector functions against synthetic project trees.
    """
    spec = importlib.util.spec_from_file_location(
        "check_template_drift", REPO_ROOT / "scripts" / "check_template_drift.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_template_drift"] = mod
    spec.loader.exec_module(mod)
    return mod


def _scaffold_minimal_project(tmp_path: Path, name: str = "fake_project") -> Path:
    """Write the minimum file set every detector expects to find."""
    root = tmp_path / "projects" / name
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "docs").mkdir()
    (root / "manuscript").mkdir()

    (root / "README.md").write_text("# Fake\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# Fake AGENTS\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.coverage.report]\nfail_under = 90\n", encoding="utf-8")
    (root / ".gitignore").write_text("output/\n", encoding="utf-8")
    (root / "src" / "__init__.py").write_text('"""Pkg."""\n\n__all__ = ["a", "b"]\n', encoding="utf-8")
    (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (root / "tests" / "conftest.py").write_text("", encoding="utf-8")
    (root / "manuscript" / "config.yaml").write_text("{}\n", encoding="utf-8")
    (root / "manuscript" / "references.bib").write_text("", encoding="utf-8")
    (root / "manuscript" / "preamble.md").write_text("", encoding="utf-8")
    (root / "docs" / "AGENTS.md").write_text("# Docs\n", encoding="utf-8")
    return root


def test_function_name_drift_catches_invented_check(drift_module, tmp_path):
    """A `_check_invented` reference in docs/* but absent from src/pipeline.py
    must raise an ERROR."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "pipeline.py").write_text("def _check_real(report): return None\n", encoding="utf-8")
    (root / "docs" / "rules.md").write_text("The check is `_check_invented` in `src/pipeline.py`.", encoding="utf-8")
    rep = drift_module.Report()
    # Temporarily redirect the detector at our synthetic root.
    drift_module.check_function_name_drift(root, rep, "fake_project")
    errors = rep.errors()
    assert any("function_name_drift" == e.rule for e in errors), [(e.severity, e.rule, e.message) for e in rep.findings]
    assert any("_check_invented" in e.message for e in errors)


def test_function_name_drift_clean_when_names_match(drift_module, tmp_path):
    """Docs referencing real `_check_*` names must produce no findings."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "pipeline.py").write_text("def _check_real(report): return None\n", encoding="utf-8")
    (root / "docs" / "rules.md").write_text("The check is `_check_real` in `src/pipeline.py`.", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_function_name_drift(root, rep, "fake_project")
    assert rep.findings == []


def test_test_class_drift_catches_invented_class(drift_module, tmp_path):
    """A `TestInvented` referenced in docs/* but absent from tests/* must raise."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "tests" / "test_pipeline.py").write_text("class TestReal:\n    def test_a(self): pass\n", encoding="utf-8")
    (root / "docs" / "patterns.md").write_text("The class `TestInvented` covers the unit cases.", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_test_class_drift(root, rep, "fake_project")
    errors = rep.errors()
    assert any(e.rule == "test_class_drift" for e in errors)
    assert any("TestInvented" in e.message for e in errors)


def test_test_class_drift_clean_when_class_real(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "tests" / "test_pipeline.py").write_text("class TestReal:\n    def test_a(self): pass\n", encoding="utf-8")
    (root / "docs" / "patterns.md").write_text("The class `TestReal` covers it.", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_test_class_drift(root, rep, "fake_project")
    assert rep.findings == []


def test_coverage_floor_drift_catches_doc_mismatch(drift_module, tmp_path):
    """pyproject.toml fail_under = 90, doc says fail_under = 70 → ERROR."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "philosophy.md").write_text("The local floor is `fail_under = 70`.", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_coverage_floor_consistency(root, rep, "fake_project")
    errors = rep.errors()
    assert any(e.rule == "coverage_floor_drift" for e in errors)


def test_coverage_floor_drift_clean_when_matching(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "philosophy.md").write_text("The local floor is `fail_under = 90`.", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_coverage_floor_consistency(root, rep, "fake_project")
    assert rep.findings == []


def test_all_export_drift_catches_invented_entry(drift_module, tmp_path):
    """STYLE.md claims an __all__ entry that src/__init__.py does not export → ERROR."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "__init__.py").write_text('"""Pkg."""\n\n__all__ = ["real_name"]\n', encoding="utf-8")
    (root / "src" / "STYLE.md").write_text('__all__ = [\n    "real_name",\n    "invented_name",\n]\n', encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_all_export_drift(root, rep, "fake_project")
    errors = rep.errors()
    assert any(e.rule == "__all___doc_drift" for e in errors)
    assert any("invented_name" in e.message for e in errors)


def test_all_export_drift_clean_when_matching(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "__init__.py").write_text('"""Pkg."""\n\n__all__ = ["real_name"]\n', encoding="utf-8")
    (root / "src" / "STYLE.md").write_text('__all__ = ["real_name"]\n', encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_all_export_drift(root, rep, "fake_project")
    assert rep.findings == []


def test_dead_link_catches_missing_target(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "links.md").write_text("See [the missing](nonexistent.md) for details.", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_referenced_files_exist(root, rep, "fake_project")
    assert any(f.rule == "dead_link" for f in rep.findings)


def test_dead_link_skips_example_filenames(drift_module, tmp_path):
    """Illustrative `[link](new_*.png)` patterns inside docs are intentional examples."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "links.md").write_text(
        "Example: `[Figure caption.](../output/figures/new_figure.png)`",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_referenced_files_exist(root, rep, "fake_project")
    # `new_figure.png` is an example filename — must not be flagged.
    assert not any("new_figure" in f.message for f in rep.findings)


def test_dead_link_skips_fenced_code(drift_module, tmp_path):
    """Markdown links inside ``` fences are illustrative."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "links.md").write_text("```markdown\n[caption](missing_in_a_fence.png)\n```\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_referenced_files_exist(root, rep, "fake_project")
    assert rep.findings == []


def test_oversize_src_file_flags_large_python(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    big = root / "src" / "huge.py"
    big.write_text("# line\n" * 1600, encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_no_oversize_src_files(root, rep, "fake_project")
    assert any(f.rule == "oversize_src_file" and "huge.py" in f.message for f in rep.findings)


def test_oversize_src_file_silent_under_threshold(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    small = root / "src" / "small.py"
    small.write_text("x = 1\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_no_oversize_src_files(root, rep, "fake_project")
    assert rep.findings == []


def test_blanket_except_error_when_no_noqa(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "bad.py").write_text(
        "def f():\n    try:\n        pass\n    except Exception:\n        return None\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_no_blanket_except_in_src(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "blanket_except" for f in rep.findings)


def test_blanket_except_warning_when_noqa_present(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "ok.py").write_text(
        "def f():\n    try:\n        pass\n    except Exception:  # noqa: BLE001\n        return None\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_no_blanket_except_in_src(root, rep, "fake_project")
    assert any(f.severity == "WARNING" and f.rule == "blanket_except_with_noqa" for f in rep.findings)


def test_blanket_except_suppressed_for_safety_net(drift_module, tmp_path):
    """An annotated TOP-LEVEL MAIN SAFETY NET except Exception is intentional.

    Matches the production pattern in analysis.py: the suppression marker is
    in the inline comment of the `except` line itself (within the 200-char
    forward window the detector reads).
    """
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "main_handler.py").write_text(
        "def main():\n"
        "    try:\n"
        "        run()\n"
        "    except Exception as e:  # noqa: BLE001 — TOP-LEVEL MAIN SAFETY NET\n"
        "        raise\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_no_blanket_except_in_src(root, rep, "fake_project")
    assert rep.findings == []


def test_mocks_absent_from_tests_catches_unittest_mock(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    mock_import = "from unittest." + "mock import " + "Magic" + "M" + "ock"
    mock_ctor = "    m = " + "Magic" + "M" + "ock" + "()\n"
    (root / "tests" / "test_naughty.py").write_text(
        f"{mock_import}\n\ndef test_bad():\n{mock_ctor}",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_mocks_absent_from_tests(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "mock_in_tests" for f in rep.findings)


def test_required_files_exist_clean_for_full_scaffold(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert rep.findings == []


def test_required_files_exist_flags_missing_pyproject(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "pyproject.toml").unlink()
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "missing_canonical_file" for f in rep.findings)


def test_end_to_end_run_on_live_exemplars_is_clean(drift_module):
    """Final smoke: the actual checked-in exemplars must be clean.

    If this test fails on `main`, someone landed drift that bypassed the
    pre-commit hook. The fix is in the source, not in this test.
    """
    rep = drift_module.Report()
    for proj in drift_module.PROJECT_NAMES:
        drift_module.check_project(proj, rep)
    assert rep.errors() == [], [(f.project, f.rule, f.message) for f in rep.errors()]
