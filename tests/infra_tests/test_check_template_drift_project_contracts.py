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
    # Documented canonical surface (projects/templates/AGENTS.md): the
    # per-exemplar agent skill catalog.
    skill_dir = root / ".agents" / "skills" / name.replace("_", "-")
    skill_dir.mkdir(parents=True)
    (root / ".agents" / "AGENTS.md").write_text("# Agent contract\n", encoding="utf-8")
    for filename in ("SKILL.md", "AGENTS.md", "README.md"):
        (skill_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")
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


def test_required_files_exist_flags_missing_license(drift_module, tmp_path):
    """Positive control for the LICENSE clause of the exemplar contract.

    Until 2026-07-27, 23 of 24 exemplars declared a license only in CITATION.cff
    and shipped no LICENSE, so a fork asserted terms it never granted.
    """
    root = _scaffold_minimal_project(tmp_path)
    (root / "LICENSE").unlink()
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "missing_canonical_file" and "LICENSE" in f.message for f in rep.findings
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


def test_required_files_exist_flags_missing_agents_catalog(drift_module, tmp_path):
    """Positive control: the documented .agents/ skill catalog is enforced."""
    import shutil

    root = _scaffold_minimal_project(tmp_path)
    shutil.rmtree(root / ".agents")
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "missing_canonical_file" and ".agents/AGENTS.md" in f.message
        for f in rep.findings
    )


def test_required_files_exist_flags_missing_skill_definition(drift_module, tmp_path):
    """The per-exemplar skill SKILL.md is part of the canonical surface."""
    root = _scaffold_minimal_project(tmp_path)
    (root / ".agents" / "skills" / "fake-project" / "SKILL.md").unlink()
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR"
        and f.rule == "missing_canonical_file"
        and ".agents/skills/fake-project/SKILL.md" in f.message
        for f in rep.findings
    )


def test_required_files_exist_skill_name_uses_bare_qualified_project(drift_module, tmp_path):
    """A qualified roster name ("templates/<name>") maps to the same skill folder."""
    root = _scaffold_minimal_project(tmp_path)
    rep = drift_module.Report()
    drift_module.check_required_files_exist(root, rep, "templates/fake_project")
    assert rep.findings == []


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


def test_config_author_placeholder_name_is_error(drift_module, tmp_path):
    """A scaffold author name in config.yaml itself must ERROR — the derived
    CITATION.cff/.zenodo.json would agree with the bad source and pass the
    export-consistency checks green."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper: {}\npublication: {}\nauthors:\n  - name: 'Research Template Author'\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_config_author_placeholders(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "config_author_placeholder_name" and "Research Template Author" in f.message
        for f in rep.findings
    )


def test_config_author_placeholder_orcid_is_error(drift_module, tmp_path):
    """All-zero / example ORCIDs must ERROR, including the URL form."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper: {}\npublication: {}\nauthors:\n"
        "  - name: 'Real Person'\n    orcid: '0000-0000-0000-0000'\n"
        "  - name: 'Other Person'\n    orcid: 'https://orcid.org/0000-0000-0000-1234'\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_config_author_placeholders(root, rep, "fake_project")
    orcid_errors = [f for f in rep.findings if f.rule == "config_author_placeholder_orcid"]
    assert len(orcid_errors) == 2
    assert all(f.severity == "ERROR" for f in orcid_errors)


def test_config_author_unknown_keys_is_error(drift_module, tmp_path):
    """Unrecognized author sub-keys (e.g. plural 'affiliations:') are silently
    dropped by the metadata generator — the check must catch them."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper: {}\npublication: {}\nauthors:\n"
        "  - name: 'Real Person'\n    orcid: '0000-0001-6232-9096'\n"
        "    affiliations: 'Some Institute'\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_config_author_placeholders(root, rep, "fake_project")
    assert any(
        f.severity == "ERROR" and f.rule == "config_author_unknown_keys" and "affiliations" in f.message
        for f in rep.findings
    )


def test_config_authors_missing_with_reserved_doi_warns(drift_module, tmp_path):
    """A reserved concept DOI with no authors block warns — the 'Project Author'
    generator fallback would ride into a real Zenodo deposit."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper: {}\npublication:\n  doi: '10.5281/zenodo.11111'\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_config_author_placeholders(root, rep, "fake_project")
    assert any(f.severity == "WARNING" and f.rule == "config_authors_missing_with_doi" for f in rep.findings)


