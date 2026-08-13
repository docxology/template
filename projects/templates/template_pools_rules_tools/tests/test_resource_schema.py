"""Typed resource-manifest and evaluator negative controls."""

from pathlib import Path

import pytest

from src.resource_schema import (
    REQUIRED_MANIFEST_KEYS,
    build_resource_schema_receipt,
    validate_resource_directory,
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


def test_non_mapping_manifest_fails_closed():
    assert validate_resource_manifest(["not", "a", "mapping"], "fond") == (
        "manifest must be a mapping",
    )


def test_blank_string_fields_fail_closed():
    manifest = {
        "type": "bibliography",
        "description": "   ",
        "version": 1,
        "license": "MIT",
    }
    issues = validate_resource_manifest(manifest, "fond")
    assert "manifest description must be non-empty" in issues
    assert "manifest version must be non-empty" in issues


def test_unknown_resource_kind_fails_closed():
    manifest = {
        "type": "bibliography",
        "description": "x",
        "version": "1",
        "license": "MIT",
    }
    issues = validate_resource_manifest(manifest, "bogus")
    assert "unknown resource kind: bogus" in issues


def test_tool_manifest_requires_non_empty_type():
    manifest = {
        "type": "  ",
        "description": "x",
        "version": "1",
        "license": "MIT",
        "entrypoints": ["run.py"],
    }
    issues = validate_resource_manifest(manifest, "tools")
    assert "tool manifest type must be non-empty" in issues


def test_manifest_type_not_valid_for_kind_fails_closed():
    manifest = {
        "type": "not-a-real-fond-type",
        "description": "x",
        "version": "1",
        "license": "MIT",
    }
    issues = validate_resource_manifest(manifest, "fond")
    assert "manifest type 'not-a-real-fond-type' is not valid for fond" in issues


def test_invalid_tags_fail_closed():
    manifest = {
        "type": "bibliography",
        "description": "x",
        "version": "1",
        "license": "MIT",
        "tags": ["ok", "", 5],
    }
    issues = validate_resource_manifest(manifest, "fond")
    assert "manifest tags must be a list of non-empty strings" in issues


def test_required_manifest_keys_are_the_documented_four():
    assert REQUIRED_MANIFEST_KEYS == ("type", "description", "version", "license")


def test_validate_resource_directory_rejects_unknown_kind(tmp_path):
    issues = validate_resource_directory(tmp_path, "bogus")
    assert issues == ("unknown resource kind: bogus",)


def test_validate_resource_directory_reports_missing_manifest(tmp_path):
    issues = validate_resource_directory(tmp_path, "fond")
    assert issues == ("missing fonds.yaml",)


def test_validate_resource_directory_fails_closed_on_malformed_yaml(tmp_path):
    """Regression: malformed YAML must fail closed, never raise.

    Prior to this fix the `except` clause caught (OSError,
    UnicodeDecodeError, ValueError) but not yaml.YAMLError, so a malformed
    manifest crashed the caller instead of returning an issue tuple — a
    direct violation of AGENTS.md's Resilience Policy ("Log a warning but
    do not raise") and CLAUDE.md's invariant ("Graceful fallback
    everywhere ... they never raise").
    """
    (tmp_path / "fonds.yaml").write_text("key: [unterminated", encoding="utf-8")
    issues = validate_resource_directory(tmp_path, "fond")
    assert len(issues) == 1
    assert issues[0].startswith("cannot read fonds.yaml:")


def test_validate_resource_directory_rejects_symlinked_entrypoint(tmp_path):
    real_script = tmp_path / "real_run.py"
    real_script.write_text("print('hi')\n", encoding="utf-8")
    link = tmp_path / "run.py"
    link.symlink_to(real_script)
    (tmp_path / "tools.yaml").write_text(
        "type: code_executor\n"
        "description: x\n"
        "version: '1'\n"
        "license: MIT\n"
        "entrypoints: [run.py]\n",
        encoding="utf-8",
    )
    issues = validate_resource_directory(tmp_path, "tools")
    assert "symlinked tool entrypoint is not allowed: run.py" in issues


def test_validate_resource_directory_rejects_escaping_entrypoint(tmp_path):
    (tmp_path / "tools.yaml").write_text(
        "type: code_executor\n"
        "description: x\n"
        "version: '1'\n"
        "license: MIT\n"
        "entrypoints: ['../escape.py']\n",
        encoding="utf-8",
    )
    issues = validate_resource_directory(tmp_path, "tools")
    assert any("escapes resource root" in issue for issue in issues)


def test_validate_resource_directory_reports_missing_entrypoint_file(tmp_path):
    (tmp_path / "tools.yaml").write_text(
        "type: code_executor\n"
        "description: x\n"
        "version: '1'\n"
        "license: MIT\n"
        "entrypoints: [missing.py]\n",
        encoding="utf-8",
    )
    issues = validate_resource_directory(tmp_path, "tools")
    assert "missing tool entrypoint: missing.py" in issues


def test_build_resource_schema_receipt_is_empty_safe():
    receipt = build_resource_schema_receipt([])
    assert receipt["resource_count"] == 0
    assert receipt["status"] == "fail"
    assert receipt["resources"] == []


@pytest.mark.parametrize("resource_kind", ["fond", "rules", "tools"])
def test_validate_resource_directory_manifest_name_per_kind(tmp_path, resource_kind):
    """Each resource kind expects a differently-named manifest file."""
    issues = validate_resource_directory(tmp_path, resource_kind)
    expected_name = {"fond": "fonds.yaml", "rules": "rules.yaml", "tools": "tools.yaml"}[
        resource_kind
    ]
    assert issues == (f"missing {expected_name}",)
