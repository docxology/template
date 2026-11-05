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

import functools
import hashlib
import json
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
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

REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "output/readiness/composed-probe"


def _revision() -> str:
    observed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return observed.stdout.strip()


@functools.cache
def _profile() -> tuple[list[Any], str, str | None]:
    """Compile the required profile once; re-deriving it per test costs minutes.

    ``required_profile`` hashes the whole public source set, so it is genuinely
    expensive. The controls below vary the *receipt*, not the tree, so one
    compile is both sufficient and honest.
    """
    fingerprint = source_fingerprint(REPO_ROOT)
    stage = stage_digest(REPO_ROOT)
    if stage is None:
        # These controls build a fully-populated composed receipt, which binds a
        # scope-owned class and therefore needs a substantiable stage closure.
        # A checkout that declares `kmyth` without initializing it refuses
        # admission by design, so there is no receipt to compose. That refusal
        # is pinned in the reporting controls, which need no closure.
        pytest.skip(
            "the stage closure is unavailable in this checkout"
            f" ({unavailable_cause(REPO_ROOT)}); run"
            " `git submodule update --init infrastructure/steganography/kmyth`"
        )
    requirements, faults = required_profile(REPO_ROOT, SnapshotReader(REPO_ROOT), fingerprint)
    assert not faults, faults
    return list(requirements), fingerprint, stage


def _class_artifact(gate: str) -> Path:
    return PROBE_DIR / f"{gate.replace(':', '_').replace('/', '_')}.json"


def _composed_payload(requirements: list[Any], fingerprint: str, stage: str | None) -> dict[str, Any]:
    """Build a fully-populated composed receipt, with real producer artifacts.

    Each class artifact is written by the canonical ``gate_payload`` producer, so
    the receipt binds the same bytes a real lane would upload rather than a
    hand-shaped stand-in.
    """
    from infrastructure.project.public_acceptance_evidence import gate_payload

    revision = _revision()
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    classes: dict[str, Any] = {}
    for requirement in requirements:
        binding = class_binding(requirement, REPO_ROOT, repository_fingerprint=fingerprint, stage=stage)
        artifact = _class_artifact(requirement.id)
        artifact.write_text(
            json.dumps(
                gate_payload(
                    requirement,
                    fingerprint,
                    "pass",
                    {"declared": "composed-acceptance-probe"},
                    repository_root=REPO_ROOT,
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
            "artifact": artifact.relative_to(REPO_ROOT).as_posix(),
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


@contextmanager
def _written(payload: dict[str, Any]) -> Iterator[Path]:
    target = REPO_ROOT / COMPOSED_RECEIPT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        yield target
    finally:
        target.unlink()
        for path in PROBE_DIR.glob("*.json"):
            path.unlink()
        if PROBE_DIR.exists():
            PROBE_DIR.rmdir()


def test_hosted_carrier_always_takes_the_strict_path() -> None:
    """A supplied carrier is admitted as hosted, unchanged from today."""
    assert validate_handoff_inputs(REPO_ROOT, "123", "789", "a" * 64)


@pytest.mark.parametrize("values", [("123", "", ""), ("", "789", ""), ("", "", "a" * 64), ("123", "789", "")])
def test_partial_hosted_handoff_is_refused(values: tuple[str, str, str]) -> None:
    """A partly supplied carrier must refuse rather than fall through to composed."""
    with pytest.raises(ValueError, match="every one of run id"):
        validate_handoff_inputs(REPO_ROOT, *values, composed_receipt=COMPOSED_RECEIPT_PATH)


def test_no_handoff_at_all_is_refused() -> None:
    """Publication never proceeds without a named evidence shape."""
    with pytest.raises(MissingAcceptanceHandoff):
        validate_handoff_inputs(REPO_ROOT, "", "", "")


def test_a_composed_receipt_refuses_when_a_hosted_origin_cannot_be_resolved() -> None:
    """Control: a receipt naming hosted classes is unverifiable without auth.

    This checkout has no token, so the hosted run cannot be distinguished from a
    fabricated identifier. The receipt must refuse rather than read a claim as
    proof. Where auth is available the same receipt is admitted instead; that
    branch is covered by the pure-origin verdict controls below.
    """
    from infrastructure.publishing.composed_receipt import hosted_origin_resolvable

    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    with _written(payload) as target:
        if hosted_origin_resolvable(REPO_ROOT):
            assert validate_composed_receipt(REPO_ROOT, target)["source_commit"] == payload["source_commit"]
        else:
            with pytest.raises(ValueError, match="cannot be verified from this checkout"):
                validate_composed_receipt(REPO_ROOT, target)


def test_composed_receipt_with_a_missing_class_is_refused() -> None:
    """Dropping any required class must refuse, never admit a partial release."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"].pop(requirements[0].id)
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_composed_receipt_with_a_stale_commit_is_refused() -> None:
    """A receipt bound to another commit must refuse."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["source_commit"] = "0" * 40
    with _written(payload) as target:
        with pytest.raises(ValueError, match="different source commit"):
            validate_composed_receipt(REPO_ROOT, target)


@pytest.mark.parametrize("status", ["unknown", "blocked", "fail"])
def test_composed_receipt_with_a_non_pass_class_is_refused(status: str) -> None:
    """An unknown, blocked or failed class cannot compose to a release."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"][requirements[0].id]["status"] = status
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_composed_receipt_with_a_stale_closure_is_refused() -> None:
    """A class whose recorded closure no longer matches this tree must refuse."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"][requirements[0].id]["class_binding"]["sha256"] = "0" * 64
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_composed_receipt_without_a_producer_is_refused() -> None:
    """An unattributable class is not evidence."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"][requirements[0].id]["producer"] = []
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_composed_receipt_with_an_unknown_class_is_refused() -> None:
    """A receipt cannot widen the required roster."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"]["templates/template_not_public:runtime:3.14"] = payload["classes"][requirements[0].id]
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_composed_receipt_with_an_unsupported_schema_is_refused() -> None:
    """A foreign schema must refuse rather than be interpreted loosely."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["schema_version"] = "template-composed-acceptance-v0"
    with _written(payload) as target:
        with pytest.raises(ValueError, match="schema is unsupported"):
            validate_composed_receipt(REPO_ROOT, target)


def test_class_artifact_naming_another_gate_is_refused() -> None:
    """Artifacts cannot be shared across classes to satisfy two obligations."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    first, second = requirements[0].id, requirements[1].id
    payload["classes"][second]["artifact"] = payload["classes"][first]["artifact"]
    payload["classes"][second]["artifact_sha256"] = payload["classes"][first]["artifact_sha256"]
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_hosted_only_class_without_a_hosted_origin_is_refused() -> None:
    """A macOS or transfer class must name the hosted run that observed it."""
    requirements, fingerprint, stage = _profile()
    hosted = [r for r in requirements if hosted_required((r,))]
    assert hosted, "this tree must declare hosted-only classes"
    payload = _composed_payload(requirements, fingerprint, stage)
    del payload["classes"][hosted[0].id]["hosted_origin"]
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_locally_provable_class_claiming_a_hosted_origin_is_refused() -> None:
    """Local evidence cannot be laundered through an unrelated hosted run."""
    requirements, fingerprint, stage = _profile()
    local = [r for r in requirements if not hosted_required((r,))]
    assert local
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"][local[0].id]["hosted_origin"] = {
        "repository": "docxology/template",
        "run_id": "1",
        "artifact_id": "2",
        "head_sha": "0" * 40,
    }
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


