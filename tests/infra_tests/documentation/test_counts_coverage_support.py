"""Tests for the coverage support closure and identity/workspace safeguards (split from test_counts_doc.py)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from infrastructure.documentation.counts_doc import (
    exemplar_source_hash,
)
from infrastructure.documentation.counts_coverage import (
    _COVERAGE_COPY_SUPPORT_SPECS,
    _coverage_measurement_environment,
    _coverage_measurement_workspace,
    _coverage_support_identity,
)

from tests.infra_tests.documentation._counts_doc_helpers import (
    _repo_root,
    _repo_root_anchor,
    _write_test_coverage_support_closure,
)


# Several cases create temporary Git trees and exercise subprocess-backed
# provenance discovery. They are bounded, but can exceed the repository's
# 10-second default when the complete coverage suite is under load.
pytestmark = pytest.mark.timeout(30)


def test_active_coverage_support_closure_exactly_matches_outward_documentation_links() -> None:
    import runpy

    repo_root = _repo_root()
    project = repo_root / "projects" / "templates" / "template_active_inference"
    contract = runpy.run_path(str(project / "src" / "gates" / "documentation_contract.py"))
    iter_targets = contract["_iter_markdown_targets"]
    split_target = contract["_split_link_target"]
    skip_parts = contract["SKIP_PARTS"]
    outward_targets: list[str] = []
    for path in sorted(project.rglob("*.md")):
        if any(part in skip_parts for part in path.relative_to(project).parts):
            continue
        text = path.read_text(encoding="utf-8")
        for _, raw_target in iter_targets(text):
            target, _ = split_target(raw_target)
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            candidate = (path.parent / target).resolve()
            if candidate.is_relative_to(project):
                continue
            outward_targets.append(candidate.relative_to(repo_root).as_posix())

    expected_targets = [
        "AGENTS.md",
        "docs/RUN_GUIDE.md",
        "docs/_generated/COUNTS.md",
        "docs/_generated/COUNTS.md",
        "docs/guides/manuscript-semantics.md",
        "docs/guides/publishing-guide.md",
        "docs/guides/zenodo-doi-strategy.md",
        "docs/maintenance/archival-targets.md",
        "docs/maintenance/exemplar-backlog-history.md",
        "docs/rules/memory_and_decision_records.md",
        "infrastructure/publishing/README.md",
        "projects/AGENTS.md",
        "projects/AGENTS.md",
        "projects/templates/template_code_project",
    ]
    declared_targets = {_repo_root_anchor(spec) for spec in _COVERAGE_COPY_SUPPORT_SPECS}

    assert sorted(outward_targets) == sorted(expected_targets)
    assert set(outward_targets) == declared_targets


def test_active_coverage_support_identity_binds_contract_bytes_but_not_counts_content(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_source = repo_root / "projects" / "templates" / "template_active_inference" / "src" / "demo.py"
    project_source.parent.mkdir(parents=True)
    project_source.write_text("VALUE = 1\n", encoding="utf-8")
    _write_test_coverage_support_closure(repo_root)
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)

    before_identity = _coverage_support_identity(repo_root)
    before_source_hash = exemplar_source_hash(repo_root, "template_active_inference")
    counts = repo_root / "docs" / "_generated" / "COUNTS.md"
    counts.write_text("generated counts may refresh\n", encoding="utf-8")
    assert _coverage_support_identity(repo_root) == before_identity
    assert exemplar_source_hash(repo_root, "template_active_inference") == before_source_hash

    projects_agents = repo_root / "projects" / "AGENTS.md"
    projects_agents.write_text("# Changed anchor-bearing contract\n", encoding="utf-8")
    assert _coverage_support_identity(repo_root) != before_identity
    assert exemplar_source_hash(repo_root, "template_active_inference") != before_source_hash


def test_active_coverage_support_identity_rejects_missing_or_wrong_type(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_test_coverage_support_closure(repo_root)
    counts = repo_root / "docs" / "_generated" / "COUNTS.md"
    counts.unlink()
    with pytest.raises(RuntimeError, match="support path is unavailable"):
        _coverage_support_identity(repo_root)

    counts.write_text("restored\n", encoding="utf-8")
    code_project = repo_root / "projects" / "templates" / "template_code_project"
    code_project.rmdir()
    code_project.write_text("not a directory\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not a real directory"):
        _coverage_support_identity(repo_root)


def test_active_coverage_workspace_rejects_symlinked_support_without_touching_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project_source = repo_root / "projects" / "templates" / "template_active_inference" / "src" / "demo.py"
    project_source.parent.mkdir(parents=True)
    project_source.write_text("VALUE = 1\n", encoding="utf-8")
    _write_test_coverage_support_closure(repo_root)
    external = tmp_path / "external-agents.md"
    external.write_text("EXTERNAL\n", encoding="utf-8")
    projects_agents = repo_root / "projects" / "AGENTS.md"
    projects_agents.unlink()
    try:
        projects_agents.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RuntimeError, match="support path cannot contain a symlink"):
        with _coverage_measurement_workspace(repo_root, "template_active_inference"):
            pass

    assert external.read_text(encoding="utf-8") == "EXTERNAL\n"


def test_active_coverage_workspace_preserves_canonical_semantic_readiness(tmp_path: Path) -> None:
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    repo_root = _repo_root()
    canonical = repo_root / "projects" / "templates" / "template_active_inference"
    probe = (
        "import json; "
        "from gates.documentation_contract import check_documentation_contract; "
        "from manuscript.sheaf.semantic import semantic_gluing_issues; "
        "from roadmap_tracks.sheaf_track_validation import validate_sheaf_track_artifacts; "
        "from pathlib import Path; "
        "root=Path.cwd(); "
        "print(json.dumps({'documentation': [issue.format() for issue in check_documentation_contract(root)], "
        "'semantic': semantic_gluing_issues(root), "
        "'sheaf': validate_sheaf_track_artifacts(root)}, sort_keys=True))"
    )

    with _coverage_measurement_workspace(repo_root, "template_active_inference") as (_, disposable):
        result = run_with_policy(
            (
                "uv",
                "run",
                "--locked",
                "--project",
                str(canonical),
                "--directory",
                str(disposable),
                "--extra",
                "dev",
                "python",
                "-c",
                probe,
            ),
            cwd=repo_root,
            env=_coverage_measurement_environment(tmp_path / ".coverage.readiness-probe"),
            policy=SubprocessPolicy(
                policy_id="coverage-copy-readiness-probe",
                source_path="infrastructure/documentation/counts_coverage.py",
                timeout_seconds=30,
            ),
        )

    assert result.returncode == 0, result.stderr
    assert result.timed_out is False
    assert not result.command_error
    assert json.loads(result.stdout.splitlines()[-1]) == {
        "documentation": [],
        "semantic": [],
        "sheaf": [],
    }


def test_active_coverage_workspace_passes_documentation_and_inventory_nodes(tmp_path: Path) -> None:
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

    repo_root = _repo_root()
    canonical = repo_root / "projects" / "templates" / "template_active_inference"
    nodes = (
        "tests/test_documentation_contracts.py::test_rendering_reproducibility_reference_is_signposted",
        "tests/test_documentation_contracts.py::test_documentation_contract_cli",
        "tests/test_method_inventory.py::test_method_inventory_check_command",
    )

    with _coverage_measurement_workspace(repo_root, "template_active_inference") as (_, disposable):
        result = run_with_policy(
            (
                "uv",
                "run",
                "--locked",
                "--project",
                str(canonical),
                "--directory",
                str(disposable),
                "--extra",
                "dev",
                "pytest",
                "-q",
                "--no-cov",
                *nodes,
            ),
            cwd=repo_root,
            env=_coverage_measurement_environment(tmp_path / ".coverage.documentation-probe"),
            policy=SubprocessPolicy(
                policy_id="coverage-copy-documentation-probe",
                source_path="infrastructure/documentation/counts_coverage.py",
                timeout_seconds=30,
            ),
        )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.timed_out is False
    assert not result.command_error
    assert "3 passed" in result.stdout


def test_active_coverage_workspace_rejects_project_symlink_without_touching_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    project = repo_root / "projects" / "templates" / "template_active_inference"
    source = project / "src"
    source.mkdir(parents=True)
    external = tmp_path / "external.txt"
    external.write_bytes(b"EXTERNAL\n")
    try:
        (source / "external-link").symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RuntimeError, match="copy refuses symlink"):
        with _coverage_measurement_workspace(repo_root, "template_active_inference"):
            pass

    assert external.read_bytes() == b"EXTERNAL\n"


@pytest.mark.parametrize("symlinked_component", ("projects", "templates", "template_active_inference"))
def test_active_coverage_workspace_rejects_symlinked_path_component_without_touching_target(
    tmp_path: Path,
    symlinked_component: str,
) -> None:
    repo_root = tmp_path / "repo"
    external = tmp_path / f"external-{symlinked_component}"
    project_name = "template_active_inference"
    if symlinked_component == "projects":
        repo_root.mkdir()
        external_project = external / "templates" / project_name
        link = repo_root / "projects"
    elif symlinked_component == "templates":
        (repo_root / "projects").mkdir(parents=True)
        external_project = external / project_name
        link = repo_root / "projects" / "templates"
    else:
        (repo_root / "projects" / "templates").mkdir(parents=True)
        external_project = external
        link = repo_root / "projects" / "templates" / project_name
    sentinel = external_project / "src" / "sentinel.py"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"EXTERNAL-SOURCE\n")
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    with pytest.raises(RuntimeError, match="path component cannot be a symlink"):
        with _coverage_measurement_workspace(repo_root, project_name):
            pass

    assert sentinel.read_bytes() == b"EXTERNAL-SOURCE\n"
