"""Tests for `check_pyproject_publication_consistency`.

This detector closes a gate gap, so the tests are written the same way as
`tests/infra_tests/test_check_template_drift.py`: a gate that has never
failed is not a gate. Every rule this check can raise gets a **positive
control** that injects the drift and proves the detector fires, paired
with a negative control that proves it stays quiet on the clean form.

The originating defect (2026-07-27): `template_autopoiesis/pyproject.toml`
declared `version = "0.1.0"` while CITATION.cff, codemeta.json,
.zenodo.json and manuscript/config.yaml all declared `1.0.1` — the release
actually deposited as 10.5281/zenodo.21229620. It survived indefinitely
because `infrastructure/project/drift/checks_publication.py` cross-checked
config.yaml <-> CITATION.cff <-> .zenodo.json <-> codemeta.json and never
opened pyproject.toml, which is the sole input to `uv build`.

All inputs are real files written to `tmp_path` — no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.drift.checks_publication import (
    check_publication_metadata_consistency,
    check_pyproject_publication_consistency,
)
from infrastructure.project.drift.models import Report

REPO_ROOT = Path(__file__).resolve().parents[3]

_REAL_AUTHOR_CFF = """authors:
- affiliation: Active Inference Institute
  family-names: Friedman
  given-names: Daniel Ari
  orcid: 0000-0001-6232-9096
