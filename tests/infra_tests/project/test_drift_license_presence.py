"""Tests for `check_license_file_present_and_consistent`.

A gate that has never failed is not a gate, so every rule this detector can
raise gets a **positive control** that injects the defect and proves the check
fires, paired with a negative control on the clean form.

The originating defect (2026-07-27): 23 of the 24 public exemplars declared a
license in `CITATION.cff` — the surface their Zenodo deposits were made from —
while shipping no `LICENSE` file at all, and 21 declared no `[project] license`
in `pyproject.toml` either. A fork extracted through `STANDALONE.md` therefore
arrived with a README asserting terms that no file in the tree granted, and a
wheel built from it carried no license metadata.

All inputs are real files written to `tmp_path` — no mocks.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.drift.checks_publication import (
    check_license_file_present_and_consistent,
)
from infrastructure.project.drift.models import Report

_CFF = """authors:
- family-names: Friedman
  given-names: Daniel Ari
cff-version: 1.2.0
message: If you use this software, please cite it using the metadata from this file.
title: Fake Exemplar
type: software
version: 1.0.0
license: {license}
"""

_MIT_BODY = "MIT License\n\nCopyright (c) 2026 Daniel Ari Friedman\n\nPermission is hereby granted...\n"
_APACHE_BODY = "                                 Apache License\n                           Version 2.0\n"
_CC_BODY = "Creative Commons Attribution 4.0 International (CC BY 4.0)\n\nCopyright (c) 2026 D. A. F.\n"


def _scaffold(
    tmp_path: Path,
    *,
    declared: str = "MIT",
    license_body: str | None = _MIT_BODY,
    pyproject: str | None = None,
    extra: dict[str, str] | None = None,
) -> Path:
    root = tmp_path / "fake_project"
    root.mkdir(parents=True, exist_ok=True)
    (root / "CITATION.cff").write_text(_CFF.format(license=declared), encoding="utf-8")
    if license_body is not None:
        (root / "LICENSE").write_text(license_body, encoding="utf-8")
    if pyproject is not None:
        (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    for name, body in (extra or {}).items():
        (root / name).write_text(body, encoding="utf-8")
    return root


def _rules(report: Report) -> list[str]:
    return [finding.rule for finding in report.findings]


# --------------------------------------------------------------------------
# Positive controls — the detector must FAIL on injected defects.
# --------------------------------------------------------------------------


def test_positive_control_missing_license_file_is_error(tmp_path: Path) -> None:
    """The exact 2026-07-27 defect: license declared, no LICENSE shipped."""
    root = _scaffold(tmp_path, declared="MIT", license_body=None)
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert "publication_license_file_missing" in _rules(report)
    finding = next(f for f in report.findings if f.rule == "publication_license_file_missing")
    assert finding.severity == "ERROR"
    assert "MIT" in finding.message


def test_positive_control_license_body_disagrees_with_declaration(tmp_path: Path) -> None:
    root = _scaffold(tmp_path, declared="MIT", license_body=_APACHE_BODY)
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert "publication_license_file_drift" in _rules(report)


def test_positive_control_pyproject_license_disagrees_with_cff(tmp_path: Path) -> None:
    root = _scaffold(
        tmp_path,
        declared="MIT",
        pyproject='[project]\nname = "fake"\nlicense = {text = "Apache-2.0"}\n',
    )
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert "publication_license_metadata_drift" in _rules(report)


# --------------------------------------------------------------------------
# Negative controls — the detector must stay quiet on valid layouts.
# --------------------------------------------------------------------------


def test_negative_control_matching_license_is_clean(tmp_path: Path) -> None:
    root = _scaffold(
        tmp_path,
        declared="MIT",
        pyproject='[project]\nname = "fake"\nlicense = {text = "MIT"}\n',
    )
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert report.findings == []


def test_negative_control_dual_license_layout_is_accepted(tmp_path: Path) -> None:
    """Apache-2.0 code + declared CC-BY-4.0 content in a LICENSE-* sibling."""
    root = _scaffold(
        tmp_path,
        declared="CC-BY-4.0",
        license_body=_APACHE_BODY,
        extra={"LICENSE-CONTENT.md": "# Content License\n\nCreative Commons Attribution 4.0 International\n"},
    )
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert report.findings == []


def test_dual_license_claim_needs_a_real_sibling(tmp_path: Path) -> None:
    """A LICENSE-* sibling that does NOT carry the declared license must still fail.

    Guards the dual-license escape hatch against becoming a blanket bypass: the
    exemption is earned by a sibling that actually grants the declared terms.
    """
    root = _scaffold(
        tmp_path,
        declared="CC-BY-4.0",
        license_body=_APACHE_BODY,
        extra={"LICENSE-NOTES.md": "See the project website for terms.\n"},
    )
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert "publication_license_file_drift" in _rules(report)


def test_absent_citation_cff_is_not_drift(tmp_path: Path) -> None:
    root = tmp_path / "fake_project"
    root.mkdir(parents=True, exist_ok=True)
    report = Report()
    check_license_file_present_and_consistent(root, report, "templates/fake_project")
    assert report.findings == []


def test_every_public_exemplar_satisfies_the_license_contract() -> None:
    """Bind the gate to the live tree, not just fixtures."""
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    repo_root = Path(__file__).resolve().parents[3]
    report = Report()
    checked = 0
    for qualified in PUBLIC_PROJECT_NAMES:
        project_root = repo_root / "projects" / qualified
        if not project_root.is_dir():
            continue
        checked += 1
        check_license_file_present_and_consistent(project_root, report, qualified)
    assert checked > 0, "no public exemplars found — the scan set went empty"
    assert report.findings == [], [f.message for f in report.findings]
