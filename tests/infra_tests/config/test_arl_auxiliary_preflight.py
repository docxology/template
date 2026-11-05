"""The opt-in diagnostic retains the required cell's real execution contract."""

from __future__ import annotations

import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _workflow(name: str) -> dict:
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def test_diagnostic_selection_keeps_native_pr_behavior_and_read_only_credentials() -> None:
    workflow = _workflow("platform-native-preflight.yml")
    trigger = workflow.get("on", workflow.get(True))
    assert trigger["workflow_dispatch"]["inputs"]["diagnostic_arl_auxiliary"]["default"] is False
    assert trigger["pull_request"]["branches"] == ["main"]
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["native-preflight"]["if"] == "inputs.diagnostic_arl_auxiliary != true"
    job = workflow["jobs"]["arl-auxiliary-diagnostic"]
    assert job["if"] == "github.event_name == 'workflow_dispatch' && inputs.diagnostic_arl_auxiliary == true"
    assert job.get("permissions", workflow["permissions"]) == {"contents": "read"}
    checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["persist-credentials"] is False
    assert checkout["with"]["submodules"] is True
    assert "env" not in job or not any("runner." in str(value) for value in job["env"].values())


def test_diagnostic_executes_the_complete_original_cell_then_a_strict_fresh_consumer() -> None:
    job = _workflow("platform-native-preflight.yml")["jobs"]["arl-auxiliary-diagnostic"]
    steps = {step["name"]: step for step in job["steps"] if "name" in step}
    original = steps["Complete source-owned auxiliary project selection"]
    assert original.get("continue-on-error", False) is False
    command = shlex.split(original["run"])
    assert command[:3] == [".venv/bin/python", "-m", "infrastructure.core.testing.ci_execution_user"]
    assert (
        "--matrix-cell" in command
        and command[command.index("--matrix-cell") + 1] == "template_advanced_literature_review"
    )
    assert command[command.index("--auxiliary-workers") + 1] == "1"
    assert command[command.index("--timeout-seconds") + 1] == "1800"
    assert command[command.index("--local-model") + 1] == "smollm2:360m"
    assert "--gate" not in command and "--all" not in command
    consumer = steps["Independently read every original ARL gate and its complete group"]
    assert consumer["if"] == "always()"
    assert consumer.get("continue-on-error", False) is False
    assert "public_acceptance_literature_group_cli" in consumer["run"]
    assert "original_job_outcome" not in consumer["run"]
    names = [step.get("name") for step in job["steps"]]
    assert (
        names.index(original["name"]) < names.index(consumer["name"]) < names.index("Retain original auxiliary audit")
    )
    upload = steps["Retain original auxiliary audit"]
    assert upload["if"] == "always()"
    assert upload["with"]["name"].startswith("auxiliary-preflight-arl-")
    assert upload["with"]["retention-days"] == 30
    assert (
        "same-SHA required acceptance remains mandatory" in steps["State the selected-cell diagnostic boundary"]["run"]
    )


def test_diagnostic_uses_the_existing_genuine_preparation_and_owned_model_cleanup() -> None:
    required = _workflow("platform-required-acceptance.yml")["jobs"]["auxiliary-original"]
    diagnostic = _workflow("platform-native-preflight.yml")["jobs"]["arl-auxiliary-diagnostic"]
    uses = [step.get("uses") for step in diagnostic["steps"]]
    for action in [
        "setup-acceptance-fixtures",
        "setup-python-env",
        "setup-meta-provider",
        "setup-docs-lint",
        "setup-acceptance-documents",
        "setup-acceptance-model",
        "setup-ci-execution-user",
    ]:
        assert "./.github/actions/" + action in uses
    names = [step.get("name") for step in diagnostic["steps"]]
    cleanup = "Stop only the owned model daemon and descendants"
    original_cleanup = next(step for step in required["steps"] if step.get("name") == cleanup)
    diagnostic_cleanup = next(step for step in diagnostic["steps"] if step.get("name") == cleanup)
    assert diagnostic_cleanup == original_cleanup
    assert names.index(cleanup) < names.index("Export original Linux readiness bytes for the artifact reader")
    all_commands = "\n".join(step.get("run", "") for step in diagnostic["steps"])
    assert "git push" not in all_commands
    assert "release.yml" not in all_commands
    assert "required_acceptance_aggregate" not in all_commands
