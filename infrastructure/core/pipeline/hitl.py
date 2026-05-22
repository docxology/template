"""Lightweight human-in-the-loop state for template pipeline runs.

The template keeps HITL deliberately explicit and file-backed. A pause writes
``output/hitl/waiting.json``; non-interactive commands append decisions to
``output/hitl/decisions.jsonl``. Resume still uses the existing checkpoint
machinery rather than introducing hidden workflow state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import compute_sha256
from infrastructure.core.pipeline.types import PipelineControlConfig, StagePolicy, StageSpec


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

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        return asdict(self)


@dataclass(frozen=True)
class AgentResponseValidation:
    """Validation result for a detached HITL agent response."""

    valid: bool
    issues: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)


AGENT_RESPONSE_ACTIONS = ("approve", "reject", "guide", "resume", "abort")


class HitlController:
    """File-backed HITL controller for one project output directory."""

    def __init__(
        self,
        *,
        project_output_dir: Path,
        mode: HitlMode | str = HitlMode.FULL_AUTO,
        control: PipelineControlConfig | None = None,
        custom_gate_stages: tuple[int, ...] = (),
    ) -> None:
        self.project_output_dir = project_output_dir
        self.control = control or PipelineControlConfig(hitl_mode=str(mode))
        self.mode = _coerce_mode(self.control.hitl_mode if control is not None else mode)
        self.custom_gate_stages = self.control.custom_gate_stages or custom_gate_stages
        self.hitl_dir = project_output_dir / "hitl"
        self.waiting_path = self.hitl_dir / "waiting.json"
        self.decisions_path = self.hitl_dir / "decisions.jsonl"
        self.guidance_dir = self.hitl_dir / "guidance"
        self.agent_context_path = self.hitl_dir / "agent_context.json"
        self.agent_response_schema_path = self.hitl_dir / "agent_response.schema.json"

    def should_pause_before(self, stage_num: int, stage_spec: StageSpec) -> bool:
        """Return whether the run should pause before executing a stage."""
        if self._auto_proceed_timed_out_waiting_stage(stage_num):
            return False
        policy = self.stage_policy(stage_num)
        if policy.pause_before:
            return True
        return policy.require_approval and self.mode == HitlMode.CUSTOM

    def should_pause_after(self, stage_num: int, stage_spec: StageSpec) -> bool:
        """Return whether the run should pause after a completed stage."""
        if self._auto_proceed_timed_out_waiting_stage(stage_num):
            return False
        policy = self.stage_policy(stage_num)
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
        self.hitl_dir.mkdir(parents=True, exist_ok=True)
        waiting = WaitingState(
            stage_num=stage_num,
            stage_name=stage_name,
            reason=reason,
            context_summary=context_summary,
            timeout_seconds=self.stage_policy(stage_num).timeout_seconds,
            auto_proceed_on_timeout=self.stage_policy(stage_num).auto_proceed_on_timeout,
        )
        self.waiting_path.write_text(json.dumps(waiting.to_dict(), indent=2), encoding="utf-8")
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
            waiting = json.loads(self.waiting_path.read_text(encoding="utf-8"))
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
        for line in self.decisions_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                history.append(row)
        return history

    def agent_context(self) -> dict[str, Any]:
        """Return the current detached-review context, if present."""
        if not self.agent_context_path.exists():
            return {}
        return json.loads(self.agent_context_path.read_text(encoding="utf-8"))

    def write_agent_context(self, waiting: WaitingState, *, stage_spec: StageSpec | None = None) -> Path:
        """Write adapter-ready context for detached review tools."""
        context = {
            "stage": {
                "num": waiting.stage_num,
                "name": waiting.stage_name,
                "reason": waiting.reason,
                "context_summary": waiting.context_summary,
                "contract": _stage_contract_payload(stage_spec),
            },
            "declared_artifacts": _declared_artifact_payloads(self.project_output_dir, stage_spec),
            "validation_status": _validation_status(self.project_output_dir),
            "guidance_history": _guidance_history(self.history()),
            "permitted_actions": list(AGENT_RESPONSE_ACTIONS),
            "response_schema_path": str(self.agent_response_schema_path),
        }
        self.hitl_dir.mkdir(parents=True, exist_ok=True)
        self.agent_context_path.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self.agent_context_path

    def write_agent_response_schema(self) -> Path:
        """Write the detached response JSON schema."""
        self.hitl_dir.mkdir(parents=True, exist_ok=True)
        self.agent_response_schema_path.write_text(
            json.dumps(agent_response_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return self.agent_response_schema_path

    def approve(self, message: str = "") -> None:
        """Approve the currently waiting stage and clear waiting state."""
        self._decision_for_waiting("approve", message)
        self.waiting_path.unlink(missing_ok=True)

    def reject(self, message: str = "") -> None:
        """Reject the currently waiting stage and clear waiting state."""
        self._decision_for_waiting("reject", message)
        self.waiting_path.unlink(missing_ok=True)

    def resume(self, message: str = "") -> None:
        """Record resume intent and clear waiting state.

        The actual stage selection still happens through checkpoint resume.
        """
        self._decision_for_waiting("resume", message)
        self.waiting_path.unlink(missing_ok=True)

    def abort(self, message: str = "") -> None:
        """Record explicit abort intent and clear waiting state."""
        self._decision_for_waiting("abort", message)
        self.waiting_path.unlink(missing_ok=True)

    def guide(self, *, stage_num: int, message: str) -> Path:
        """Persist human guidance for a future or paused stage."""
        if not self.stage_policy(stage_num).allow_guidance:
            raise ValueError(f"guidance is disabled for stage {stage_num}")
        self.guidance_dir.mkdir(parents=True, exist_ok=True)
        path = self.guidance_dir / f"stage-{stage_num:02d}.md"
        path.write_text(message.rstrip() + "\n", encoding="utf-8")
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
        message = str(payload.get("message", "") or payload.get("reason", "") or "")
        if action == "approve":
            self.approve(message=message)
        elif action == "reject":
            self.reject(message=message)
        elif action == "resume":
            self.resume(message=message)
        elif action == "abort":
            self.abort(message=message)
        elif action == "guide":
            stage_num = int(payload.get("stage_num") or self._current_waiting_stage_num())
            self.guide(stage_num=stage_num, message=message)
        return payload

    def _current_waiting_stage_num(self) -> int:
        if not self.waiting_path.exists():
            return 0
        try:
            waiting = json.loads(self.waiting_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return 0
        return int(waiting.get("stage_num", 0) or 0)

    def _decision_for_waiting(self, action: str, message: str) -> None:
        if self.waiting_path.exists():
            waiting = json.loads(self.waiting_path.read_text(encoding="utf-8"))
            stage_num = int(waiting.get("stage_num", 0))
            stage_name = str(waiting.get("stage_name", ""))
        else:
            stage_num = 0
            stage_name = ""
        self._append_decision(
            action=action,
            stage_num=stage_num,
            stage_name=stage_name,
            message=message,
        )

    def _append_decision(
        self,
        *,
        action: str,
        stage_num: int,
        stage_name: str,
        message: str,
    ) -> None:
        self.hitl_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "action": action,
            "stage_num": stage_num,
            "stage_name": stage_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with self.decisions_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    def _auto_proceed_timed_out_waiting_stage(self, stage_num: int) -> bool:
        if not self.waiting_path.exists():
            return False
        try:
            waiting = json.loads(self.waiting_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        if int(waiting.get("stage_num", 0) or 0) != stage_num:
            return False
        policy = self.stage_policy(stage_num)
        if not policy.auto_proceed_on_timeout or not self._waiting_timed_out(waiting, policy):
            return False
        self._append_decision(
            action="timeout_auto_proceed",
            stage_num=stage_num,
            stage_name=str(waiting.get("stage_name", "")),
            message="auto-proceed after configured HITL timeout",
        )
        self.waiting_path.unlink(missing_ok=True)
        return True

    def _waiting_timed_out(self, waiting: dict[str, Any], policy: StagePolicy) -> bool:
        try:
            since = datetime.fromisoformat(str(waiting.get("since", "")))
        except ValueError:
            return False
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        timeout = int(waiting.get("timeout_seconds", policy.timeout_seconds) or policy.timeout_seconds)
        now = datetime.now(tz=since.tzinfo)
        return (now - since).total_seconds() >= timeout


def _coerce_mode(mode: HitlMode | str) -> HitlMode:
    if isinstance(mode, HitlMode):
        return mode
    try:
        return HitlMode(mode)
    except ValueError:
        return HitlMode.FULL_AUTO


def agent_response_schema() -> dict[str, Any]:
    """Return the JSON schema for detached HITL responses."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["action"],
        "properties": {
            "action": {"type": "string", "enum": list(AGENT_RESPONSE_ACTIONS)},
            "message": {"type": "string"},
            "reason": {"type": "string"},
            "stage_num": {"type": "integer", "minimum": 0},
        },
    }


