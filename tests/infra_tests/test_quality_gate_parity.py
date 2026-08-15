"""Bind high-value quality gates across CI, health, and pre-push."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from infrastructure.core.health import build_gate_specs

REPO_ROOT = Path(__file__).resolve().parents[2]


def _local_hooks() -> dict[str, dict[str, object]]:
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hooks: dict[str, dict[str, object]] = {}
    for repo in config["repos"]:
        if repo["repo"] != "local":
            continue
        hooks.update({hook["id"]: hook for hook in repo["hooks"]})
    return hooks


def _hook_command(hook: dict[str, object]) -> str:
    return " ".join(str(arg) for arg in hook["args"])


def test_health_registry_carries_cross_surface_gates() -> None:
    specs = dict(build_gate_specs(REPO_ROOT))

    assert specs["semantic-standins"][-3:] == [
        "--inventory",
        "--max-dependency-replacements",
        "0",
    ]
    assert specs["operations-manifest"][-1] == "operations-check"
    assert specs["skill-reachability"][-1] == "scripts/gates/skill_reachability_check.py"
    for gate in ("api-reference", "exemplar-roster", "counts", "publication-records"):
        assert "--check" in specs[gate]


def test_ci_workflow_carries_cross_surface_gates() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    required_commands = (
        "scripts/audit/verify_no_mocks.py\n          --inventory --max-dependency-replacements 0",
        "python -m infrastructure.skills operations-check",
        "scripts/gates/skill_reachability_check.py",
        "scripts/docgen/api_reference.py --check",
        "scripts/docgen/exemplar_roster.py --check",
        "scripts/docgen/counts.py --check",
        "scripts/docgen/publication_records.py --check",
    )
    for command in required_commands:
        assert command in workflow


def test_ci_public_matrix_uses_current_stage_cli_contract() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "--project-only --all-projects --public-projects" in workflow
    assert "--project-workers 2" in workflow
    assert "--public-scope" not in workflow
    assert "--workers 2" not in workflow


def test_pre_push_carries_cross_surface_gates() -> None:
    hooks = _local_hooks()
    quick = _hook_command(hooks["pre-push-quick"])
    docs = _hook_command(hooks["docs-contract-guard"])
    reachability = hooks["skill-reachability-check"]

    assert "--inventory --max-dependency-replacements 0" in quick
    assert "pre-push" in reachability["stages"]
    assert "pre-push" in hooks["operations-check"]["stages"]
    for command in (
        "scripts/docgen/api_reference.py --check",
        "scripts/docgen/exemplar_roster.py --check",
        "scripts/docgen/counts.py --check",
        "scripts/docgen/publication_records.py --check",
    ):
        assert command in docs


def test_large_file_hook_allows_only_named_public_arxiv_archives() -> None:
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hook = next(hook for repo in config["repos"] for hook in repo["hooks"] if hook["id"] == "check-added-large-files")
    excluded = re.compile(str(hook["exclude"]), re.VERBOSE)

    assert excluded.search("projects/templates/template_active_inference/output/arxiv_submission_20260814.tar.gz")
    assert not excluded.search("projects/templates/template_active_inference/output/arbitrary.tar.gz")
    assert not excluded.search("projects/working/private/output/arxiv_submission_20260814.tar.gz")
