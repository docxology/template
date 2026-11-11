"""Composed acceptance receipt: refuse missing, stale, unknown and unverifiable.

The negative controls are the point. A composed receipt may authorize a release
only when every required class is present, current, passing, bound to the exact
commit, and backed by a producer that actually observed the fact. Any other shape
refuses, and a supplied hosted carrier always takes the strict path unchanged.

Two controls exist specifically because a declared claim must never be readable
as a verified one: a fabricated origin must never be admitted, and a claimed
success whose run actually failed must be refused rather than downgraded.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.composed_receipt import (
    COMPOSED_RECEIPT_PATH,
    SCHEMA,
    _origin_verdict,
    validate_composed_receipt,
)
from infrastructure.publishing.release_acceptance import MissingAcceptanceHandoff, validate_handoff_inputs
from infrastructure.reporting.evidence_class import (
    class_binding,
    hosted_required,
    stage_digest,
    unavailable_cause,
)
from infrastructure.reporting.readiness_receipts import source_fingerprint
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.project.test_public_reference import (
    _clone_complete_reference,
    complete_reference as complete_reference,
)


@pytest.fixture
def source_root(complete_reference: tuple[Path, str, str], tmp_path: Path) -> Path:
    """Give each receipt control its own genuine Source, Git and artifact tree."""
    return _clone_complete_reference(complete_reference, tmp_path / "source", deadline=time.monotonic() + 300)


@pytest.fixture
def handoff_root(tmp_path: Path) -> Path:
    """Input-only controls need the real version metadata, not full Source."""
    shutil.copyfile(Path(__file__).resolve().parents[3] / "pyproject.toml", tmp_path / "pyproject.toml")
    return tmp_path


def _revision(root: Path) -> str:
    observed = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return observed.stdout.strip()


def _profile(root: Path) -> tuple[list[Any], str, str]:
    """Observe the required profile and stage closure of this test's owned Source."""
    fingerprint = source_fingerprint(root)
    stage = stage_digest(root)
    assert stage is not None, (
        f"the owned complete public reference must substantiate its stage closure ({unavailable_cause(root)})"
    )
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    assert not faults, faults
    return list(requirements), fingerprint, stage


def _class_artifact(root: Path, gate: str) -> Path:
    return root / "output/readiness/composed-probe" / f"{gate.replace(':', '_').replace('/', '_')}.json"