def validate_agent_response_file(path: Path) -> AgentResponseValidation:
    """Validate a detached HITL response JSON file without recording it."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return AgentResponseValidation(valid=False, issues=(f"invalid response JSON: {exc}",))
    if not isinstance(payload, dict):
        return AgentResponseValidation(valid=False, issues=("response must be a JSON object",))
    issues: list[str] = []
    allowed = set(agent_response_schema()["properties"])
    unknown = set(payload) - allowed
    if unknown:
        issues.append(f"unsupported response key(s): {', '.join(sorted(unknown))}")
    action = payload.get("action")
    if action not in AGENT_RESPONSE_ACTIONS:
        issues.append(f"unsupported action: {action}")
    if action == "guide" and not str(payload.get("message", "") or "").strip():
        issues.append("guide responses require message")
    return AgentResponseValidation(valid=not issues, issues=tuple(issues), payload=payload if not issues else {})


def _stage_contract_payload(stage_spec: StageSpec | None) -> dict[str, Any]:
    if stage_spec is None:
        return {}
    return asdict(stage_spec.contract)


def _declared_artifact_payloads(output_dir: Path, stage_spec: StageSpec | None) -> list[dict[str, Any]]:
    if stage_spec is None:
        return []
    payloads: list[dict[str, Any]] = []
    project_name = output_dir.parent.name
    for raw in stage_spec.contract.output_artifacts:
        path = _resolve_declared_output(output_dir, raw.replace("{project}", project_name))
        row: dict[str, Any] = {
            "declared": raw,
            "path": _display_path(output_dir, path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        }
        if path.exists() and path.is_file():
            row["sha256"] = compute_sha256(path)
        payloads.append(row)
    return payloads


def _resolve_declared_output(output_dir: Path, raw: str) -> Path:
    rendered = raw.rstrip("/")
    if "/output/" in rendered:
        return output_dir / rendered.split("/output/", 1)[1]
    if rendered.startswith("output/"):
        return output_dir / rendered.removeprefix("output/")
    return output_dir / rendered


def _display_path(output_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(output_dir))
    except ValueError:
        return str(path)


def _validation_status(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "reports" / "validation_report.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid validation_report.json"}
    if not isinstance(payload, dict):
        return {"error": "validation_report.json must be an object"}
    return {
        "checks": payload.get("checks", {}),
        "summary": payload.get("summary", {}),
        "output_statistics": payload.get("output_statistics", {}),
    }


def _guidance_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in history if row.get("action") == "guide"]
