"""Root release version and target-boundary contracts."""

from __future__ import annotations

from pathlib import Path

import subprocess

import pytest

from infrastructure.publishing.root_release_contract import (
    main,
    root_changelog_versions,
    root_package_version,
    root_runtime_version,
    validate_root_versions,
    validate_root_release_tag,
    RUNTIME_VERSION_PROVIDER_SOURCE,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _write_pyproject(repo_root: Path, version: str = "3.5.1") -> None:
    (repo_root / "pyproject.toml").write_text(
        f'[project]\nname = "research-project-template"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    (repo_root / "infrastructure").mkdir(exist_ok=True)
    (repo_root / "infrastructure" / "_version.py").write_text(RUNTIME_VERSION_PROVIDER_SOURCE, encoding="utf-8")
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


def test_cli_fails_closed_for_exemplar_shaped_tag(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)

    assert main(["--repo-root", str(tmp_path), "--tag", "v1.0.1"]) == 2
    assert main(["--repo-root", str(tmp_path), "--tag", "v3.5.1"]) == 0


def test_runtime_and_package_version_drift_blocks_release(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    (tmp_path / "infrastructure/_version.py").write_text('__version__ = "3.6.0"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="canonical package metadata"):
        validate_root_release_tag(tmp_path, "v3.5.1")


def test_runtime_version_is_read_without_executing_source(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    (tmp_path / "infrastructure/_version.py").write_text(
        RUNTIME_VERSION_PROVIDER_SOURCE + '# raise RuntimeError("must not execute")\n', encoding="utf-8"
    )
    assert root_runtime_version(tmp_path) == "3.5.1"


def test_current_source_versions_agree() -> None:
    from infrastructure import __version__

    assert validate_root_versions(REPO_ROOT) == __version__


@pytest.mark.parametrize(
    "source",
    [
        '__version__ = ""',
        "__version__ = str(4)",
        '__version__ = "4"\n__version__ = "5"',
        '__version__ = "4"\n__version__ = str(5)',
    ],
)
def test_retired_runtime_constant_and_arbitrary_code_are_refused(tmp_path: Path, source: str) -> None:
    _write_pyproject(tmp_path)
    (tmp_path / "infrastructure/_version.py").write_text(source, encoding="utf-8")
    with pytest.raises(ValueError, match="canonical package metadata"):
        validate_root_versions(tmp_path)


def test_intended_unreleased_version_does_not_authorize_tag(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "4.0.1")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## [4.0.1] - Unreleased\n")
    assert root_changelog_versions(tmp_path) == ()
    with pytest.raises(ValueError, match="no released heading"):
        validate_root_release_tag(tmp_path, "v4.0.1")


def test_wrong_distribution_provider_is_refused(tmp_path: Path) -> None:
    _write_pyproject(tmp_path)
    (tmp_path / "infrastructure/_version.py").write_text(
        'from importlib.metadata import version\n__version__ = version("other-package")\n'
    )
    with pytest.raises(ValueError, match="canonical package metadata"):
        root_runtime_version(tmp_path)


@pytest.mark.parametrize("case", ["accepted", "checkout-receipt-only", "missing-receipt", "different-revision"])
def test_release_publication_inputs_require_exact_handoff(tmp_path: Path, case: str) -> None:
    """Execute actual workflow routing; absent/stale handoffs never fall back."""
    import os
    import yaml

    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["release"]["steps"]
    selection = next(step for step in steps if step.get("id") == "release_inputs")
    source = tmp_path / "release source"
    source.mkdir()

    def git(root: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
        )

    git(source, "init", "--quiet")
    git(source, "config", "user.name", "Release Routing Test")
    git(source, "config", "user.email", "release-routing@example.invalid")
    (source / "authored.txt").write_text("same authored source\n")
    git(source, "add", "authored.txt")
    git(source, "commit", "--quiet", "-m", "Freeze test source")
    temporary = tmp_path / "runner temporary"
    temporary.mkdir()
    mirror = temporary / "template-release-reader-root"
    git(source, "clone", "--quiet", "--no-hardlinks", str(source), str(mirror))
    root = source if case == "checkout-receipt-only" else mirror
    relative = (
        "output/readiness/installed-release-123-1/receipt.json"
        if case == "checkout-receipt-only"
        else "output/readiness/installed/receipt.json"
    )
    receipt = root / relative
    if case != "missing-receipt":
        receipt.parent.mkdir(parents=True)
        receipt.write_text("{}\n")  # Routing only; existing validators authenticate evidence.
    if case == "different-revision":
        git(mirror, "config", "user.name", "Release Routing Test")
        git(mirror, "config", "user.email", "release-routing@example.invalid")
        (mirror / "authored.txt").write_text("different authored source\n")
        git(mirror, "add", "authored.txt")
        git(mirror, "commit", "--quiet", "-m", "Different test source")
    output = tmp_path / "output.txt"
    environment = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    environment.update(
        GITHUB_WORKSPACE=str(source),
        RUNNER_TEMP=str(temporary),
        GITHUB_RUN_ID="123",
        GITHUB_RUN_ATTEMPT="1",
        GITHUB_OUTPUT=str(output),
    )
    result = subprocess.run(
        ["bash", "-c", selection["run"]], cwd=source, env=environment, capture_output=True, text=True, timeout=30
    )
    if case in {"checkout-receipt-only", "missing-receipt", "different-revision"}:
        assert result.returncode != 0
        assert not output.exists()
    else:
        assert result.returncode == 0, result.stderr
        assert output.read_text().splitlines() == [f"root={root}", f"installed_receipt={receipt}"]