@pytest.mark.parametrize(
    "origin",
    [
        {"repository": "docxology/template", "run_id": "1", "artifact_id": "2"},
        {"repository": "not a repo", "run_id": "1", "artifact_id": "2", "head_sha": "0" * 40},
        {"repository": "docxology/template", "run_id": "0", "artifact_id": "2", "head_sha": "0" * 40},
        {"repository": "docxology/template", "run_id": "1", "artifact_id": "2", "head_sha": "abc"},
    ],
)
def test_malformed_hosted_origin_is_refused(origin: dict[str, str]) -> None:
    """A hosted origin must carry exactly its four canonical identities."""
    requirements, fingerprint, stage = _profile()
    hosted = [r for r in requirements if hosted_required((r,))]
    assert hosted
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"][hosted[0].id]["hosted_origin"] = origin
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


def test_evidence_state_must_match_the_resolved_origin() -> None:
    """A receipt cannot record 'observed' for an origin that was only declared."""
    requirements, fingerprint, stage = _profile()
    hosted = [r for r in requirements if hosted_required((r,))]
    assert hosted
    payload = _composed_payload(requirements, fingerprint, stage)
    payload["classes"][hosted[0].id]["evidence_state"] = "observed"
    with _written(payload) as target:
        with pytest.raises(ValueError):
            validate_composed_receipt(REPO_ROOT, target)


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


def test_composed_receipt_binds_every_declared_public_scope() -> None:
    """The composed shape covers the real roster, not a synthetic subset."""
    requirements, fingerprint, stage = _profile()
    payload = _composed_payload(requirements, fingerprint, stage)
    try:
        scopes = {gate.split(":", 1)[0] for gate in payload["classes"]}
        assert set(PUBLIC_PROJECT_NAMES).issubset(scopes)
    finally:
        for path in PROBE_DIR.glob("*.json"):
            path.unlink()
        if PROBE_DIR.exists():
            PROBE_DIR.rmdir()