def _composed_payload(root: Path, requirements: list[Any], fingerprint: str, stage: str) -> dict[str, Any]:
    """Serialize source-bound fixture metadata with the canonical gate producer.

    These bytes and the illustrative hosted identifiers are test controls, not
    observed producer runs or evidence that can authorize publication.
    """
    from infrastructure.project.public_acceptance_evidence import gate_payload

    revision = _revision(root)
    (root / "output/readiness/composed-probe").mkdir(parents=True, exist_ok=True)
    classes: dict[str, Any] = {}
    for requirement in requirements:
        binding = class_binding(requirement, root, repository_fingerprint=fingerprint, stage=stage)
        artifact = _class_artifact(root, requirement.id)
        artifact.write_text(
            json.dumps(
                gate_payload(
                    requirement,
                    fingerprint,
                    "pass",
                    {"declared": "composed-acceptance-probe"},
                    repository_root=root,
                    stage=stage,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        hosted = hosted_required((requirement,))
        entry: dict[str, Any] = {
            "status": "pass",
            "source_commit": revision,
            "producer": ["probe-producer"],
            "artifact": artifact.relative_to(root).as_posix(),
            "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "class_binding": binding.to_dict(),
            "evidence_state": "declared" if hosted else "observed",
        }
        if hosted:
            entry["hosted_origin"] = {
                "repository": "docxology/template",
                "run_id": "9829",
                "artifact_id": "3141",
                "head_sha": revision,
            }
        classes[requirement.id] = entry
    return {"schema_version": SCHEMA, "source_commit": revision, "classes": classes}


def _written(root: Path, payload: dict[str, Any]) -> Path:
    """Keep the receipt with its private Source until pytest removes the fixture."""
    target = root / COMPOSED_RECEIPT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target


def test_hosted_carrier_always_takes_the_strict_path(handoff_root: Path) -> None:
    """A supplied carrier is admitted as hosted, unchanged from today."""
    assert validate_handoff_inputs(handoff_root, "123", "789", "a" * 64)


@pytest.mark.parametrize("values", [("123", "", ""), ("", "789", ""), ("", "", "a" * 64), ("123", "789", "")])
def test_partial_hosted_handoff_is_refused(values: tuple[str, str, str], handoff_root: Path) -> None:
    """A partly supplied carrier must refuse rather than fall through to composed."""
    with pytest.raises(ValueError, match="every one of run id"):
        validate_handoff_inputs(handoff_root, *values, composed_receipt=COMPOSED_RECEIPT_PATH)


def test_no_handoff_at_all_is_refused(handoff_root: Path) -> None:
    """Publication never proceeds without a named evidence shape."""
    with pytest.raises(MissingAcceptanceHandoff):
        validate_handoff_inputs(handoff_root, "", "", "")


def test_a_composed_receipt_refuses_when_a_hosted_origin_cannot_be_resolved(source_root: Path) -> None:
    """An uncredentialed consumer must refuse, regardless of the caller's login."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    target = _written(source_root, payload)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "infrastructure.publishing.release_acceptance",
            "inputs",
            "--repo-root",
            str(source_root),
            "--composed-receipt",
            str(target),
        ],
        cwd=source_root,
        env={key: value for key, value in os.environ.items() if key not in {"GH_TOKEN", "GITHUB_TOKEN"}},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert "hosted classes require a resolvable hosted origin" in result.stdout


def test_composed_receipt_with_a_missing_class_is_refused(source_root: Path) -> None:
    """Dropping any required class must refuse, never admit a partial release."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"].pop(requirements[0].id)
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_composed_receipt_with_a_stale_commit_is_refused(source_root: Path) -> None:
    """A receipt bound to another commit must refuse."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["source_commit"] = "0" * 40
    target = _written(source_root, payload)
    with pytest.raises(ValueError, match="different source commit"):
        validate_composed_receipt(source_root, target)


@pytest.mark.parametrize("status", ["unknown", "blocked", "fail"])
def test_composed_receipt_with_a_non_pass_class_is_refused(status: str, source_root: Path) -> None:
    """An unknown, blocked or failed class cannot compose to a release."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"][requirements[0].id]["status"] = status
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_composed_receipt_with_a_stale_closure_is_refused(source_root: Path) -> None:
    """A class whose recorded closure no longer matches this tree must refuse."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"][requirements[0].id]["class_binding"]["sha256"] = "0" * 64
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_composed_receipt_without_a_producer_is_refused(source_root: Path) -> None:
    """An unattributable class is not evidence."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"][requirements[0].id]["producer"] = []
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_composed_receipt_with_an_unknown_class_is_refused(source_root: Path) -> None:
    """A receipt cannot widen the required roster."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"]["templates/template_not_public:runtime:3.14"] = payload["classes"][requirements[0].id]
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_composed_receipt_with_an_unsupported_schema_is_refused(source_root: Path) -> None:
    """A foreign schema must refuse rather than be interpreted loosely."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["schema_version"] = "template-composed-acceptance-v0"
    target = _written(source_root, payload)
    with pytest.raises(ValueError, match="schema is unsupported"):
        validate_composed_receipt(source_root, target)


