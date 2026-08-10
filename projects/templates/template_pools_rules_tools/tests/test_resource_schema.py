"""Typed resource-manifest and evaluator negative controls."""

from pathlib import Path

from src.resource_schema import (
    build_resource_schema_receipt,
    validate_resource_manifest,
)

PROJECT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT.parents[2]


def test_public_resource_manifests_have_a_passing_receipt():
    resources = [
        ("bibliography", REPO_ROOT / "fonds" / "templates" / "template_bibliography", "fond"),
        ("contacts", REPO_ROOT / "fonds" / "templates" / "template_contacts", "fond"),
        ("datasets", REPO_ROOT / "fonds" / "templates" / "template_datasets", "fond"),
        ("project-rules", REPO_ROOT / "rules" / "templates" / "template_project_rules", "rules"),
        (
            "manuscript-rules",
            REPO_ROOT / "rules" / "templates" / "template_manuscript_rules",
            "rules",
        ),
        ("code-executor", REPO_ROOT / "tools" / "templates" / "template_code_executor", "tools"),
    ]
    receipt = build_resource_schema_receipt(resources)
    assert receipt["status"] == "pass"
    assert receipt["resource_count"] == len(resources)


def test_manifest_missing_required_field_fails_closed():
    issues = validate_resource_manifest({"type": "bibliography", "description": "x"}, "fond")
    assert "missing required manifest key: version" in issues
    assert "missing required manifest key: license" in issues


def test_tool_entrypoints_are_required_and_typed():
    issues = validate_resource_manifest(
        {
            "type": "code_executor",
            "description": "x",
            "version": "1",
            "license": "MIT",
            "entrypoints": [],
        },
        "tools",
    )
    assert "tool manifest entrypoints must be a non-empty string list" in issues