cff-version: 1.2.0
message: If you use this software, please cite it using the metadata from this file.
title: Fake Exemplar
type: software
version: {version}
"""


def _scaffold(tmp_path: Path, *, pyproject: str, cff_version: str = "1.0.1") -> Path:
    """Write the two files this detector reads, and nothing else."""
    root = tmp_path / "fake_project"
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    (root / "CITATION.cff").write_text(_REAL_AUTHOR_CFF.format(version=cff_version), encoding="utf-8")
    return root


def _rules(report: Report) -> list[str]:
    return [finding.rule for finding in report.findings]


# --------------------------------------------------------------------------
# Positive controls — the detector must FAIL on injected drift.
# --------------------------------------------------------------------------


def test_positive_control_pyproject_version_drift_is_error(tmp_path):
    """The exact 2026-07-27 template_autopoiesis defect must raise an ERROR."""
    root = _scaffold(
        tmp_path,
        pyproject='[project]\nname = "fake"\nversion = "0.1.0"\n',
        cff_version="1.0.1",
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_version_drift" in _rules(report)
    drift = next(f for f in report.findings if f.rule == "publication_pyproject_version_drift")
    assert drift.severity == "ERROR"
    assert "0.1.0" in drift.message and "1.0.1" in drift.message


def test_positive_control_version_drift_surfaces_through_public_entry_point(tmp_path):
    """The wiring matters, not just the helper: the drift must reach the check
    that the drift registry actually runs (`check_publication_metadata_consistency`),
    and must survive its early return for projects with no manuscript/config.yaml."""
    root = _scaffold(
        tmp_path,
        pyproject='[project]\nname = "fake"\nversion = "0.1.0"\n',
        cff_version="1.0.1",
    )
    assert not (root / "manuscript" / "config.yaml").exists()
    report = Report()
    check_publication_metadata_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_version_drift" in _rules(report)


def test_positive_control_version_drift_surfaces_for_draft_projects(tmp_path):
    """`check_publication_metadata_consistency` returns early on a draft
    publication status; the pyproject cross-check must run before that gate,
    because a wrongly stamped wheel is just as wrong for a draft exemplar."""
    root = _scaffold(
        tmp_path,
        pyproject='[project]\nname = "fake"\nversion = "0.1.0"\n',
        cff_version="1.0.1",
    )
    (root / "manuscript").mkdir()
    (root / "manuscript" / "config.yaml").write_text(
        "paper:\n  version: '1.0.1'\npublication:\n  status: draft\n",
        encoding="utf-8",
    )
    report = Report()
    check_publication_metadata_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_version_drift" in _rules(report)


def test_positive_control_scaffold_placeholder_author_is_error(tmp_path):
    """`Research Template Author` in pyproject rides into the wheel's
    `Author-email`; config.yaml-scoped placeholder scanning never saw it."""
    root = _scaffold(
        tmp_path,
        pyproject=(
            '[project]\nname = "fake"\nversion = "1.0.1"\n'
            'authors = [{name = "Research Template Author", email = "author@research-template.org"}]\n'
        ),
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_author_placeholder" in _rules(report)


def test_positive_control_author_absent_from_citation_cff_is_error(tmp_path):
    """A real-looking but uncredited author still splits the DOI record from
    the built distribution, so it is drift even though it is not a placeholder."""
    root = _scaffold(
        tmp_path,
        pyproject=(
            '[project]\nname = "fake"\nversion = "1.0.1"\n'
            'authors = [{name = "Someone Else", email = "someone@example.org"}]\n'
        ),
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_author_drift" in _rules(report)
    assert "publication_pyproject_author_placeholder" not in _rules(report)


def test_positive_control_unparseable_pyproject_is_error(tmp_path):
    """A pyproject the detector cannot parse must fail loudly, not read clean."""
    root = _scaffold(tmp_path, pyproject="[project\nname = broken\n")
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_unparseable" in _rules(report)


# --------------------------------------------------------------------------
# Negative controls — the detector must stay quiet on legitimate forms.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("py_version", "cff_version"),
    [
        ("0.1.0", "'0.1'"),
        ("0.1", "'0.1.0'"),
        ("1.0", "'1.0.0.0'"),
        ("2.5.2", "2.5.2"),
    ],
)
def test_pep440_equivalent_versions_are_not_drift(tmp_path, py_version, cff_version):
    """PEP 440 zero-pads release segments, so `0.1 == 0.1.0`. Flagging the
    string difference would turn template_search_project into a false positive."""
    root = _scaffold(
        tmp_path,
        pyproject=f'[project]\nname = "fake"\nversion = "{py_version}"\n',
        cff_version=cff_version,
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert report.findings == []


def test_non_numeric_versions_still_compare_exactly(tmp_path):
    """Pre/post/dev suffixes are not normalized into equality — `1.0.0rc1` and
    `1.0.0` name different releases and must still read as drift."""
    root = _scaffold(
        tmp_path,
        pyproject='[project]\nname = "fake"\nversion = "1.0.0rc1"\n',
        cff_version="1.0.0",
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert "publication_pyproject_version_drift" in _rules(report)


def test_matching_version_and_author_is_clean(tmp_path):
    root = _scaffold(
        tmp_path,
        pyproject=(
            '[project]\nname = "fake"\nversion = "1.0.1"\n'
            'authors = [{name = "Daniel Ari Friedman", email = "daniel@activeinference.institute"}]\n'
        ),
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert report.findings == []


def test_author_name_comparison_ignores_case_and_spacing(tmp_path):
    root = _scaffold(
        tmp_path,
        pyproject=('[project]\nname = "fake"\nversion = "1.0.1"\nauthors = [{name = "  daniel   ari  FRIEDMAN "}]\n'),
    )
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert report.findings == []


def test_missing_keys_and_dynamic_declarations_are_skipped(tmp_path):
    """Absence is not drift: three canonical exemplars declare no
    `[project] authors`, and a PEP 621 `dynamic` field is owned by the build
    backend rather than the file, so neither may be reported."""
    variants = (
        '[project]\nname = "fake"\n',
        '[project]\nname = "fake"\ndynamic = ["version"]\n',
        '[project]\nname = "fake"\nversion = "1.0.1"\ndynamic = ["authors"]\n'
        'authors = [{name = "Research Template Author"}]\n',
        "[tool.coverage.report]\nfail_under = 90\n",
    )
    for index, pyproject in enumerate(variants):
        root = _scaffold(tmp_path / f"variant_{index}", pyproject=pyproject)
        report = Report()
        check_pyproject_publication_consistency(root, report, "templates/fake_project")
        assert report.findings == [], pyproject


def test_no_citation_cff_means_nothing_to_cross_check(tmp_path):
    root = tmp_path / "fake_project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "fake"\nversion = "9.9.9"\n', encoding="utf-8")
    report = Report()
    check_pyproject_publication_consistency(root, report, "templates/fake_project")
    assert report.findings == []


# --------------------------------------------------------------------------
# The real tree: the shipped exemplars must satisfy the new gate.
# --------------------------------------------------------------------------


def test_canonical_exemplars_pass_the_new_check():
    """Bind the gate to the real tree, and assert the scan set is non-empty so
    the assertion cannot pass by scanning nothing."""
    templates = sorted(
        path
        for path in (REPO_ROOT / "projects" / "templates").iterdir()
        if path.is_dir() and path.name.startswith("template_")
    )
    assert len(templates) >= 20, "exemplar scan set collapsed — this gate would be vacuous"

    scanned_versions = 0
    scanned_authors = 0
    report = Report()
    for project_root in templates:
        check_pyproject_publication_consistency(project_root, report, f"templates/{project_root.name}")
        text = (project_root / "pyproject.toml").read_text(encoding="utf-8")
        scanned_versions += 1 if "\nversion = " in text else 0
        scanned_authors += 1 if "\nauthors = " in text else 0

    assert scanned_versions >= 20, "no exemplar declares [project] version — check would be vacuous"
    assert scanned_authors >= 20, "no exemplar declares [project] authors — check would be vacuous"
    assert report.findings == [], [f"{f.project}: {f.rule}" for f in report.findings]
