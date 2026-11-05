"""release.yml: two admitted evidence shapes, and no way to skip both.

The workflow must still show a reader that publication requires evidence. These
controls pin the two shapes, the strict hosted path being untouched, and the
absence of a skip/force input.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _workflow() -> dict:
    return yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())


def _steps() -> list[dict]:
    return _workflow()["jobs"]["release"]["steps"]


def _handoff_step() -> dict:
    return next(step for step in _steps() if step.get("id") == "acceptance")


def test_workflow_declares_both_evidence_shapes() -> None:
    """The dispatch surface names the hosted triple and the composed receipt."""
    inputs = _workflow()[True]["workflow_dispatch"]["inputs"]
    assert {"tag", "acceptance_run_id", "acceptance_artifact_id", "acceptance_receipt_sha256"} <= set(inputs)
    assert "composed_receipt" in inputs


def test_no_input_can_skip_acceptance() -> None:
    """There is no skip, force or bypass flag, and none may be added silently."""
    inputs = {name.lower() for name in _workflow()[True]["workflow_dispatch"]["inputs"]}
    for forbidden in ("skip", "force", "no_acceptance", "skip_acceptance", "bypass"):
        assert forbidden not in inputs


def test_handoff_step_passes_both_shapes_to_one_admission() -> None:
    """One admission call owns both shapes, so neither can be silently dropped."""
    step = _handoff_step()
    argv = shlex.split(step["run"])
    assert "--run-id" in argv
    assert "--artifact-id" in argv
    assert "--receipt-sha256" in argv
    assert "--composed-receipt" in argv
    assert argv.count("infrastructure.publishing.release_acceptance") == 1


def test_handoff_step_runs_before_publication() -> None:
    """The evidence gate precedes the step that creates the GitHub Release."""
    steps = _steps()
    publish = next(index for index, step in enumerate(steps) if "action-gh-release@" in step.get("uses", ""))
    handoff = next(index for index, step in enumerate(steps) if step.get("id") == "acceptance")
    assert handoff < publish, "the release must not be created before evidence is admitted"


def test_publish_step_still_succeeds_only_after_the_gate() -> None:
    """The publication action has no continue-on-error, so a refusal blocks it."""
    publish = next(step for step in _steps() if "action-gh-release@" in step.get("uses", ""))
    assert publish.get("continue-on-error", False) is False
    assert publish.get("if") is None
