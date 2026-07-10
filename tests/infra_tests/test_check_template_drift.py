"""Tests for `scripts/audit/check_template_drift.py`.

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

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests._support.projects import make_project, write_doc

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def drift_module():
    """Import drift detectors from infrastructure.project.drift."""
    import infrastructure.project.drift.checks as checks
    from infrastructure.project.drift import DEFAULT_PROJECT_NAMES
    from infrastructure.project.drift.models import Report as DriftReport

    return SimpleNamespace(
        Report=DriftReport,
        PROJECT_NAMES=DEFAULT_PROJECT_NAMES,
        check_function_name_drift=checks.check_function_name_drift,
        check_test_class_drift=checks.check_test_class_drift,
        check_coverage_floor_consistency=checks.check_coverage_floor_consistency,
        check_all_export_drift=checks.check_all_export_drift,
        check_referenced_files_exist=checks.check_referenced_files_exist,
        check_no_oversize_src_files=checks.check_no_oversize_src_files,
        check_no_blanket_except_in_src=checks.check_no_blanket_except_in_src,
        check_mocks_absent_from_tests=checks.check_mocks_absent_from_tests,
        check_required_files_exist=checks.check_required_files_exist,
        check_template_signpost_contract=checks.check_template_signpost_contract,
        check_config_example_parity=checks.check_config_example_parity,
        check_publication_metadata_consistency=checks.check_publication_metadata_consistency,
        check_metadata_export_current=checks.check_metadata_export_current,
        check_publishing_status_block_current=checks.check_publishing_status_block_current,
        check_docs_hardcoded_counts=checks.check_docs_hardcoded_counts,
        check_project_src_infrastructure_boundary=checks.check_project_src_infrastructure_boundary,
        check_forkability_contract=checks.check_forkability_contract,
        check_shared_template_design_contract=checks.check_shared_template_design_contract,
        check_project=lambda project, report: checks.check_project(REPO_ROOT, project, report),
    )


def _scaffold_minimal_project(tmp_path: Path, name: str = "fake_project") -> Path:
    """Write the minimum file set every detector expects to find."""
    root = make_project(tmp_path, name, with_manuscript=True)
    (root / "docs").mkdir()
    (root / "scripts").mkdir()
    write_doc(
        root / "README.md",
        """# Fake

## Run via the template monorepo

Use `uv run python scripts/pipeline/stage_02_analysis.py --project templates/fake_project`.

## When to use this template

Use it for a fake forkable exemplar.

## Configuration

Edit `manuscript/config.yaml`; copy from `manuscript/config.yaml.example`.

## Tests

Run `uv run pytest projects/templates/fake_project/tests --cov=projects/templates/fake_project/src --cov-fail-under=90`.

## Outputs and validation

Run analysis, render, validate, and copy stages; review `output/templates/fake_project`.

## Publication and boundaries

Publication metadata and claim boundaries stay conservative.

## Fork guidance

Forks must replace placeholder config values and keep template integrity checks green.
""",
    )
    write_doc(
        root / "AGENTS.md",
        """# Fake AGENTS

## Ground Truth

Configuration lives in `manuscript/config.yaml`; outputs are regenerated, not edited.

## Commands

Run the monorepo pipeline with `uv run python scripts/pipeline/stage_02_analysis.py --project templates/fake_project`.

## Contracts

Keep tests, publication boundaries, and fork TODO evidence aligned.
""",
    )
    write_doc(
        root / "TODO.md",
        """# Fake TODO

## Current validation evidence

- Drift gate and tests are the current evidence.

## Integrity and template-status gaps

- Keep template integrity explicit.

## Configurable-surface gaps

- Keep config examples placeholder-safe.

## Documentation and signposting gaps

- Keep README and AGENTS aligned.

## Test and validator gaps

- Add negative controls for new validators.

## Ordered improvement ladder

