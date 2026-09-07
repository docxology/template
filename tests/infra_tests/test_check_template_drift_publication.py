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
_STALE_METADATA_CONFIG = _GOOD_METADATA_CONFIG.replace("Josiah Carberry", "Research Template Author").replace(
    "0000-0002-1825-0097", "0000-0000-0000-1234"
)


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


def test_docs_hardcoded_counts_flags_bare_test_total(drift_module, tmp_path):
    """The highest-churn form: a plain per-exemplar total with no qualifier.

    The original pattern required the words infrastructure/project/infra between
    the number and "tests", so `279 tests, mirroring src/...` in an exemplar
    README was never caught — which is how adding one test to template_formal
    came to require editing nine separate hardcoded totals (2026-07-27).
    """
    (tmp_path / "README.md").write_text("279 tests, mirroring the src layout.\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert any(f.rule == "repo_docs_hardcoded_test_count" for f in rep.findings)


def test_docs_hardcoded_counts_flags_reversed_coverage_phrasing(drift_module, tmp_path):
    """`Total coverage: 95.91%` must be caught, not just `95.91% coverage`."""
    (tmp_path / "README.md").write_text("Total coverage: 95.91%\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert any(f.rule == "repo_docs_hardcoded_coverage_pct" for f in rep.findings)


def test_docs_hardcoded_counts_ignores_stage_identifiers(drift_module, tmp_path):
    """`Stage 01 test runner` is a stage number, not a measured total."""
    (tmp_path / "README.md").write_text(
        "Owns the Stage 01 test runner and the Stage-02 tests lane.\n", encoding="utf-8"
    )
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert not any(f.rule == "repo_docs_hardcoded_test_count" for f in rep.findings)


def test_docs_hardcoded_counts_ignores_singular_noun_phrases(drift_module, tmp_path):
    """`50 test images per class` describes a dataset, not a suite."""
    (tmp_path / "README.md").write_text("It contains 50 test images per class.\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert not any(f.rule == "repo_docs_hardcoded_test_count" for f in rep.findings)


def test_docs_hardcoded_counts_ignores_policy_coverage_floors(drift_module, tmp_path):
    """Contract floors (60/75/90) are policy, not measurements."""
    (tmp_path / "README.md").write_text(
        "Projects must hold 90% coverage; infrastructure requires 60% coverage.\n", encoding="utf-8"
    )
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert not any(f.rule == "repo_docs_hardcoded_coverage_pct" for f in rep.findings)


def test_docs_hardcoded_counts_honours_noqa_for_dated_history(drift_module, tmp_path):
    """A dated historical record opts out; the escape hatch must work."""
    (tmp_path / "README.md").write_text(
        "The 2026-07 audit ran 362 tests. <!-- noqa: drift-counts -->\n", encoding="utf-8"
    )
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    assert rep.findings == []


def test_docs_hardcoded_counts_noqa_does_not_leak_to_other_lines(drift_module, tmp_path):
    """The escape hatch is per-line, so it cannot silence a whole file."""
    (tmp_path / "README.md").write_text(
        "Historical: 362 tests. <!-- noqa: drift-counts -->\nToday we run 999 tests.\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    messages = [f.message for f in rep.findings if f.rule == "repo_docs_hardcoded_test_count"]
    assert len(messages) == 1
    assert "999 tests" in messages[0]


def test_docs_hardcoded_counts_exempts_the_explicit_backlog_history_file(drift_module, tmp_path):
    """Immutable backlog evidence is exempt, while other tracked docs remain live-checked."""
    history = tmp_path / "docs" / "maintenance" / "exemplar-backlog-history.md"
    history.parent.mkdir(parents=True)
    history.write_text("The historical run recorded 362 tests and 91.2% coverage.\n", encoding="utf-8")
    other_history = tmp_path / "docs" / "maintenance" / "other-history.md"
    other_history.write_text("A different record reported 361 tests.\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "docs"], cwd=tmp_path, check=True)

    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)

    messages = [f.message for f in rep.findings]
    assert not any("exemplar-backlog-history.md" in message for message in messages)
    assert any("other-history.md" in message for message in messages)


def test_docs_hardcoded_counts_reports_line_numbers(drift_module, tmp_path):
    """Findings must cite a line, not a byte offset, to be actionable."""
    (tmp_path / "README.md").write_text("intro\n\nWe run 500 tests.\n", encoding="utf-8")
    rep = drift_module.Report()
    drift_module.check_docs_hardcoded_counts(tmp_path, rep)
    finding = next(f for f in rep.findings if f.rule == "repo_docs_hardcoded_test_count")
    assert "README.md:3:" in finding.message


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


@pytest.mark.timeout(300)
def test_end_to_end_run_on_live_exemplars_is_clean(drift_module):
    """Final smoke: the actual checked-in exemplars must be clean.

    If this test fails on `main`, someone landed drift that bypassed the
    pre-commit hook. The fix is in the source, not in this test.
    """
    rep = drift_module.Report()
    for proj in drift_module.PROJECT_NAMES:
        drift_module.check_project(proj, rep)
    assert rep.errors() == [], [(f.project, f.rule, f.message) for f in rep.errors()]
