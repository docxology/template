"""Tests for changed-surface test guidance."""

import subprocess

from infrastructure.core.test_impact import classify_changed_paths
from scripts.audit.test_impact import _git_changed_paths


def test_independent_public_projects_can_use_outer_parallelism() -> None:
    plan = classify_changed_paths(
        [
            "projects/templates/template_code_project/src/optimizer.py",
            "projects/templates/template_prose_project/tests/test_claims.py",
        ]
    )
    assert plan.project_names == (
        "templates/template_code_project",
        "templates/template_prose_project",
    )
    assert plan.outer_project_parallelism_allowed is True
    assert plan.recommended_lanes == (
        "project:templates/template_code_project",
        "project:templates/template_prose_project",
    )


def test_global_changes_prohibit_nested_project_parallelism() -> None:
    plan = classify_changed_paths(
        [
            "infrastructure/core/test_runner.py",
            "projects/templates/template_code_project/src/optimizer.py",
            "docs/testing.md",
        ]
    )
    assert plan.infrastructure_changed is True
    assert plan.documentation_changed is True
    assert plan.outer_project_parallelism_allowed is False
    assert plan.recommended_lanes[:2] == ("infrastructure-serial", "documentation-contract")


def test_local_only_changes_are_marked_for_private_boundary_review() -> None:
    plan = classify_changed_paths(["projects/working/private_project/src/model.py"])
    assert plan.local_only_changed is True
    assert plan.project_names == ()


def test_root_controls_and_resource_pools_get_dedicated_lanes() -> None:
    plan = classify_changed_paths(["pyproject.toml", "fonds/templates/demo/src.py"])
    assert plan.repository_control_changed is True
    assert plan.resource_pool_changed is True
    assert plan.recommended_lanes == ("repository-control", "resource-pool-contract")
    assert plan.outer_project_parallelism_allowed is False


def test_git_impact_includes_nonignored_untracked_source(tmp_path) -> None:
    """The CLI planner must see a new source file before it is staged."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=tmp_path, check=True)
    tracked = tmp_path / "README.md"
    tracked.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)

    source = tmp_path / "projects" / "templates" / "example" / "src" / "new.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")

    assert _git_changed_paths(tmp_path) == ["projects/templates/example/src/new.py"]


def test_git_impact_unions_staged_and_unstaged_paths(tmp_path) -> None:
    """The planner must cover both index and worktree changes in one run."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=tmp_path, check=True)
    staged = tmp_path / "infrastructure" / "staged.py"
    unstaged = tmp_path / "tests" / "unstaged.py"
    staged.parent.mkdir()
    unstaged.parent.mkdir()
    staged.write_text("VALUE = 1\n", encoding="utf-8")
    unstaged.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "infrastructure/staged.py", "tests/unstaged.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)

    staged.write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "infrastructure/staged.py"], cwd=tmp_path, check=True)
    unstaged.write_text("VALUE = 3\n", encoding="utf-8")

    assert _git_changed_paths(tmp_path) == ["infrastructure/staged.py", "tests/unstaged.py"]
