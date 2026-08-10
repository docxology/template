"""Tests for changed-surface test guidance."""

from infrastructure.core.test_impact import classify_changed_paths


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
