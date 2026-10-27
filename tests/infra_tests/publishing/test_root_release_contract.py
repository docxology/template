"""Root release version and target-boundary contracts."""

from __future__ import annotations

from pathlib import Path

import shlex

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


def test_cli_fails_closed_for_exemplar_shaped_tag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_pyproject(tmp_path)

    assert main(["--repo-root", str(tmp_path), "--tag", "v1.0.1"]) == 2
    assert "root release contract failed" in capsys.readouterr().out


def test_cli_reports_matching_root_version(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_pyproject(tmp_path)

    assert main(["--repo-root", str(tmp_path), "--tag", "v3.5.1"]) == 0
    assert capsys.readouterr().out == "root release contract passed: v3.5.1\n"


def test_root_release_workflow_invokes_version_contract() -> None:
    import yaml

    workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    steps = yaml.safe_load(workflow)["jobs"]["release"]["steps"]
    audit_index, audit = next(
        (index, step)
        for index, step in enumerate(steps)
        if step.get("name") == "Verify pristine published public exemplars"
    )
    assert shlex.split(audit["run"]) == [
        "uv",
        "run",
        "--no-sync",
        "--offline",
        "python",
        "-m",
        "infrastructure.validation.cli",
        "publication-audit",
        "--repo-root",
        "$GITHUB_WORKSPACE",
        "--all-public",
        "--strict",
        "--rendered",
        "--format",
        "json",
    ]
    assert "if" not in audit
    assert not audit.get("continue-on-error", False)
    assert "Verify root package release contract" in workflow
    assert 'python -m infrastructure.publishing.root_release_contract --tag "$TAG"' in workflow
    assert "ref: ${{ steps.tag.outputs.name }}" in workflow
    assert 'EXPECTED=$(git rev-parse "refs/tags/$TAG^{commit}")' in workflow
    assert 'if [ "$ACTUAL" != "$EXPECTED" ]; then' in workflow
    assert "python scripts/gates/public_capabilities.py" in workflow
    assert "python scripts/gates/installed_public.py" in workflow
    assert workflow.index("Determine tag name") < workflow.index("uses: actions/checkout@")
    names = {step.get("name"): index for index, step in enumerate(steps)}
    assert (
        names["Verify checkout is the requested tag"]
        < audit_index
        < names["Require explicit root 4+ acceptance handoff"]
        < names["Verify complete authenticated candidate with independently installed current providers"]
        < names["Verify root package release contract"]
        < names["Verify public capability manifest"]
        < names["Verify complete installed-wheel matrix"]
        < names["Admit the exact installed wheel and final source distribution"]
    )
    distribution = steps[names["Admit the exact installed wheel and final source distribution"]]
    assert "uv build" in distribution["run"]


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


def test_release_installed_matrix_prepares_all_supported_runtimes() -> None:
    """Publication cannot substitute a source-path import or diagnostic subset."""
    import yaml

    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["release"]["steps"]
    selected = {
        step.get("with", {}).get("python-version") for step in steps if "actions/setup-python@" in step.get("uses", "")
    }
    assert selected == {"3.14", "3.15", "3.14.4"}
    matrix = next(step for step in steps if step.get("name") == "Verify complete installed-wheel matrix")
    assert matrix["if"] == "steps.acceptance.outputs.required != 'true'"
    command = matrix["run"]
    assert "--project " not in command
    assert "--project-workers 1" in command
    assert "--timeout 600" in command
    assert "--no-sync --offline" in command
    for minor in ("3.14", "3.15"):
        assert f'--python "{minor}=' in command
    preparation = next(step for step in steps if step.get("name") == "Prepare locked installed-matrix dependency cache")
    assert preparation["if"] == matrix["if"]
    assert "infrastructure.project.public_scope project-names" in preparation["run"]
    for flag in ("--locked", "--no-emit-project", "--no-emit-local", "--require-hashes", "--no-build"):
        assert flag in preparation["run"]
    policy = next(step for step in steps if step.get("name") == "Bind tagged candidate build policy")
    assert 'git -C "$GITHUB_WORKSPACE" show -s --format=%ct "$candidate"' in policy["run"]
    assert "TEMPLATE_BUILD_EPOCH_SOURCE=git:$candidate" in policy["run"]


def test_release_serializes_selected_tag_across_trigger_refs() -> None:
    """Tag push and dispatch branches must share one publication lock."""
    import yaml

    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    concurrency = workflow["concurrency"]
    assert concurrency["group"] == "release-${{ inputs.tag || github.ref_name }}"
    assert concurrency["cancel-in-progress"] is False
    steps = workflow["jobs"]["release"]["steps"]
    selection = next(step for step in steps if step.get("id") == "tag")
    assert selection["env"]["INPUT_TAG"] == "${{ inputs.tag }}"
    assert selection["env"]["REF_NAME"] == "${{ github.ref_name }}"


@pytest.mark.parametrize("case", ["accepted", "legacy", "missing-receipt", "different-revision"])
def test_release_publication_inputs_use_exact_handoff_or_legacy_matrix(tmp_path: Path, case: str) -> None:
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
    root = source if case == "legacy" else mirror
    relative = (
        "output/readiness/installed-release-123-1/receipt.json"
        if case == "legacy"
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
        REQUIRED_ACCEPTANCE="false" if case == "legacy" else "true",
        GITHUB_WORKSPACE=str(source),
        RUNNER_TEMP=str(temporary),
        GITHUB_RUN_ID="123",
        GITHUB_RUN_ATTEMPT="1",
        GITHUB_OUTPUT=str(output),
    )
    result = subprocess.run(
        ["bash", "-c", selection["run"]], cwd=source, env=environment, capture_output=True, text=True, timeout=30
    )
    if case in {"missing-receipt", "different-revision"}:
        assert result.returncode != 0
        assert not output.exists()
    else:
        assert result.returncode == 0, result.stderr
        assert output.read_text().splitlines() == [f"root={root}", f"installed_receipt={receipt}"]