def test_class_artifact_naming_another_gate_is_refused(source_root: Path) -> None:
    """Artifacts cannot be shared across classes to satisfy two obligations."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    first, second = requirements[0].id, requirements[1].id
    payload["classes"][second]["artifact"] = payload["classes"][first]["artifact"]
    payload["classes"][second]["artifact_sha256"] = payload["classes"][first]["artifact_sha256"]
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_hosted_only_class_without_a_hosted_origin_is_refused(source_root: Path) -> None:
    """A macOS or transfer class must name the hosted run that observed it."""
    requirements, fingerprint, stage = _profile(source_root)
    hosted = [r for r in requirements if hosted_required((r,))]
    assert hosted, "this tree must declare hosted-only classes"
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    del payload["classes"][hosted[0].id]["hosted_origin"]
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_locally_provable_class_claiming_a_hosted_origin_is_refused(source_root: Path) -> None:
    """Local evidence cannot be laundered through an unrelated hosted run."""
    requirements, fingerprint, stage = _profile(source_root)
    local = [r for r in requirements if not hosted_required((r,))]
    assert local
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"][local[0].id]["hosted_origin"] = {
        "repository": "docxology/template",
        "run_id": "1",
        "artifact_id": "2",
        "head_sha": "0" * 40,
    }
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


@pytest.mark.parametrize(
    "origin",
    [
        {"repository": "docxology/template", "run_id": "1", "artifact_id": "2"},
        {"repository": "not a repo", "run_id": "1", "artifact_id": "2", "head_sha": "0" * 40},
        {"repository": "docxology/template", "run_id": "0", "artifact_id": "2", "head_sha": "0" * 40},
        {"repository": "docxology/template", "run_id": "1", "artifact_id": "2", "head_sha": "abc"},
    ],
)
def test_malformed_hosted_origin_is_refused(origin: dict[str, str], source_root: Path) -> None:
    """A hosted origin must carry exactly its four canonical identities."""
    requirements, fingerprint, stage = _profile(source_root)
    hosted = [r for r in requirements if hosted_required((r,))]
    assert hosted
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"][hosted[0].id]["hosted_origin"] = origin
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_evidence_state_must_match_the_resolved_origin(source_root: Path) -> None:
    """A receipt cannot record 'observed' for an origin that was only declared."""
    requirements, fingerprint, stage = _profile(source_root)
    hosted = [r for r in requirements if hosted_required((r,))]
    assert hosted
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    payload["classes"][hosted[0].id]["evidence_state"] = "observed"
    target = _written(source_root, payload)
    with pytest.raises(ValueError):
        validate_composed_receipt(source_root, target)


def test_origin_verdict_refuses_a_run_that_did_not_succeed() -> None:
    """Control: a claimed success whose run concluded failure is refused, not downgraded."""
    with pytest.raises(ValueError, match="did not succeed"):
        _origin_verdict(
            {"status": "completed", "conclusion": "failure", "head_sha": "0" * 40}, expected_head_sha="0" * 40
        )
    for conclusion in ("cancelled", "timed_out", "action_required"):
        with pytest.raises(ValueError, match="did not succeed"):
            _origin_verdict(
                {"status": "completed", "conclusion": conclusion, "head_sha": "0" * 40}, expected_head_sha="0" * 40
            )


def test_origin_verdict_requires_the_exact_commit() -> None:
    """A successful run for a different commit cannot support this class."""
    with pytest.raises(ValueError, match="bound to another commit"):
        _origin_verdict(
            {"status": "completed", "conclusion": "success", "head_sha": "1" * 40}, expected_head_sha="0" * 40
        )


def test_origin_verdict_treats_an_unobservable_origin_as_declared() -> None:
    """An unresolvable observation is a claim, never proof."""
    assert _origin_verdict({"status": None, "conclusion": None}, expected_head_sha="0" * 40) == "declared"


def test_origin_verdict_refuses_a_run_that_has_not_completed() -> None:
    """A resolved run still in progress cannot have produced a claimed pass."""
    with pytest.raises(ValueError, match="is not completed"):
        _origin_verdict({"status": "in_progress", "conclusion": "", "head_sha": "0" * 40}, expected_head_sha="0" * 40)


def test_origin_verdict_accepts_a_completed_successful_run() -> None:
    """The positive side of the verdict, so the refusals above are meaningful."""
    assert (
        _origin_verdict(
            {"status": "completed", "conclusion": "success", "head_sha": "0" * 40}, expected_head_sha="0" * 40
        )
        == "observed"
    )


def test_composed_receipt_binds_every_declared_public_scope(source_root: Path) -> None:
    """The composed shape covers the real roster, not a synthetic subset."""
    requirements, fingerprint, stage = _profile(source_root)
    payload = _composed_payload(source_root, requirements, fingerprint, stage)
    scopes = {gate.split(":", 1)[0] for gate in payload["classes"]}
    assert set(PUBLIC_PROJECT_NAMES).issubset(scopes)
