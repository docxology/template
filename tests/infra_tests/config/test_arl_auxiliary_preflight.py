"""The opt-in diagnostic retains the required cell's real execution contract."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
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
    assert (
        workflow["jobs"]["native-preflight"]["if"]
        == "inputs.diagnostic_arl_auxiliary != true && inputs.diagnostic_arl_readback != true"
    )
    job = workflow["jobs"]["arl-auxiliary-diagnostic"]
    assert (
        job["if"]
        == "github.event_name == 'workflow_dispatch' && inputs.diagnostic_arl_auxiliary == true && inputs.diagnostic_arl_readback != true"
    )
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


@pytest.mark.parametrize(
    ("workflow_name", "job_name", "cell"),
    [
        ("platform-native-preflight.yml", "arl-auxiliary-diagnostic", "template_advanced_literature_review"),
        ("platform-required-acceptance.yml", "auxiliary-original", "${{ matrix.cell }}"),
    ],
)
def test_auxiliary_carriers_preserve_hidden_pipeline_originals_in_the_exact_exported_cell(
    workflow_name: str, job_name: str, cell: str
) -> None:
    # The actual portable-pipeline validator reads every original output binding,
    # including .pipeline/execution.json and .checkpoints. The pinned upload
    # action omits hidden members unless this delivery option is explicit.
    job = _workflow(workflow_name)["jobs"][job_name]
    steps = job["steps"]
    upload = next(step for step in steps if step.get("name") == "Retain original auxiliary audit")
    assert upload["with"]["include-hidden-files"] is True
    assert upload["with"]["path"] == "${{ env.TEMPLATE_CI_ARTIFACT_DIRECTORY }}/auxiliary-linux/" + cell + "/"
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["if"] == "always()"
    export = next(
        step for step in steps if step.get("name") == "Export original Linux readiness bytes for the artifact reader"
    )
    assert export["if"] == "always()"
    assert "infrastructure.core.testing.ci_execution_user export" in export["run"]
    assert steps.index(export) < steps.index(upload)


def test_downloaded_original_mode_is_exclusive_same_sha_and_read_only() -> None:
    workflow = _workflow("platform-native-preflight.yml")
    trigger = workflow.get("on", workflow.get(True))
    inputs = trigger["workflow_dispatch"]["inputs"]
    assert inputs["diagnostic_arl_readback"]["default"] is False
    for key in ("arl_original_run_id", "arl_original_run_attempt", "arl_original_source_sha"):
        assert inputs[key]["type"] == "string" and inputs[key]["default"] == ""
    assert len(inputs) == 5
    job = workflow["jobs"]["arl-transport-readback"]
    assert job["if"] == "github.event_name == 'workflow_dispatch' && inputs.diagnostic_arl_readback == true"
    assert job["permissions"] == {"contents": "read", "actions": "read"}
    steps = job["steps"]
    named = {step["name"]: step for step in steps if "name" in step}
    admission = named["Admit the exclusive same-SHA readback request"]
    assert shlex.split(admission["run"]) == [
        "python3",
        "-S",
        "infrastructure/project/public_acceptance_literature_readback.py",
        "admit",
    ]
    assert steps.index(admission) < next(
        index for index, step in enumerate(steps) if step.get("uses") == "./.github/actions/setup-acceptance-fixtures"
    )
    uses = {step.get("uses", "") for step in steps}
    for action in ("setup-acceptance-fixtures", "setup-python-env", "setup-meta-provider"):
        assert "./.github/actions/" + action in uses
    assert not any("setup-acceptance-model" in action for action in uses)
    assert not any("setup-acceptance-documents" in action for action in uses)
    run = named["Authenticate and read the downloaded original"]
    assert run["env"] == {"GH_TOKEN": "${{ github.token }}"}
    assert shlex.split(run["run"]) == [
        ".venv/bin/python",
        "-I",
        "-B",
        "-m",
        "infrastructure.project.public_acceptance_literature_readback",
        "read",
    ]
    assert run.get("continue-on-error", False) is False
    checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
    assert "ref" not in checkout["with"]
    assert checkout["with"]["persist-credentials"] is False
    upload = named["Retain the downloaded-original reader"]
    assert upload["if"] == "always()" and upload["with"]["include-hidden-files"] is True
    assert upload["with"]["path"] == (
        "output/readiness/arl-transport-readback/${{ github.run_id }}-${{ github.run_attempt }}/"
    )
    assert upload["with"]["if-no-files-found"] == "error"
    commands = "\n".join(step.get("run", "") for step in steps)
    assert "public_acceptance_auxiliary_cli" not in commands
    assert "original_job_outcome" not in commands and "git push" not in commands


def test_downloaded_consumer_authenticates_the_actual_producer_step_names() -> None:
    from infrastructure.project.public_acceptance_literature_readback import _REQUIRED_STEPS

    job = _workflow("platform-native-preflight.yml")["jobs"]["arl-auxiliary-diagnostic"]
    names = [step.get("name") for step in job["steps"]]
    positions = [names.index(name) for name in _REQUIRED_STEPS]
    assert positions == sorted(positions)
    assert job["name"] == "ARL auxiliary diagnostic"
