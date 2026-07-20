"""Root release version and target-boundary contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.publishing.root_release_contract import (
    main,
    root_changelog_versions,
    root_package_version,
    validate_root_release_tag,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _write_pyproject(repo_root: Path, version: str = "3.5.1") -> None:
    (repo_root / "pyproject.toml").write_text(
        f'[project]\nname = "template"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (repo_root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [Unreleased]\n\n## [{version}] — 2026-06-26\n",
        encoding="utf-8",
    )


def test_root_release_tag_must_exactly_match_package_version(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)

    assert validate_root_release_tag(tmp_path, "v3.5.1") == "3.5.1"
    with pytest.raises(ValueError, match="configured standalone repository"):
        validate_root_release_tag(tmp_path, "v1.0.1")


def test_root_package_version_rejects_missing_project_version(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "template"\n', encoding="utf-8")

    with pytest.raises(ValueError, match="project.version"):
        root_package_version(tmp_path)


def test_root_release_rejects_missing_changelog_heading(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n", encoding="utf-8")

    assert root_changelog_versions(tmp_path) == ()
    with pytest.raises(ValueError, match="no released heading"):
        validate_root_release_tag(tmp_path, "v3.5.1")


def test_cli_fails_closed_for_exemplar_shaped_tag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_pyproject(tmp_path)

    assert main(["--repo-root", str(tmp_path), "--tag", "v1.0.1"]) == 2
    assert "root release contract failed" in capsys.readouterr().out


def test_cli_reports_matching_root_version(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_pyproject(tmp_path)

    assert main(["--repo-root", str(tmp_path), "--tag", "v3.5.1"]) == 0
    assert capsys.readouterr().out == "root release contract passed: v3.5.1\n"


def test_root_release_workflow_invokes_version_contract() -> None:
    workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "Verify root package release contract" in workflow
    assert 'python -m infrastructure.publishing.root_release_contract --tag "$TAG"' in workflow
    assert "ref: ${{ steps.tag.outputs.name }}" in workflow
    assert 'EXPECTED=$(git rev-parse "refs/tags/$TAG^{commit}")' in workflow
    assert 'if [ "$ACTUAL" != "$EXPECTED" ]; then' in workflow
    assert workflow.index("Determine tag name") < workflow.index("uses: actions/checkout@")
    assert workflow.index("Verify checkout is the requested tag") < workflow.index("uv build")
