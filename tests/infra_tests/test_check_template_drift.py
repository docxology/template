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
        check_config_author_placeholders=checks.check_config_author_placeholders,
        check_metadata_export_current=checks.check_metadata_export_current,
        check_publication_index_completeness=checks.check_publication_index_completeness,
        check_publishing_status_block_current=checks.check_publishing_status_block_current,
        check_docs_hardcoded_counts=checks.check_docs_hardcoded_counts,
        check_project_src_infrastructure_boundary=checks.check_project_src_infrastructure_boundary,
        check_forkability_contract=checks.check_forkability_contract,
        check_shared_template_design_contract=checks.check_shared_template_design_contract,
        check_shared_template_truth_contract=checks.check_shared_template_truth_contract,
        check_project=lambda project, report: checks.check_project(REPO_ROOT, project, report),
    )


def _scaffold_minimal_project(tmp_path: Path, name: str = "fake_project") -> Path:
    """Write the minimum file set every detector expects to find."""
    root = make_project(tmp_path, name, with_manuscript=True)
    (root / "docs").mkdir()
    (root / "scripts").mkdir()
    # Part of the exemplar contract since 2026-07-27: a fork must carry its own
    # grant. `test_required_files_exist_flags_missing_license` is the paired
    # positive control proving the detector still rejects its absence.
    (root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 Test\n", encoding="utf-8")
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


def test_shared_template_truth_contract_rejects_roster_and_output_policy_drift(drift_module, tmp_path):
    templates = tmp_path / "projects" / "templates"
    templates.mkdir(parents=True)
    write_doc(templates / "AGENTS.md", "Twenty public canonical exemplar projects.\n")
    write_doc(templates / "DESIGN.md", "All eighteen public template exemplars.\n")
    write_doc(tmp_path / "CLAUDE.md", "Never commit generated outputs to version control.\n")

    rep = drift_module.Report()
    drift_module.check_shared_template_truth_contract(tmp_path, rep)

    rules = {finding.rule for finding in rep.errors()}
    assert "shared_template_roster_literal" in rules
    assert "shared_template_roster_pointer_missing" in rules
    assert "public_output_policy_contradiction" in rules


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