def test_config_author_placeholders_negative_control(drift_module, tmp_path):
    """Negative control: a real author with only known keys, and a no-DOI
    config with no authors block, must both produce zero findings."""
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper: {}\npublication:\n  doi: '10.5281/zenodo.11111'\nauthors:\n"
        "  - name: 'Daniel Ari Friedman'\n    orcid: '0000-0001-6232-9096'\n"
        "    email: 'x@example.com'\n    affiliation: 'Active Inference Institute'\n"
        "    corresponding: true\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_config_author_placeholders(root, rep, "fake_project")
    assert rep.findings == []

    (root / "manuscript" / "config.yaml").write_text("paper: {}\npublication: {}\n", encoding="utf-8")
    rep2 = drift_module.Report()
    drift_module.check_config_author_placeholders(root, rep2, "fake_project")
    assert rep2.findings == []


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


def _write_complete_publication_index(root: Path) -> None:
    """Write the minimum complete source surface for the index contract."""
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n"
        "  title: Complete exemplar\n"
        "  version: '1.2.3'\n"
        "publication:\n"
        "  doi: '10.5281/zenodo.11111'\n"
        "  version_doi: '10.5281/zenodo.22222'\n"
        "  version_record: 'https://zenodo.org/records/22222'\n"
        "  github_repository: 'docxology/template_complete'\n"
        "  published_artifacts:\n"
        "    osf: 'https://osf.io/abc12/'\n",
        encoding="utf-8",
    )
    (root / "STANDALONE.md").write_text(
        "# Complete\n\n<!-- BEGIN:PUBLICATION_INDEX -->\nidentity\n<!-- END:PUBLICATION_INDEX -->\n",
        encoding="utf-8",
    )
    for name in ("CITATION.cff", ".zenodo.json", "codemeta.json"):
        (root / name).write_text("{}\n", encoding="utf-8")


def test_publication_index_completeness_requires_public_identity_surface(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    rep = drift_module.Report()
    drift_module.check_publication_index_completeness(root, rep, "templates/template_fake")
    rules = {finding.rule for finding in rep.errors()}
    assert "publication_index_file_missing" in rules
    assert "publication_index_value_missing" in rules
    assert "publication_index_github_missing" in rules


def test_publication_index_completeness_accepts_complete_exemplar(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    _write_complete_publication_index(root)
    rep = drift_module.Report()
    drift_module.check_publication_index_completeness(root, rep, "templates/template_complete")
    assert rep.findings == []


def test_publication_index_completeness_accepts_explicit_public_draft(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n"
        "  title: Draft exemplar\n"
        "  version: '0.1.0'\n"
        "publication:\n"
        "  status: draft\n"
        "  github_repository: 'docxology/template_draft'\n",
        encoding="utf-8",
    )
    (root / "STANDALONE.md").write_text(
        "# Draft\n\n<!-- BEGIN:PUBLICATION_INDEX -->\ndraft identity\n<!-- END:PUBLICATION_INDEX -->\n",
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publication_index_completeness(root, rep, "templates/template_draft")
    drift_module.check_publication_metadata_consistency(root, rep, "templates/template_draft")
    assert rep.findings == []


def test_publication_index_completeness_rejects_bad_mirror_declarations(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    _write_complete_publication_index(root)
    config = root / "manuscript" / "config.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "    osf: 'https://osf.io/abc12/'", "    imaginary_archive: 'not-a-url'"
        ),
        encoding="utf-8",
    )
    rep = drift_module.Report()
    drift_module.check_publication_index_completeness(root, rep, "templates/template_complete")
    rules = {finding.rule for finding in rep.errors()}
    assert rules >= {"publication_index_platform_unknown", "publication_index_url_invalid"}


def test_publication_index_completeness_is_registered():
    from infrastructure.project.drift.checks_exemplar import check_publication_index_completeness
    from infrastructure.project.drift.registry import PROJECT_CHECKS

    assert check_publication_index_completeness in PROJECT_CHECKS


def test_publication_index_completeness_does_not_constrain_private_projects(drift_module, tmp_path):
    root = _scaffold_minimal_project(tmp_path)
    rep = drift_module.Report()
    drift_module.check_publication_index_completeness(root, rep, "working/private_project")
    assert rep.findings == []


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
