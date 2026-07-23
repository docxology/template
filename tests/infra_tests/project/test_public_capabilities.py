"""Tests for the public exemplar capability inventory."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_capabilities import audit_public_capability, audit_public_capabilities
from tests._support.projects import make_project, write_doc


def test_public_capability_inventory_covers_all_canonical_exemplars(repo_root: Path) -> None:
    report = audit_public_capabilities(repo_root)

    assert len(report.projects) == 24
    assert report.passed
    assert all(project.test_file_count > 0 for project in report.projects)


def test_public_capability_inventory_reports_missing_structure(tmp_path: Path) -> None:
    project = make_project(tmp_path, "template_test", with_manuscript=True)
    write_doc(project / "README.md", "# Example\n")
    capability = audit_public_capability(tmp_path, "template_test")

    assert capability.passed is False
    assert "scripts" in capability.missing_paths
    assert "pyproject.toml" in capability.missing_paths


def test_public_capability_inventory_classifies_skip_contracts(tmp_path: Path) -> None:
    project = make_project(tmp_path, "template_test", with_manuscript=True, with_scripts=True)
    write_doc(
        project / "tests" / "test_skip_contract.py",
        "import pytest\n\ndef test_optional():\n    pytest.skip('optional tool not installed')\n",
    )
    capability = audit_public_capability(tmp_path, "template_test")

    assert len(capability.skip_contracts) == 1
    assert capability.skip_contracts[0].category == "OPTIONAL_CAPABILITY"
    assert capability.issues == ()
