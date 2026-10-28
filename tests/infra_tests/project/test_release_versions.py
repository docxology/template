"""Root and exemplar version identity across every release surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.project.release_versions import (
    format_release_version_report,
    normalize_version,
    validate_release_versions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT = "templates/template_probe"


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _scaffold(
    root: Path,
    *,
    root_version: str = "4.3.0",
    intended: str = "0.2.0",
    published: str | None = "0.1.0",
    status: str = "unreleased",
    version_doi: str | None = "10.5281/zenodo.11111111",
    platform: str = "4.3.0",
    package: str = "0.2.0",
    citation: str | None = "0.1.0",
    repository: str = "owner/template_probe",
) -> None:
    _write(root, "pyproject.toml", f'[project]\nname = "research-project-template"\nversion = "{root_version}"\n')
    _write(
        root,
        "CHANGELOG.md",
        f"# Changelog\n\n## [{root_version}]\n\nNotes.\n",
    )
    _write(root, f"docs/releases/v{root_version}.md", "# notes\n")
    _write(root, f"docs/releases/template-v{root_version}-overview.svg", "<svg/>\n")
    _write(root, f"docs/releases/template-v{root_version}-overview.png", "png\n")
    publication_lines = [
        f'release_status: "{status}"',
        f'intended_version: "{intended}"',
        f'platform_version: "{platform}"',
        f'github_repository: "{repository}"',
        f'repository_url: "https://github.com/{repository}"',
    ]
    if published:
        publication_lines.append(f'last_published_version: "{published}"')
    if version_doi:
        publication_lines.append(f'version_doi: "{version_doi}"')
    _write(
        root,
        f"projects/{PROJECT}/manuscript/config.yaml",
        "paper:\n  title: probe\n" + "publication:\n  " + "\n  ".join(publication_lines) + "\n",
    )
    dependencies = f'"research-project-template=={root_version}"'
    _write(
        root,
        f"projects/{PROJECT}/pyproject.toml",
        f'[project]\nname = "template-probe"\nversion = "{package}"\ndependencies = [{dependencies}]\n\n'
        '[tool.uv.sources]\nresearch-project-template = { path = "../../..", editable = true }\n\n'
        f'[tool.template]\nplatform_version = "{platform}"\ntested_python_versions = ["3.14", "3.15"]\n',
    )
    _write(root, f"projects/{PROJECT}/STANDALONE.md", "# Standalone\n")
    # Root tag validation parses the canonical runtime version provider.
    provider = REPO_ROOT / "infrastructure" / "_version.py"
    if provider.is_file():
        _write(root, "infrastructure/_version.py", provider.read_text(encoding="utf-8"))
    if citation is not None and published:
        _write(
            root,
            f"projects/{PROJECT}/CITATION.cff",
            f'authors:\n- family-names: Probe\n  given-names: Test\nversion: "{citation}"\n',
        )
    if published:
        _write(root, f"projects/{PROJECT}/.zenodo.json", json.dumps({"version": published}, indent=2) + "\n")
        _write(root, f"projects/{PROJECT}/codemeta.json", json.dumps({"version": published}, indent=2) + "\n")


def test_version_normalization_pads_only_simple_versions() -> None:
    assert normalize_version("0.1") == normalize_version("0.1.0") == "0.1.0"
    assert normalize_version("v4.3.0") == "4.3.0"
    assert normalize_version("1.0.0rc1") == "1.0.0rc1"


def test_coherent_root_and_exemplar_pass(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    report = validate_release_versions(tmp_path, tag="v4.3.0", projects=(PROJECT,))
    assert report.passed, format_release_version_report(report)
    assert report.root_version == "4.3.0"
    assert report.projects == 1


def test_missing_root_release_artifact_is_reported(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    (tmp_path / "docs/releases/template-v4.3.0-overview.png").unlink()
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    details = " ".join(f"{item.rule} {item.detail}" for item in report.findings)
    assert "release-artifact" in details and "template-v4.3.0-overview.png" in details


def test_missing_release_notes_is_reported(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    (tmp_path / "docs/releases/v4.3.0.md").unlink()
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    assert any(item.rule == "release-notes" for item in report.findings)


def test_tag_that_differs_from_the_declared_version_is_reported(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    report = validate_release_versions(tmp_path, tag="v4.1.0", projects=(PROJECT,))
    assert any(item.rule == "tag" for item in report.findings)


def test_package_version_must_equal_the_declared_intended_version(tmp_path: Path) -> None:
    _scaffold(tmp_path, package="0.3.0")
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    details = " ".join(item.detail for item in report.findings)
    assert "differs from intended_version" in details


def test_published_artifacts_must_equal_the_last_published_version(tmp_path: Path) -> None:
    _scaffold(tmp_path, citation="0.0.9")
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    details = " ".join(item.detail for item in report.findings)
    assert "CITATION version 0.0.9" in details


def test_version_doi_must_accompany_a_published_version(tmp_path: Path) -> None:
    _scaffold(tmp_path, version_doi=None)
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    assert any(item.rule == "version-doi" for item in report.findings)


def test_unreleased_project_may_not_equal_its_published_version(tmp_path: Path) -> None:
    _scaffold(tmp_path, intended="0.1.0", published="0.1.0", package="0.1.0", citation="0.1.0")
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    assert any("equals last published" in item.detail for item in report.findings)


def test_platform_version_must_follow_the_root_version(tmp_path: Path) -> None:
    _scaffold(tmp_path, platform="4.1.0")
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    assert any(item.rule == "platform-version" for item in report.findings)


def test_repository_must_be_owner_and_name(tmp_path: Path) -> None:
    _scaffold(tmp_path, repository="docxology")
    report = validate_release_versions(tmp_path, projects=(PROJECT,))
    assert any(item.rule == "repository" for item in report.findings)


@pytest.mark.skipif(not (REPO_ROOT / "pyproject.toml").is_file(), reason="requires the template checkout")
def test_actual_checkout_is_version_coherent() -> None:
    report = validate_release_versions(REPO_ROOT)
    assert report.passed, format_release_version_report(report)
    assert report.projects == 25