1. Keep the gate green.
""",
    )
    write_doc(root / "pyproject.toml", "[tool.coverage.report]\nfail_under = 90\n")
    write_doc(root / ".gitignore", "output/\n")
    write_doc(root / "src" / "__init__.py", '"""Pkg."""\n\n__all__ = ["a", "b"]\n')
    write_doc(root / "tests" / "conftest.py", "")
    write_doc(root / "manuscript" / "config.yaml", "paper: {}\npublication: {}\n")
    write_doc(root / "manuscript" / "config.yaml.example", "paper: {}\npublication: {}\n")
    write_doc(root / "manuscript" / "references.bib", "")
    write_doc(root / "manuscript" / "preamble.md", "")
    write_doc(root / "docs" / "AGENTS.md", "# Docs\n")
    write_doc(root / "STANDALONE.md", "# Standalone\n")
    write_doc(
        root / "domain_profile.yaml",
        """
domain: fake_research
display_name: Fake Research
review_gates: [source_quality]
artifact_expectations: [output/report.json]
benchmark_rubric:
  name: fake
  dimensions:
    - name: reproducibility
      weight: 1.0
""",
    )
    write_doc(
        root / "experiment_plan.yaml",
        """
conditions:
  - name: reference_fixture
    role: reference
  - name: proposed_fixture
    role: proposed
  - name: sensitivity_fixture
    role: variant
metrics:
  primary:
    name: accuracy
    direction: maximize
