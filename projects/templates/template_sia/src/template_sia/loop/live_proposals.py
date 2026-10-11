"""Actual Ollama numeric proposals, Docker evaluation, and byte-verified rollback.

The proposer selects thresholds on public cases only. The frozen holdout is
evaluated once after selection; no holdout cases or scores enter prompts.
Repository source is never modified and production application is unsupported.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import proposal_transport
from .approval import ApprovalContract
from .proposal_domain import (
    LiveCapabilityBlocked,
    LiveProposalFailed,
    mutate_threshold,
    public_prompt,
    read_dataset_bytes,
    score_predictions,
    threshold_assignment,
    validated_threshold,
)
from .proposal_sandbox import command, require_docker_image, run_target

SCHEMA_VERSION = "template-sia/numeric-proposal-receipt/1"


@dataclass(frozen=True)
class ProposalSettings:
    """Explicit opt-in live limits; fixture/reference execution is separate."""

    model: str
    image_id: str
    endpoint: str = "http://127.0.0.1:11434"
    max_generations: int = 3
    target_timeout_sec: int = 60
    run_timeout_sec: int = 600

    def __post_init__(self) -> None:
        if type(self.max_generations) is not int or not 2 <= self.max_generations <= 3:
            raise ValueError("live numeric proposal lane requires 2–3 total generations")
        if type(self.target_timeout_sec) is not int or not 1 <= self.target_timeout_sec <= 60:
            raise ValueError("live target timeout must be in [1,60] seconds")
        if type(self.run_timeout_sec) is not int or not 1 <= self.run_timeout_sec <= 600:
            raise ValueError("live run timeout must be an integer in [1,600] seconds")


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _same_bytes(path: Path, expected: bytes) -> bool:
    try:
        return path.read_bytes() == expected
    except OSError:
        return False


def _json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def request_proposal(settings: ProposalSettings, prompt: str, directory: Path, timeout: int = 60) -> tuple[float, str]:
    """Supervise one real local model request with a total wall-clock deadline."""
    request_path, response_path = directory / "model_request.json", directory / "model_response.json"
    _json(
        request_path,
        {
            "model": settings.model,
            "prompt": prompt,
            "format": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                    "rationale": {"type": "string", "minLength": 1, "maxLength": 2048},
                },
                "required": ["threshold", "rationale"],
                "additionalProperties": False,
            },
            "stream": False,
            "options": {"temperature": 0, "seed": 20260930, "num_predict": 512},
        },
    )
    proc = command(
        [
            sys.executable,
            str(Path(proposal_transport.__file__).resolve()),
            "--endpoint",
            settings.endpoint,
            "--request",
            str(request_path),
            "--response",
            str(response_path),
        ],
        directory,
        timeout,
    )
    _json(
        directory / "model_execution.json",
        {
            "returncode": proc.returncode,
            "timed_out": proc.timed_out,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "deadline_sec": timeout,
        },
    )
    if proc.timed_out or proc.returncode == 75:
        raise LiveCapabilityBlocked(
            f"selected local Ollama model is unavailable or exceeded its {timeout}-second deadline"
        )
    if proc.returncode or not response_path.is_file():
        raise LiveProposalFailed("local model response failed; model_execution.json retains diagnostics")
    try:
        raw = json.loads(response_path.read_text(encoding="utf-8"))
        candidate = json.loads(raw.get("response", ""))
    except (ValueError, AttributeError, TypeError) as exc:
        raise LiveProposalFailed("model returned malformed proposal JSON") from exc
    if not isinstance(candidate, dict) or set(candidate) != {"threshold", "rationale"}:
        raise LiveProposalFailed("proposal must contain exactly threshold and rationale; code/paths are forbidden")
    try:
        threshold = validated_threshold(candidate["threshold"])
    except ValueError as exc:
        raise LiveProposalFailed(str(exc)) from exc
    rationale = candidate["rationale"]
    if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 2048:
        raise LiveProposalFailed("proposal requires a bounded nonempty rationale")
    return threshold, rationale


def run_live_proposals(project_root: Path, output_dir: Path, settings: ProposalSettings) -> Path:
    """Keep/reject sandbox mutations, evaluate a frozen holdout, and retain failure receipts."""
    project_root, output_dir = project_root.resolve(), output_dir.resolve()
    if not output_dir.is_relative_to(project_root / "output"):
        raise ValueError("live proposal output must be confined to the project's ignored output tree")
    if output_dir.exists():
        raise ValueError("live proposal output already exists; select a fresh run directory")
    output_dir.mkdir(parents=True)
    started = time.monotonic()
    deadline = started + settings.run_timeout_sec

    def bounded_timeout(requested: int, *, cleanup_reserve: int = 30) -> int:
        available = int(deadline - time.monotonic()) - cleanup_reserve
        if available < 1:
            raise LiveCapabilityBlocked("live run deadline exhausted; container cleanup allowance is reserved")
        return min(requested, available)

    receipt_path = output_dir / "live_proposal_receipt.json"
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "incomplete",
        "execution_mode": "ollama_docker_numeric_proposals",
        "mutation_scope": "one finite THRESHOLD literal in fixed reference code",
        "production_source_applied": False,
        "owner_approval_required_for_source_apply": True,
        "model": settings.model,
        "image_id": settings.image_id,
        "max_generations": settings.max_generations,
        "run_deadline_sec": settings.run_timeout_sec,
        "target_deadline_sec": settings.target_timeout_sec,
        "container_cleanup_allowance_sec": 30,
        "generations": [],
        "holdout_used_for_selection": False,
        "rollback_verified": False,
    }
    baseline_path = project_root / "tasks/mini_classify/reference/reference_target_agent.py"
    public_path = project_root / "tasks/mini_classify/data/public/train.csv"
    holdout_path = project_root / "tasks/mini_classify/data/private/proposal_holdout.csv"
    workspace = output_dir / "sandbox_target.py"
    baseline: bytes | None = None
    public_bytes: bytes | None = None
    holdout_bytes: bytes | None = None
    _json(receipt_path, receipt)
    try:
        if not settings.model.strip():
            raise LiveCapabilityBlocked("an explicitly selected local Ollama model is required")
        docker = require_docker_image(settings.image_id, output_dir, timeout=bounded_timeout(15, cleanup_reserve=45))
        baseline = baseline_path.read_bytes()
        public_bytes, holdout_bytes = public_path.read_bytes(), holdout_path.read_bytes()
        source = baseline.decode("utf-8")
        threshold = validated_threshold(threshold_assignment(source).value)
        public_rows = read_dataset_bytes(public_bytes)
        workspace.write_bytes(baseline)
        inputs = {
            "reference_sha256": _hash(baseline),
            "public_sha256": _hash(public_bytes),
            "holdout_sha256": _hash(holdout_bytes),
        }
        receipt["inputs"] = inputs
        _json(receipt_path, receipt)
        baseline_dir = output_dir / "gen_1"
        score = score_predictions(
            public_rows,
            run_target(
                docker,
                settings.image_id,
                source,
                public_rows,
                baseline_dir,
                bounded_timeout(settings.target_timeout_sec),
            ),
        )
        receipt["generations"].append(
            {
                "generation": 1,
                "threshold": threshold,
                "public_accuracy": score,
                "source_sha256": _hash(baseline),
                "selection": "baseline",
            }
        )
        _json(receipt_path, receipt)
        mutation_count = 0
        for generation in range(2, settings.max_generations + 1):
            if (
                baseline_path.read_bytes() != baseline
                or public_path.read_bytes() != public_bytes
                or holdout_path.read_bytes() != holdout_bytes
            ):
                raise LiveProposalFailed("source or frozen dataset changed during proposal execution")
            directory = output_dir / f"gen_{generation}"
            directory.mkdir()
            proposal, rationale = request_proposal(
                settings, public_prompt(public_rows, threshold, score), directory, bounded_timeout(60)
            )
            identity = json.loads((directory / "model_identity.json").read_text(encoding="utf-8"))
            digest = identity["before_sha256"]
            if "model_sha256" in receipt and receipt["model_sha256"] != digest:
                raise LiveProposalFailed("selected installed model digest changed between proposals")
            receipt["model_sha256"] = digest
            before = workspace.read_bytes()
            candidate = mutate_threshold(source, proposal)
            diff = "".join(
                difflib.unified_diff(
                    source.splitlines(keepends=True),
                    candidate.splitlines(keepends=True),
                    fromfile="target.py",
                    tofile="target.py",
                )
            )
            (directory / "proposal.diff").write_text(diff, encoding="utf-8")
            (directory / "rollback_target.py").write_bytes(before)
            (directory / "target_agent.py").write_text(candidate, encoding="utf-8")
            approval = ApprovalContract(
                mode="live_proposal",
                sandbox_root=str(output_dir),
                diff_sha256=_hash(diff.encode("utf-8")),
                rollback_sha256=_hash(before),
                approval_status="pending",
            )
            if approval.validate():
                raise LiveProposalFailed("generated proposal approval evidence is invalid")
            approval_receipt = {
                **approval.to_dict(),
                "rollback_verified": False,
                "production_apply_permitted": False,
            }
            _json(directory / "approval_receipt.json", approval_receipt)
            workspace.write_text(candidate, encoding="utf-8")
            try:
                proposal_score = score_predictions(
                    public_rows,
                    run_target(
                        docker,
                        settings.image_id,
                        candidate,
                        public_rows,
                        directory,
                        bounded_timeout(settings.target_timeout_sec),
                    ),
                )
            finally:
                workspace.write_bytes(before)
                approval_receipt["rollback_verified"] = workspace.read_bytes() == before
                _json(directory / "approval_receipt.json", approval_receipt)
                if workspace.read_bytes() != before:
                    raise LiveProposalFailed("candidate rollback did not restore exact prior bytes")
            changed = candidate.encode("utf-8") != before
            mutation_count += int(changed)
            keep = changed and proposal_score > score
            receipt["generations"].append(
                {
                    "generation": generation,
                    "threshold": proposal,
                    "rationale": rationale,
                    "public_accuracy": proposal_score,
                    "selection": "keep_in_sandbox" if keep else "reject_no_improvement",
                    "diff_sha256": _hash(diff.encode("utf-8")),
                    "rollback_sha256": _hash(before),
                    "rollback_verified": True,
                    "mutation_applied_in_sandbox": changed,
                }
            )
            if keep:
                source, threshold, score = candidate, proposal, proposal_score
                workspace.write_text(source, encoding="utf-8")
            _json(receipt_path, receipt)
        if not mutation_count:
            raise LiveProposalFailed(
                "no distinct numeric mutation was proposed; live mutation acceptance is incomplete"
            )
        if (
            baseline_path.read_bytes() != baseline
            or public_path.read_bytes() != public_bytes
            or holdout_path.read_bytes() != holdout_bytes
        ):
            raise LiveProposalFailed("source or frozen dataset changed before final held-out scoring")
        holdout = read_dataset_bytes(holdout_bytes)
        if {row["id"] for row in holdout} & {row["id"] for row in public_rows}:
            raise LiveProposalFailed("held-out cases overlap the public selection dataset")
        holdout_score = score_predictions(
            holdout,
            run_target(
                docker,
                settings.image_id,
                source,
                holdout,
                output_dir / "heldout",
                bounded_timeout(settings.target_timeout_sec),
            ),
        )
        (output_dir / "selected_target.py").write_text(source, encoding="utf-8")
        receipt.update(
            status="passed",
            selected_threshold=threshold,
            public_accuracy=score,
            heldout_accuracy=holdout_score,
            heldout_cases=len(holdout),
            mutation_count=mutation_count,
        )
    except LiveCapabilityBlocked as exc:
        receipt.update(status="blocked", diagnostic=str(exc))
        raise
    except (OSError, ValueError, LiveProposalFailed) as exc:
        receipt.update(status="failed", diagnostic=str(exc))
        raise
    finally:
        receipt["elapsed_sec"] = time.monotonic() - started
        if baseline is not None:
            workspace.write_bytes(baseline)
            receipt["rollback_verified"] = _same_bytes(workspace, baseline) and _same_bytes(baseline_path, baseline)
            receipt["frozen_inputs_verified"] = (
                public_bytes is not None
                and holdout_bytes is not None
                and _same_bytes(public_path, public_bytes)
                and _same_bytes(holdout_path, holdout_bytes)
            )
            if receipt["status"] == "passed" and (
                not receipt["rollback_verified"] or not receipt["frozen_inputs_verified"]
            ):
                receipt.update(status="failed", diagnostic="final rollback/source/frozen-input identity failed")
        _json(receipt_path, receipt)
    if receipt["status"] != "passed":
        raise LiveProposalFailed("final source/rollback contract failed")
    return receipt_path
