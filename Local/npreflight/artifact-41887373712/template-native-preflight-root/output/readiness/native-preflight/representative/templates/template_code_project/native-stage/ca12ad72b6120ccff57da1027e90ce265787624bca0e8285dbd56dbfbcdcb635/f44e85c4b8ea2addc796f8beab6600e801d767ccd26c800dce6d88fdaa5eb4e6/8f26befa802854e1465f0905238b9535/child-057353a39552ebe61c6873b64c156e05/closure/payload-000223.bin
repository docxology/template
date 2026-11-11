"""Strict transport decoding for immutable resolved execution plans."""

from __future__ import annotations

import math
import re
from dataclasses import fields
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.dag import parse_stage_definition
from infrastructure.core.pipeline.plan import ExecutionPlan, PlannedStage, PLAN_SCHEMA_VERSION
from infrastructure.core.pipeline.target_contracts import effective_target_tags
from infrastructure.core.pipeline.types import StageContract, StageHooks, StagePolicy

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_-]*\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _mapping(value: object, names: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != names:
        raise ValueError(f"{label} requires exactly its declared fields")
    return value


def _strings(value: object, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list | tuple) or any(
        not isinstance(item, str) or "\0" in item or (not allow_empty and not item.strip()) for item in value
    ):
        raise ValueError(f"{label} requires an array of strings")
    return list(value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        raise ValueError(f"{label} requires a nonempty string")
    return value


def _stage(value: object) -> PlannedStage:
    raw = _mapping(value, {field.name for field in fields(PlannedStage)}, "Planned stage")
    contract = dict(_mapping(raw["contract"], {field.name for field in fields(StageContract)}, "Stage contract"))
    for name in ("input_artifacts", "output_artifacts", "mutable_artifacts"):
        contract[name] = _strings(contract[name], name)
    hooks = dict(_mapping(raw["hooks"], {field.name for field in fields(StageHooks)}, "Stage hooks"))
    for name in ("pre_stage", "post_stage", "on_fail", "on_pause"):
        commands = hooks[name]
        if not isinstance(commands, list | tuple):
            raise ValueError(f"Hook {name} requires an array of argv arrays")
        hooks[name] = [_strings(command, name) for command in commands]
        if any(not command for command in hooks[name]):
            raise ValueError(f"Hook {name} cannot contain an empty command")
    policy = StagePolicy(**_mapping(raw["policy"], {field.name for field in fields(StagePolicy)}, "Stage policy"))
    dependencies = _strings(raw["dependencies"], "Stage dependencies")
    if any(_IDENTIFIER.fullmatch(key) is None for key in dependencies):
        raise ValueError("Dependencies require stable stage keys")
    # Reuse declaration checks for targets, contracts, typed arguments and hooks.
    declaration = parse_stage_definition(
        {
            "key": raw["key"],
            "name": raw["name"],
            "script": raw["script"],
            "method": raw["method"],
            "args": _strings(raw["arguments"], "Stage arguments", allow_empty=True),
            "depends_on": dependencies,
            "tags": _strings(raw["tags"], "Stage tags"),
            "contract": contract,
            "hooks": hooks,
            "allow_skip": raw["allow_skip"],
        }
    )
    assert declaration.key is not None
    return PlannedStage(
        declaration.key,
        declaration.name,
        declaration.script,
        declaration.method,
        tuple(declaration.args),
        tuple(dependencies),
        tuple(declaration.tags),
        declaration.contract,
        declaration.hooks,
        policy,
        declaration.allow_skip,
    )


def plan_from_payload(payload: object, *, expected_digest: str | None = None) -> ExecutionPlan:
    """Reject unknown schemas, coercions and changed transported contracts."""
    raw = _mapping(payload, {field.name for field in fields(ExecutionPlan)}, "Execution plan")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != PLAN_SCHEMA_VERSION:
        raise ValueError("Unsupported execution plan schema; prepare a fresh resolved plan")
    project = _text(raw["project"], "Plan project")
    if Path(project).is_absolute() or ".." in Path(project).parts or "\\" in project:
        raise ValueError("Plan project must be a qualified repository-relative name")
    if not isinstance(raw["mode"], str) or raw["mode"] not in {"core", "live"}:
        raise ValueError("Plan mode must be core or live")
    for name in ("source_identity", "definition_identity", "environment_identity"):
        if _DIGEST.fullmatch(_text(raw[name], name)) is None:
            raise ValueError(f"Plan {name} requires a SHA-256 identity")
    provenance = _text(raw["provenance"], "Plan provenance")
    if ".." in Path(provenance).parts or "\\" in provenance:
        raise ValueError("Plan provenance cannot contain traversal")
    budget = raw["run_timeout_seconds"]
    try:
        valid_budget = type(budget) in {int, float} and math.isfinite(budget) and budget > 0
    except OverflowError:
        valid_budget = False
    if not valid_budget:
        raise ValueError("Plan run budget must be positive and finite")
    if not isinstance(raw["hitl_mode"], str) or raw["hitl_mode"] not in {
        "full-auto",
        "gate-only",
        "checkpoint",
        "custom",
    }:
        raise ValueError("Plan human intervention mode is invalid")
    if not isinstance(raw["smart_pause_action"], str) or raw["smart_pause_action"] not in {"report", "pause"}:
        raise ValueError("Plan pause policy is invalid")
    if not isinstance(raw["stages"], list | tuple) or not raw["stages"]:
        raise ValueError("Plan requires nonempty selected stages")
    stages = tuple(_stage(row) for row in raw["stages"])
    keys = tuple(stage.key for stage in stages)
    if len(set(keys)) != len(keys) or len({stage.name for stage in stages}) != len(stages):
        raise ValueError("Plan stage keys and names must be unique")
    for index, stage in enumerate(stages):
        if set(effective_target_tags(stage.tags, stage.script, stage.method)) != set(stage.tags):
            raise ValueError("Transported plan omits binding canonical target capabilities; prepare a fresh plan")
        if any(key in keys[index:] for key in stage.dependencies):
            raise ValueError("Selected plan dependencies must precede their consumers")
        if raw["mode"] == "core" and {"live", "llm"}.intersection(stage.tags):
            raise ValueError("Core plan cannot authorize a live stage")
    plan = ExecutionPlan(
        project,
        raw["mode"],
        stages,
        raw["source_identity"],
        raw["definition_identity"],
        provenance,
        budget,
        raw["hitl_mode"],
        raw["smart_pause_action"],
        raw["schema_version"],
        raw["environment_identity"],
    )
    if expected_digest is not None and (
        not isinstance(expected_digest, str)
        or _DIGEST.fullmatch(expected_digest) is None
        or plan.digest != expected_digest
    ):
        raise ValueError("Transported plan differs from the parent-resolved digest")
    return plan


__all__ = ["plan_from_payload"]