protocol: "Run all fixtures with the same seed."
baselines: [reference_fixture]
ablations: [sensitivity_fixture]
""",
    )
    return root


def test_function_name_drift_catches_invented_check(drift_module, tmp_path):
    """A `_check_invented` reference in docs/* but absent from pipeline checks
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


def test_function_name_drift_supports_pipeline_package(drift_module, tmp_path):
    """The detector must handle src/pipeline/checks.py packages."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "src" / "pipeline").mkdir()
    (root / "src" / "pipeline" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pipeline" / "checks.py").write_text("def _check_real(report): return None\n", encoding="utf-8")
    (root / "docs" / "rules.md").write_text(
        "The check is `_check_missing` in `src/pipeline/checks.py`.",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_function_name_drift(root, rep, "fake_project")
    errors = rep.errors()
    assert any("function_name_drift" == e.rule for e in errors), [(e.severity, e.rule, e.message) for e in rep.findings]
    assert any("src/pipeline/checks.py" in e.message for e in errors)


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


def test_shared_template_design_contract_requires_sections(drift_module, tmp_path):
    design = tmp_path / "projects" / "templates" / "DESIGN.md"
    design.parent.mkdir(parents=True)
    design.write_text("# Design\n\n## 1. Atmosphere & Identity\n", encoding="utf-8")
    (design.parent / "AGENTS.md").write_text("See `DESIGN.md` for browser-QA expectations.\n", encoding="utf-8")

    rep = drift_module.Report()
    drift_module.check_shared_template_design_contract(tmp_path, rep)

    errors = rep.errors()
    assert any(e.rule == "shared_template_design_section_missing" for e in errors)
    assert any("## 2. Color" in e.message for e in errors)


def test_shared_template_design_contract_requires_agents_signpost(drift_module, tmp_path):
    design = tmp_path / "projects" / "templates" / "DESIGN.md"
    design.parent.mkdir(parents=True)
    design.write_text(
        "\n".join(
            [
                "# Design",
                "## 1. Atmosphere & Identity",
                "## 2. Color",
                "## 3. Typography",
                "## 4. Spacing & Layout",
                "## 5. Components",
                "## 6. Motion & Interaction",
                "## 7. Depth & Surface",
                "## Browser QA Expectations",
                "## Template-Specific Boundaries",
            ]
        ),
        encoding="utf-8",
    )
    (design.parent / "AGENTS.md").write_text("No design link here.\n", encoding="utf-8")

    rep = drift_module.Report()
    drift_module.check_shared_template_design_contract(tmp_path, rep)

    assert any(e.rule == "shared_template_design_signpost_missing" for e in rep.errors())


def test_shared_template_design_contract_accepts_complete_shared_doc(drift_module, tmp_path):
    design = tmp_path / "projects" / "templates" / "DESIGN.md"
    design.parent.mkdir(parents=True)
    design.write_text(
        "\n".join(
            [
                "# Design",
                "## 1. Atmosphere & Identity",
                "## 2. Color",
                "## 3. Typography",
                "## 4. Spacing & Layout",
                "## 5. Components",
                "## 6. Motion & Interaction",
                "## 7. Depth & Surface",
                "## Browser QA Expectations",
                "## Template-Specific Boundaries",
            ]
        ),
        encoding="utf-8",
    )
    (design.parent / "AGENTS.md").write_text("See `DESIGN.md` for browser-QA expectations.\n", encoding="utf-8")

    rep = drift_module.Report()
    drift_module.check_shared_template_design_contract(tmp_path, rep)

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


def test_dead_link_skips_output_targets(drift_module, tmp_path):
    """Manuscript figure embeds into ``output/`` are disposable/regenerated.

    Regression: on a fresh checkout (CI strict drift gate) the gitignored
    project-local ``output/figures/*.png`` do not exist yet, so a real manuscript
    embed like ``![cap](../output/figures/free_energy_curve.png)`` must NOT be
    reported as a dead link — the docstring contract excludes ``output/`` and the
    figures are validated at render time, not by this stale-link gate.
    """
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript").mkdir(exist_ok=True)
    (root / "manuscript" / "11_results.md").write_text(
        "![A real generated figure.](../output/figures/free_energy_curve.png){#fig:fe}\n"
        "Also a nested one: [data](../output/data/results.json).\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_referenced_files_exist(root, rep, "fake_project")
    assert not any(f.rule == "dead_link" for f in rep.findings)


def test_dead_link_still_catches_non_output_missing_target(drift_module, tmp_path):
    """The output exclusion must not mask genuinely-dead non-output links."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript").mkdir(exist_ok=True)
    (root / "manuscript" / "12_results.md").write_text(
        "See [the appendix](./99_appendix_missing.md) and a figure [chart](../assets/not_output.png).\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_referenced_files_exist(root, rep, "fake_project")
    flagged = [f.message for f in rep.findings if f.rule == "dead_link"]
    assert any("99_appendix_missing.md" in m for m in flagged)
    assert any("not_output.png" in m for m in flagged)


def test_dead_link_scans_beyond_docs_dir(drift_module, tmp_path):
    """Broadened scope: stale links in root ``AGENTS.md`` and ``manuscript/`` are
    caught, not only those under ``docs/``.

    Regression for the ``projects/templates/`` move that left 89 broken relative
    links across AGENTS.md / manuscript / src which the docs-only scan missed.
    """
    root = _scaffold_minimal_project(tmp_path)
    (root / "AGENTS.md").write_text("See [guide](../../docs/guides/missing.md).", encoding="utf-8")
    (root / "manuscript" / "01_intro.md").write_text("Ref [syntax](../../docs/missing_syntax.md).", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_referenced_files_exist(root, rep, "fake_project")
    flagged = [f.message for f in rep.findings if f.rule == "dead_link"]
    assert any("AGENTS.md" in m for m in flagged), flagged
    assert any("01_intro.md" in m for m in flagged), flagged


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


def test_oversize_src_file_catches_file_in_subdirectory(drift_module, tmp_path):
    """Oversize check must descend into src/ subdirectories (rglob, not glob)."""
    root = _scaffold_minimal_project(tmp_path)
    subdir = root / "src" / "submodule"
    subdir.mkdir()
    (subdir / "large.py").write_text("# line\n" * 1600, encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_no_oversize_src_files(root, rep, "fake_project")
    assert any(f.rule == "oversize_src_file" and "large.py" in f.message for f in rep.findings), (
        f"Expected oversize_src_file finding for src/submodule/large.py, got: {rep.findings}"
    )


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


def test_required_files_exist_flags_missing_todo(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "TODO.md").unlink()
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "missing_canonical_file" and "TODO.md" in f.message for f in rep.findings
    )


def test_required_files_exist_flags_missing_config_example(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml.example").unlink()
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "missing_canonical_file" and "manuscript/config.yaml.example" in f.message
        for f in rep.findings
    )


def test_required_files_exist_allows_fit_for_purpose_docs(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "AGENTS.md").unlink()
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert rep.findings == []


def test_template_signpost_contract_flags_missing_readme_use_when(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "README.md").write_text("# Fake\n\n## Configuration\n\nUses `config.yaml`.\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_template_signpost_contract(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "missing_template_signpost" and "README.md" in f.message
        for f in rep.findings
    )


def test_template_signpost_contract_flags_missing_todo_ladder(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "TODO.md").write_text("# Fake TODO\n\n## Current validation evidence\n\n- Tests.\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_template_signpost_contract(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "missing_template_signpost" and "TODO.md" in f.message for f in rep.findings
    )


def test_config_example_parity_flags_missing_top_level_section(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text("paper: {}\npublication: {}\noutputs: {}\n", encoding="utf-8")
    (root / "manuscript" / "config.yaml.example").write_text("paper: {}\npublication: {}\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_config_example_parity(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "config_example_missing_section" and "outputs" in f.message
        for f in rep.findings
    )


def test_forkability_contract_flags_missing_standalone_doc(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "STANDALONE.md").unlink()
    rep = drift_module.Report()
    drift_module.check_forkability_contract(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "missing_standalone_doc" for f in rep.findings)


def test_forkability_contract_flags_invalid_overlay(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "experiment_plan.yaml").write_text(
        "conditions:\n  - name: broken\n    role: ablation\nmetrics: {}\nprotocol: ''\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_forkability_contract(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "invalid_experiment_plan" for f in rep.findings)


def test_forkability_contract_flags_unsafe_raw_recursive_copy_docs(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "fork.md").write_text(
        "Fork it with `cp -r projects/templates/template_code_project projects/working/new_project`.\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_forkability_contract(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "unsafe_fork_copy" for f in rep.findings)


def test_forkability_contract_flags_unsafe_raw_recursive_copy_fenced_docs(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "docs" / "fork.md").write_text(
        "```bash\ncp -r projects/templates/template_code_project projects/working/new_project\n```\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_forkability_contract(root, rep, "fake_project")
    assert any(f.severity == "ERROR" and f.rule == "unsafe_fork_copy" for f in rep.findings)


def test_publication_metadata_flags_doi_collision(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  version: '1.0'\npublication:\n"
        "  doi: '10.5281/zenodo.11111'\n"
        "  version_doi: '10.5281/zenodo.11111'\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publication_metadata_consistency(root, rep, "fake_project")
    assert any(f.rule == "publication_split_doi_collision" for f in rep.findings)


def test_publication_metadata_flags_cff_version_drift(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  version: '2.0'\npublication:\n  doi: '10.5281/zenodo.11111'\n",
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text("version: '1.0'\ndoi: 10.5281/zenodo.11111\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_publication_metadata_consistency(root, rep, "fake_project")
    assert any(f.rule == "publication_cff_version_drift" for f in rep.findings)


def test_publication_metadata_flags_missing_concept_xlink(drift_module, tmp_path):
    """A .zenodo.json with a concept DOI but no isVersionOf cross-link is drift."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  version: '1.0.0'\npublication:\n"
        "  doi: '10.5281/zenodo.11111'\n"
        "  version_doi: '10.5281/zenodo.22222'\n"
        "  version_record: 'https://zenodo.org/records/22222'\n",
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text("version: '1.0.0'\ndoi: 10.5281/zenodo.11111\n", encoding="utf-8")
    (root / ".zenodo.json").write_text('{"version": "1.0.0", "title": "X"}\n', encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_publication_metadata_consistency(root, rep, "fake_project")
    assert any(f.rule == "publication_zenodo_missing_concept_xlink" for f in rep.findings)


def test_publication_metadata_accepts_present_concept_xlink(drift_module, tmp_path):
    """A .zenodo.json carrying the isVersionOf concept cross-link is clean."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  version: '1.0.0'\npublication:\n"
        "  doi: '10.5281/zenodo.11111'\n"
        "  version_doi: '10.5281/zenodo.22222'\n"
        "  version_record: 'https://zenodo.org/records/22222'\n",
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text("version: '1.0.0'\ndoi: 10.5281/zenodo.11111\n", encoding="utf-8")
    (root / ".zenodo.json").write_text(
        '{"version": "1.0.0", "title": "X", "related_identifiers": '
        '[{"relation": "isVersionOf", "identifier": "10.5281/zenodo.11111", '
        '"scheme": "doi"}]}\n',
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publication_metadata_consistency(root, rep, "fake_project")
    assert not any(f.rule == "publication_zenodo_missing_concept_xlink" for f in rep.findings)


def test_publication_metadata_flags_cff_zenodo_version_drift_without_paper_version(drift_module, tmp_path):
    """Book-schema exemplars (no paper.version) still get CITATION/zenodo agreement."""
    root = _scaffold_minimal_project(tmp_path)
    # No paper.version (mirrors book-schema textbook); concept DOI present.
    (root / "manuscript" / "config.yaml").write_text(
        "publication:\n"
        "  doi: '10.5281/zenodo.11111'\n"
        "  version_doi: '10.5281/zenodo.22222'\n"
        "  version_record: 'https://zenodo.org/records/22222'\n",
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text("version: '0.1.0'\ndoi: 10.5281/zenodo.11111\n", encoding="utf-8")
    (root / ".zenodo.json").write_text(
        '{"version": "0.1", "title": "X", "related_identifiers": '
        '[{"relation": "isVersionOf", "identifier": "10.5281/zenodo.11111", '
        '"scheme": "doi"}]}\n',
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publication_metadata_consistency(root, rep, "fake_project")
    assert any(f.rule == "publication_cff_zenodo_version_drift" for f in rep.findings)


_GOOD_METADATA_CONFIG = (
    "paper:\n"
    "  title: Real Title\n"
    "  version: '1.0'\n"
    "  date: '2026-07-10'\n"
    "authors:\n"
    "  - name: 'Josiah Carberry'\n"
    "    orcid: '0000-0002-1825-0097'\n"
    "publication:\n"
    "  doi: '10.5281/zenodo.11111'\n"
)
# The 2026-07-10 incident shape: scaffold author + fabricated ORCID riding in
# the derived files after config.yaml itself was corrected.
_STALE_METADATA_CONFIG = _GOOD_METADATA_CONFIG.replace("Josiah Carberry", "Research Template Author").replace(
    "0000-0002-1825-0097", "0000-0000-0000-1234"
)


def _write_metadata_exports(root: Path, config_text: str) -> None:
    """Generate CITATION.cff/.zenodo.json/codemeta.json from a config snippet
    with the real generator — the same one the metadata-export CLI wraps."""
    import yaml

    from infrastructure.publishing.metadata_export import write_metadata_files

    write_metadata_files(yaml.safe_load(config_text), root, released_date="2026-07-10")


def test_metadata_export_negative_control_planted_author_mismatch_fires(drift_module, tmp_path):
    """Negative control / proof-of-detection: config.yaml carries the corrected
    author, but the tracked derived files still carry the scaffold
    'Research Template Author' with fabricated ORCID 0000-0000-0000-1234
    (the exact 2026-07-10 incident). All three files must raise ERROR."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    _write_metadata_exports(root, _STALE_METADATA_CONFIG)
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    author_errors = [f for f in rep.errors() if f.rule == "metadata_export_author_drift"]
    flagged_files = {f.message.split(" ", 1)[0] for f in author_errors}
    assert flagged_files == {"CITATION.cff", ".zenodo.json", "codemeta.json"}, [
        (f.rule, f.message) for f in rep.findings
    ]
    assert any("0000-0000-0000-1234" in f.message for f in author_errors)
    assert all("metadata_export_cli metadata-export --project fake_project" in f.message for f in author_errors)


def test_metadata_export_accepts_regenerated_files(drift_module, tmp_path):
    """Files regenerated from the same config must produce zero findings."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    _write_metadata_exports(root, _GOOD_METADATA_CONFIG)
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    assert not [f for f in rep.findings if f.rule.startswith("metadata_export")], [
        (f.rule, f.message) for f in rep.findings
    ]


def test_metadata_export_flags_concept_doi_drift_in_all_three_files(drift_module, tmp_path):
    """Derived files minted against a different concept DOI must raise in
    CITATION.cff (doi), .zenodo.json (isVersionOf), and codemeta.json (identifier)."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    _write_metadata_exports(root, _GOOD_METADATA_CONFIG.replace("zenodo.11111", "zenodo.99999"))
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    doi_errors = [f for f in rep.errors() if f.rule == "metadata_export_doi_drift"]
    assert {f.message.split(" ", 1)[0] for f in doi_errors} == {"CITATION.cff", ".zenodo.json", "codemeta.json"}
    assert not any(f.rule == "metadata_export_author_drift" for f in rep.findings)


def test_metadata_export_ignores_version_only_differences(drift_module, tmp_path):
    """Version/date churn is check_publication_metadata_consistency's turf —
    authorship+DOI agreement must NOT fire on a version-only difference."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    _write_metadata_exports(root, _GOOD_METADATA_CONFIG.replace("version: '1.0'", "version: '9.9'"))
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    assert not [f for f in rep.findings if f.rule.startswith("metadata_export")], [
        (f.rule, f.message) for f in rep.findings
    ]


def test_metadata_export_authorless_config_fallback_is_clean(drift_module, tmp_path):
    """A config with no authors block regenerates with the generator's
    'Project Author' fallback on both sides — must be clean, not drift."""
    root = _scaffold_minimal_project(tmp_path)
    config = "paper:\n  title: Real Title\n  version: '1.0'\npublication: {}\n"
    (root / "manuscript" / "config.yaml").write_text(config, encoding="utf-8")
    _write_metadata_exports(root, config)
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    assert not [f for f in rep.findings if f.rule.startswith("metadata_export")]


def test_metadata_export_url_form_orcid_is_not_drift(drift_module, tmp_path):
    """A CITATION.cff carrying the URL ORCID form (`https://orcid.org/0000-...`)
    names the same person as the generator's bare form — must NOT fire. A
    genuinely different identifier in the same URL form still must."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    _write_metadata_exports(root, _GOOD_METADATA_CONFIG)
    cff = root / "CITATION.cff"
    cff.write_text(
        cff.read_text(encoding="utf-8").replace(
            "orcid: 0000-0002-1825-0097", "orcid: https://orcid.org/0000-0002-1825-0097"
        ),
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    assert not [f for f in rep.findings if f.rule.startswith("metadata_export")], [
        (f.rule, f.message) for f in rep.findings
    ]
    # Same URL form, different identifier → still drift.
    cff.write_text(
        cff.read_text(encoding="utf-8").replace("0000-0002-1825-0097", "0000-0002-9999-9999"),
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    assert any(f.rule == "metadata_export_author_drift" and "CITATION.cff" in f.message for f in rep.errors())


def test_metadata_export_check_is_registered_in_project_checks():
    """The production gate runs registry.PROJECT_CHECKS — direct-call unit tests
    stay green even if the check is silently dropped from the registry, so the
    registration itself must be pinned."""
    from infrastructure.project.drift.checks_exemplar import check_metadata_export_current
    from infrastructure.project.drift.registry import PROJECT_CHECKS

    assert check_metadata_export_current in PROJECT_CHECKS


def test_metadata_export_skips_when_no_derived_files(drift_module, tmp_path):
    """Exemplars that do not ship the derived metadata files are out of scope."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")
    assert rep.findings == []


def test_metadata_export_flags_corrupt_json_without_crashing(drift_module, tmp_path):
    """A truncated .zenodo.json must yield a clean ERROR, not an uncaught exception."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(_GOOD_METADATA_CONFIG, encoding="utf-8")
    _write_metadata_exports(root, _GOOD_METADATA_CONFIG)
    (root / ".zenodo.json").write_text('{"creators": [', encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")  # must not raise
    assert any(f.rule == "metadata_export_unparseable" and f.severity == "ERROR" for f in rep.findings)


def test_metadata_export_flags_unparseable_config_without_crashing(drift_module, tmp_path):
    """Malformed config.yaml must yield a clean ERROR, not an uncaught YAMLError."""
    root = _scaffold_minimal_project(tmp_path)
    _write_metadata_exports(root, _GOOD_METADATA_CONFIG)
    (root / "manuscript" / "config.yaml").write_text("paper: {title: 'unterminated\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_metadata_export_current(root, rep, "fake_project")  # must not raise
    assert any(f.rule == "metadata_export_config_unparseable" and f.severity == "ERROR" for f in rep.findings)


def test_publishing_status_block_flags_missing_block(drift_module, tmp_path):
    """A project with manuscript/config.yaml but no PUBLISHING-STATUS block in README is drift."""
    root = _scaffold_minimal_project(tmp_path)
    rep = drift_module.Report()
    drift_module.check_publishing_status_block_current(root, rep, "fake_project")
    assert any(f.rule == "publishing_status_block_missing" for f in rep.findings)


def test_publishing_status_block_flags_stale_block(drift_module, tmp_path):
    """A PUBLISHING-STATUS block present but disagreeing with config.yaml is drift."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: Real Title\n  version: '1.0'\npublication:\n  doi: '10.5281/zenodo.99999'\n",
        encoding="utf-8",
    )
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n<!-- PUBLISHING-STATUS:START (generated by infrastructure.publishing.status_report) -->\n"
        "stale, hand-typed, does not match config.yaml\n"
        "<!-- PUBLISHING-STATUS:END -->\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publishing_status_block_current(root, rep, "fake_project")
    assert any(f.rule == "publishing_status_block_stale" for f in rep.findings)


def test_publishing_status_block_accepts_current_block(drift_module, tmp_path):
    """A block generated by the real CLI helper is accepted — no false positive."""
    from infrastructure.publishing.status_report import compile_publishing_status, render_status_block

    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  title: Real Title\n  version: '1.0'\npublication:\n  doi: '10.5281/zenodo.99999'\n",
        encoding="utf-8",
    )
    compiled = compile_publishing_status(root)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\n" + render_status_block(compiled) + "\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publishing_status_block_current(root, rep, "fake_project")
    assert not any(f.rule in {"publishing_status_block_missing", "publishing_status_block_stale"} for f in rep.findings)


def test_publishing_status_block_skips_project_without_config(drift_module, tmp_path):
    """No manuscript/config.yaml (non-manuscript project shape) — check is a no-op."""
    root = tmp_path / "no_manuscript_project"
    (root / "manuscript").mkdir(parents=True)
    write_doc(root / "README.md", "# No manuscript config here\n")
    rep = drift_module.Report()
    drift_module.check_publishing_status_block_current(root, rep, "fake_project")
    assert rep.findings == []


def test_publishing_status_block_skips_project_without_readme(drift_module, tmp_path):
    """config.yaml present but no README.md yet (mid-scaffold) — check is a no-op."""
    root = tmp_path / "no_readme_project"
    (root / "manuscript").mkdir(parents=True)
    write_doc(root / "manuscript" / "config.yaml", "paper: {}\npublication: {}\n")
    rep = drift_module.Report()
    drift_module.check_publishing_status_block_current(root, rep, "fake_project")
    assert rep.findings == []


def test_publishing_status_block_flags_unparseable_config_without_crashing(drift_module, tmp_path):
    """Malformed manuscript/config.yaml must yield a clean ERROR, not an uncaught YAMLError."""
    from infrastructure.publishing.status_report import render_status_block, compile_publishing_status

    root = _scaffold_minimal_project(tmp_path)
    # Seed a valid, current block first so the function reaches the compile_publishing_status() call.
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\n" + render_status_block(compile_publishing_status(root)) + "\n",
        encoding="utf-8",
    )
    # Now corrupt config.yaml with invalid YAML (unterminated flow mapping).
    (root / "manuscript" / "config.yaml").write_text("paper: {title: 'unterminated\n", encoding="utf-8")

    rep = drift_module.Report()
    drift_module.check_publishing_status_block_current(root, rep, "fake_project")  # must not raise
    assert any(f.rule == "publishing_status_config_unparseable" and f.severity == "ERROR" for f in rep.findings)


def test_docs_hardcoded_counts_flags_readme_literal(drift_module, tmp_path):
    (tmp_path / "README.md").write_text("We run 1234 infrastructure tests today.\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert any(f.rule == "repo_docs_hardcoded_test_count" for f in rep.findings)


def test_docs_hardcoded_counts_ignores_untracked_dirs_in_git_repo(drift_module, tmp_path):
    """In a real git repo, an untracked sibling dir must not redden the gate.

    Restores local↔CI parity: CI runs against a fresh clone that never contains
    local-only sibling projects, so a maintainer's `--strict` run must ignore
    them too. No mocks — a real git repo with a tracked-clean + untracked-dirty
    pair proves the tracked-set intersection.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    tracked = tmp_path / "README.md"
    tracked.write_text("This template links to COUNTS.md for live numbers.\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)

    untracked = tmp_path / "projects" / "codomyrmex_local"
    untracked.mkdir(parents=True)
    (untracked / "AGENTS.md").write_text("Coverage sits at 40% coverage right now.\n", encoding="utf-8")

    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert not any("codomyrmex_local" in f.message for f in rep.findings)

    # Regression guard: a tracked doc with a hardcoded count is still caught.
    tracked.write_text("Coverage sits at 40% coverage right now.\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    rep2 = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep2)
    assert any(f.rule == "repo_docs_hardcoded_coverage_pct" for f in rep2.findings)


def test_project_src_boundary_errors_on_standalone_infra_import(drift_module, tmp_path):
    root = tmp_path / "projects" / "templates" / "template_textbook"
    (root / "src").mkdir(parents=True)
    (root / "src" / "bad.py").write_text("from infrastructure.core import x\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_project_src_infrastructure_boundary(root, rep, "templates/template_textbook")
    assert any(f.rule == "src_infrastructure_import" and f.severity == "ERROR" for f in rep.findings)


def test_project_src_boundary_respects_layer_contract(drift_module, tmp_path):
    root = tmp_path / "projects" / "templates" / "template_code_project"
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "layer_contract.yaml").write_text(
        "allow_infrastructure_imports:\n  - src/analysis/_infra.py\n",
        encoding="utf-8",
    )
    (root / "src" / "analysis").mkdir(parents=True)
    (root / "src" / "analysis" / "_infra.py").write_text("from infrastructure.core import x\n", encoding="utf-8")
    (root / "src" / "other.py").write_text("x = 1\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_project_src_infrastructure_boundary(root, rep, "templates/template_code_project")
    assert not any(f.rule == "src_infrastructure_import" for f in rep.findings)


def test_end_to_end_run_on_live_exemplars_is_clean(drift_module):
    """Final smoke: the actual checked-in exemplars must be clean.

    If this test fails on `main`, someone landed drift that bypassed the
    pre-commit hook. The fix is in the source, not in this test.
    """
    rep = drift_module.Report()
    for proj in drift_module.PROJECT_NAMES:
        drift_module.check_project(proj, rep)
    assert rep.errors() == [], [(f.project, f.rule, f.message) for f in rep.errors()]
