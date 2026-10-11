"""Lightweight human-in-the-loop state for template pipeline runs.

The template keeps HITL deliberately explicit and file-backed. A pause writes
``output/hitl/waiting.json``; non-interactive commands append decisions to
``output/hitl/decisions.jsonl``. Resume still uses the existing checkpoint
machinery rather than introducing hidden workflow state.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.hitl_context import (
    _stage_contract_payload,
    _declared_artifact_payloads,
    _validation_status,
    _guidance_history,
    reviewed_content_digest,
)
from infrastructure.core.pipeline.hitl_storage import locked_state
from infrastructure.core.pipeline.hitl_responses import (
    AGENT_RESPONSE_ACTIONS,
    DECISION_BINDINGS,
    agent_response_schema,
    validate_agent_response_file,
)
from infrastructure.core.pipeline.types import PipelineControlConfig, StagePolicy, StageSpec
from infrastructure.core.files.secure_write import (
    atomic_write_text_confined,
    read_text_confined,
    append_text_confined,
    unlink_confined,
)


class HitlMode(str, Enum):
    """Supported lightweight intervention modes."""

    FULL_AUTO = "full-auto"
    GATE_ONLY = "gate-only"
    CHECKPOINT = "checkpoint"
    CUSTOM = "custom"


@dataclass(frozen=True)
class WaitingState:
    """Persisted state for a paused pipeline stage."""

    stage_num: int
    stage_name: str
    reason: str
    context_summary: str = ""
    timeout_seconds: int = 86400
    auto_proceed_on_timeout: bool = False
    since: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    run_id: str = ""
    plan_digest: str = ""
    stage_key: str = ""
    artifact_digest: str = ""
    input_artifacts: tuple[str, ...] = ()
    output_artifacts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        return asdict(self)


class HitlController:
    """File-backed HITL controller for one project output directory."""

    def __init__(
        self,
        *,
        project_output_dir: Path,
        mode: HitlMode | str = HitlMode.FULL_AUTO,
        control: PipelineControlConfig | None = None,
        custom_gate_stages: tuple[int, ...] = (),
        run_id: str = "",
        plan_digest: str = "",
        repo_root: Path | None = None,
        project_dir: Path | None = None,
    ) -> None:
        self.project_output_dir = project_output_dir
        self.control = control or PipelineControlConfig(hitl_mode=_coerce_mode(mode).value)
        self.mode = _coerce_mode(self.control.hitl_mode if control is not None else mode)
        self.custom_gate_stages = self.control.custom_gate_stages or custom_gate_stages
        self.hitl_dir = project_output_dir / "hitl"
        self.waiting_path = self.hitl_dir / "waiting.json"
        self.decisions_path = self.hitl_dir / "decisions.jsonl"
        self.guidance_dir = self.hitl_dir / "guidance"
        self.agent_context_path = self.hitl_dir / "agent_context.json"
        self.agent_response_schema_path = self.hitl_dir / "agent_response.schema.json"
        self.run_id = run_id
        self.plan_digest = plan_digest
        self.repo_root = repo_root
        self.source_project_dir = project_dir if project_dir is not None else project_output_dir.parent
        self._approved_stages: set[str] = set()
        self._approved_bindings: dict[str, dict[str, Any]] = {}

    @locked_state
    def decision_for_stage(self, stage_spec: StageSpec) -> str | None:
        """Find a bound, unconsumed decision for the exact reviewed inputs."""
        key = stage_spec.key or stage_spec.name
        rows = [
            row
            for row in self.history()
            if row.get("run_id") == self.run_id
            and row.get("plan_digest") == self.plan_digest
            and row.get("stage_key") == key
        ]
        consumed = {row.get("decision_id") for row in rows if row.get("action") == "consume"}
        for row in reversed(rows):
            if row.get("action") not in {"approve", "resume", "reject", "abort"} or row.get("decision_id") in consumed:
                continue
            if row.get("artifact_digest") != reviewed_content_digest(
                self.project_output_dir,
                stage_spec.contract.input_artifacts,
                self.repo_root,
                stage_spec.contract.output_artifacts,
                project_dir=self.source_project_dir,
            ):
                return None
            action = str(row["action"])
            if action == "resume" and stage_spec.policy is not None and stage_spec.policy.require_approval:
                return None
            if action in {"approve", "resume"}:
                self._append_decision(
                    action="consume",
                    stage_num=int(row["stage_num"]),
                    stage_name=stage_spec.name,
                    message="approval used once",
                    bindings=row,
                )
                self._approved_stages.add(key)
                self._approved_bindings[key] = deepcopy(row)
            return action
        return None

    def approved_binding(self, stage_spec: StageSpec) -> dict[str, Any] | None:
        """Return the original consumed authority without recomputing review bytes."""
        return deepcopy(self._approved_bindings.get(stage_spec.key or stage_spec.name))

    @locked_state
    def validate_consumed_binding(self, binding: dict[str, Any], stage_key: str) -> None:
        """Re-admit the exact consumed decision; later rejection prevents launch."""
        if (
            binding.get("run_id") != self.run_id
            or binding.get("plan_digest") != self.plan_digest
            or binding.get("stage_key") != stage_key
            or binding.get("action") not in {"approve", "resume"}
        ):
            raise ValueError("Consumed human authorization is bound to another execution")
        rows = self.history()
        matching = [row for row in rows if row.get("decision_id") == binding.get("decision_id")]
        decisions = [row for row in matching if row.get("action") in {"approve", "resume"}]
        consumes = [row for row in matching if row.get("action") == "consume"]
        if decisions != [binding] or len(consumes) != 1:
            raise ValueError("Original human authorization or its single consumption changed")
        decision_index = rows.index(decisions[0])
        if any(
            row.get("action") in {"reject", "abort"}
            and row.get("run_id") == self.run_id
            and row.get("plan_digest") == self.plan_digest
            and row.get("stage_key") == stage_key
            for row in rows[decision_index + 1 :]
        ):
            raise ValueError("A later human rejection prevents execution")

    def should_pause_before(self, stage_num: int, stage_spec: StageSpec) -> bool:
        """Return whether the run should pause before executing a stage."""
        if self._auto_proceed_timed_out_waiting_stage(stage_num, stage_spec):
            return False
        policy = self.stage_policy(stage_num)
        if (stage_spec.key or stage_spec.name) in self._approved_stages:
            return False
        if policy.pause_before:
            return True
        return policy.require_approval

    def should_pause_after(self, stage_num: int, stage_spec: StageSpec) -> bool:
        """Return whether the run should pause after a completed stage."""
        if self._auto_proceed_timed_out_waiting_stage(stage_num, stage_spec):
            return False
        policy = self.stage_policy(stage_num)
        if (stage_spec.key or stage_spec.name) in self._approved_stages:
            return False
        if policy.pause_after or policy.require_approval:
            return True
        if self.mode == HitlMode.FULL_AUTO:
            return False
        if self.mode == HitlMode.GATE_ONLY:
            return bool(stage_spec.contract.gate)
        if self.mode == HitlMode.CHECKPOINT:
            return True
        if self.mode == HitlMode.CUSTOM:
            return stage_num in set(self.custom_gate_stages)
        return False

    def stage_policy(self, stage_num: int) -> StagePolicy:
        """Return configured stage policy or default policy."""
        return self.control.stage_policies.get(stage_num, StagePolicy())

    def pause_reason(
        self,
        *,
        stage_num: int,
        stage_spec: StageSpec,
        default: str,
    ) -> str:
        """Return the persisted reason for a pause."""
        policy = self.stage_policy(stage_num)
        if policy.require_approval:
            return "approval_required"
        return stage_spec.contract.gate or default

    @locked_state
    def pause(
        self,
        *,
        stage_num: int,
        stage_name: str,
        reason: str,
        context_summary: str = "",
        stage_spec: StageSpec | None = None,
    ) -> WaitingState:
        """Persist a waiting state and return it."""
        self.project_output_dir.mkdir(parents=True, exist_ok=True)
        waiting = WaitingState(
            stage_num=stage_num,
            stage_name=stage_name,
            reason=reason,
            context_summary=context_summary,
            timeout_seconds=self.stage_policy(stage_num).timeout_seconds,
            auto_proceed_on_timeout=self.stage_policy(stage_num).auto_proceed_on_timeout,
            run_id=self.run_id,
            plan_digest=self.plan_digest,
            stage_key=(stage_spec.key or stage_spec.name) if stage_spec else stage_name,
            artifact_digest=reviewed_content_digest(
                self.project_output_dir,
                stage_spec.contract.input_artifacts if stage_spec else (),
                self.repo_root,
                stage_spec.contract.output_artifacts if stage_spec else (),
                project_dir=self.source_project_dir,
            ),
            input_artifacts=stage_spec.contract.input_artifacts if stage_spec else (),
            output_artifacts=stage_spec.contract.output_artifacts if stage_spec else (),
        )
        atomic_write_text_confined(
            self.project_output_dir, self.waiting_path, json.dumps(waiting.to_dict(), indent=2), mode=0o600
        )
        self.write_agent_context(waiting, stage_spec=stage_spec)
        self.write_agent_response_schema()
        self._append_decision(
            action="pause",
            stage_num=stage_num,
            stage_name=stage_name,
            message=reason,
        )
        return waiting

    def status(self) -> dict[str, Any]:
        """Return current HITL status for CLI use."""
        waiting: dict[str, Any] | None = None
        if self.waiting_path.exists():
            waiting = json.loads(read_text_confined(self.project_output_dir, self.waiting_path))
            stage_num = int(waiting.get("stage_num", 0) or 0)
            policy = self.stage_policy(stage_num)
            waiting["timed_out"] = self._waiting_timed_out(waiting, policy)
        return {
            "mode": self.mode.value,
            "waiting": waiting,
            "decisions_path": str(self.decisions_path),
        }

    def history(self) -> list[dict[str, Any]]:
        """Return structured decision history."""
        if not self.decisions_path.exists():
            return []
        history: list[dict[str, Any]] = []
        decisions: dict[str, dict[str, Any]] = {}
        consumed: set[str] = set()
        for number, line in enumerate(read_text_confined(self.project_output_dir, self.decisions_path).splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Human decision history is corrupt at line {number}; authorization refused") from exc
            if not isinstance(row, dict) or not isinstance(row.get("action"), str):
                raise ValueError(
                    f"Human decision history has an invalid record at line {number}; authorization refused"
                )
            actions = {"pause", "guide", "approve", "resume", "reject", "abort", "consume", "timeout_auto_proceed"}
            if row["action"] not in actions:
                raise ValueError(
                    f"Human decision history has an unknown action at line {number}; authorization refused"
                )
            if row["action"] not in {"pause", "guide"}:
                valid = (
                    type(row.get("stage_num")) is int
                    and row["stage_num"] > 0
                    and isinstance(row.get("decision_id"), str)
                    and len(row["decision_id"]) == 32
                    and all(isinstance(row.get(key), str) for key in DECISION_BINDINGS)
                    and bool(row.get("stage_key"))
                    and len(row["artifact_digest"]) == 64
                )
                if not valid:
                    raise ValueError(
                        f"Human decision history lost decision bindings at line {number}; authorization refused"
                    )
            if row["action"] in {"approve", "resume"}:
                if row["decision_id"] in decisions:
                    raise ValueError("Human decision history repeats an authorization ID; authorization refused")
                decisions[row["decision_id"]] = row
            if row["action"] == "consume":
                prior = decisions.get(row["decision_id"])
                keys = (*DECISION_BINDINGS, "stage_num", "stage_name")
                if (
                    prior is None
                    or row["decision_id"] in consumed
                    or any(prior.get(key) != row.get(key) for key in keys)
                ):
                    raise ValueError("Human decision consumption has inconsistent custody; authorization refused")
                consumed.add(row["decision_id"])
            history.append(row)
        return history

    def agent_context(self) -> dict[str, Any]:
        """Return the current detached-review context, if present."""
        if not self.agent_context_path.exists():
            return {}
        payload = json.loads(read_text_confined(self.project_output_dir, self.agent_context_path))
        if not isinstance(payload, dict):
            raise ValueError(f"agent context must be a JSON object: {self.agent_context_path}")
        return dict(payload)

    def write_agent_context(self, waiting: WaitingState, *, stage_spec: StageSpec | None = None) -> Path:
        """Write adapter-ready context for detached review tools."""
        context = {
            "identity": {key: getattr(waiting, key) for key in DECISION_BINDINGS},
            "stage": {
                "num": waiting.stage_num,
                "name": waiting.stage_name,
                "reason": waiting.reason,
                "context_summary": waiting.context_summary,
                "contract": _stage_contract_payload(stage_spec),
            },
            "declared_artifacts": _declared_artifact_payloads(
                self.project_output_dir,
                stage_spec,
                project_dir=self.source_project_dir,
                repo_root=self.repo_root,
            ),
            "validation_status": _validation_status(self.project_output_dir),
            "guidance_history": _guidance_history(self.history()),
            "permitted_actions": list(AGENT_RESPONSE_ACTIONS),
            "response_schema_path": str(self.agent_response_schema_path),
        }
        self.project_output_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text_confined(
            self.project_output_dir,
            self.agent_context_path,
            json.dumps(context, indent=2, sort_keys=True) + "\n",
            mode=0o600,
        )
        return self.agent_context_path

    def write_agent_response_schema(self) -> Path:
        """Write the detached response JSON schema."""
        self.project_output_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_text_confined(
            self.project_output_dir,
            self.agent_response_schema_path,
            json.dumps(agent_response_schema(), indent=2, sort_keys=True) + "\n",
            mode=0o600,
        )
        return self.agent_response_schema_path

    def approve(self, message: str = "") -> None:
        """Approve the currently waiting stage and clear waiting state."""
        self._decision_for_waiting("approve", message)

    def reject(self, message: str = "") -> None:
        """Reject the currently waiting stage and clear waiting state."""
        self._decision_for_waiting("reject", message)

    def resume(self, message: str = "") -> None:
        """Record resume intent and clear waiting state.

        The actual stage selection still happens through checkpoint resume.
        """
        self._decision_for_waiting("resume", message)

    def abort(self, message: str = "") -> None:
        """Record explicit abort intent and clear waiting state."""
        self._decision_for_waiting("abort", message)

    def guide(self, *, stage_num: int, message: str) -> Path:
        """Persist human guidance for a future or paused stage."""
        if not self.stage_policy(stage_num).allow_guidance:
            raise ValueError(f"guidance is disabled for stage {stage_num}")
        path = self.guidance_dir / f"stage-{stage_num:02d}.md"
        atomic_write_text_confined(self.project_output_dir, path, message.rstrip() + "\n", mode=0o600)
        self._append_decision(
            action="guide",
            stage_num=stage_num,
            stage_name=f"stage-{stage_num:02d}",
            message=message,
        )
        return path

    def respond_from_file(self, response_path: Path) -> dict[str, Any]:
        """Validate and record a detached HITL response file."""
        validation = validate_agent_response_file(response_path)
        if not validation.valid:
            raise ValueError("; ".join(validation.issues))
        payload = validation.payload
        action = str(payload["action"])
        if action != "guide":
            if not self.waiting_path.is_file() or self.waiting_path.is_symlink():
                raise ValueError("No current waiting stage for detached response")
            waiting = json.loads(read_text_confined(self.project_output_dir, self.waiting_path))
            if any(payload.get(key) != waiting.get(key) for key in DECISION_BINDINGS):
                raise ValueError("Detached decision identity differs from reviewed waiting state")
            if "stage_num" in payload and payload["stage_num"] != waiting.get("stage_num"):
                raise ValueError("Detached decision stage number differs from reviewed waiting state")
        message = str(payload.get("message", "") or payload.get("reason", "") or "")
        if action == "guide":
            stage_num = int(payload.get("stage_num") or self._current_waiting_stage_num())
            self.guide(stage_num=stage_num, message=message)
        else:
            self._decision_for_waiting(action, message, expected=payload)
        return payload

    def _current_waiting_stage_num(self) -> int:
        if not self.waiting_path.exists():
            return 0
        try:
            waiting = json.loads(read_text_confined(self.project_output_dir, self.waiting_path))
        except json.JSONDecodeError:
            return 0
        return int(waiting.get("stage_num", 0) or 0)

    @locked_state
    def _decision_for_waiting(self, action: str, message: str, *, expected: dict[str, Any] | None = None) -> None:
        if self.waiting_path.exists():
            waiting = json.loads(read_text_confined(self.project_output_dir, self.waiting_path))
            stage_num = int(waiting.get("stage_num", 0))
            stage_name = str(waiting.get("stage_name", ""))
        else:
            raise ValueError("No current waiting stage to decide")
        if expected is not None and any(expected.get(key) != waiting.get(key) for key in DECISION_BINDINGS):
            raise ValueError("Detached decision identity differs from reviewed waiting state")
        if action == "resume" and waiting.get("reason") == "approval_required":
            raise ValueError("This checkpoint requires explicit approval; waiting state retained")
        self.history()
        if waiting.get("artifact_digest") != reviewed_content_digest(
            self.project_output_dir,
            tuple(waiting.get("input_artifacts", ())),
            self.repo_root,
            tuple(waiting.get("output_artifacts", ())),
            project_dir=self.source_project_dir,
        ):
            raise ValueError("Reviewed artifact contents changed; resolve and review a fresh pause")
        self._append_decision(
            action=action,
            stage_num=stage_num,
            stage_name=stage_name,
            message=message,
            bindings=waiting,
        )
        unlink_confined(self.project_output_dir, self.waiting_path)

    def _append_decision(
        self,
        *,
        action: str,
        stage_num: int,
        stage_name: str,
        message: str,
        bindings: dict[str, Any] | None = None,
    ) -> None:
        self.project_output_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "action": action,
            "stage_num": stage_num,
            "stage_name": stage_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if bindings:
            row.update(
                {key: bindings.get(key, "") for key in ("run_id", "plan_digest", "stage_key", "artifact_digest")}
            )
            row["decision_id"] = bindings.get("decision_id") or __import__("uuid").uuid4().hex
            row["input_artifacts"] = bindings.get("input_artifacts", [])
            row["output_artifacts"] = bindings.get("output_artifacts", [])
        append_text_confined(self.project_output_dir, self.decisions_path, json.dumps(row, sort_keys=True) + "\n")

    @locked_state
    def _auto_proceed_timed_out_waiting_stage(self, stage_num: int, stage_spec: StageSpec) -> bool:
        if not self.waiting_path.exists():
            return False
        try:
            waiting = json.loads(read_text_confined(self.project_output_dir, self.waiting_path))
        except json.JSONDecodeError:
            return False
        if (
            not isinstance(waiting, dict)
            or type(waiting.get("stage_num")) is not int
            or waiting["stage_num"] != stage_num
        ):
            return False
        identity = {
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "stage_key": stage_spec.key or stage_spec.name,
            "artifact_digest": reviewed_content_digest(
                self.project_output_dir,
                stage_spec.contract.input_artifacts,
                self.repo_root,
                stage_spec.contract.output_artifacts,
                project_dir=self.source_project_dir,
            ),
        }
        if any(waiting.get(key) != value for key, value in identity.items()):
            return False
        policy = self.stage_policy(stage_num)
        if policy.require_approval:
            return False
        if not policy.auto_proceed_on_timeout or not self._waiting_timed_out(waiting, policy):
            return False
        self._append_decision(
            action="timeout_auto_proceed",
            stage_num=stage_num,
            stage_name=str(waiting.get("stage_name", "")),
            message="auto-proceed after configured HITL timeout",
            bindings=waiting,
        )
        unlink_confined(self.project_output_dir, self.waiting_path)
        return True

    def _waiting_timed_out(self, waiting: dict[str, Any], policy: StagePolicy) -> bool:
        try:
            since = datetime.fromisoformat(str(waiting.get("since", "")))
        except ValueError:
            return False
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        if type(waiting.get("timeout_seconds")) is not int or waiting["timeout_seconds"] != policy.timeout_seconds:
            return False
        timeout = policy.timeout_seconds
        now = datetime.now(tz=since.tzinfo)
        return (now - since).total_seconds() >= timeout


def _coerce_mode(mode: HitlMode | str) -> HitlMode:
    if isinstance(mode, HitlMode):
        return mode
    try:
        return HitlMode(mode)
    except ValueError as exc:
        raise ValueError(f"Unsupported human intervention mode: {mode}") from exc
