"""Pipeline control configuration parsing and merging."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.types import PipelineControlConfig, StagePolicy

_CONTROL_KEYS = frozenset(
    {
        "hitl_mode",
        "smart_pause_action",
        "custom_gate_stages",
        "stage_policies",
    }
)
_STAGE_POLICY_KEYS = frozenset(key for key in StagePolicy.__dataclass_fields__ if not key.startswith("_"))


def load_pipeline_control_config(
    default_yaml: Path | None,
    *,
    project_yaml: Path | None = None,
    cli_hitl_mode: str | None = None,
) -> PipelineControlConfig:
    """Load and merge advisory pipeline control config.

    Precedence is default YAML, then project YAML, then explicit CLI mode.
    """
    config = PipelineControlConfig()
    if default_yaml is not None:
        config = _merge_control_configs(config, _load_control_from_yaml(default_yaml))
    if project_yaml is not None:
        config = _merge_control_configs(config, _load_control_from_yaml(project_yaml))
    if cli_hitl_mode and cli_hitl_mode != "full-auto":
        config = replace(config, hitl_mode=cli_hitl_mode)
    return config


def merge_control_configs(
    base: PipelineControlConfig,
    overlay: PipelineControlConfig,
) -> PipelineControlConfig:
    """Merge two explicit control configs, with ``overlay`` taking precedence."""
    return _merge_control_configs(base, overlay)


def control_config_from_dict(data: dict[str, Any] | None) -> PipelineControlConfig:
    """Parse a ``control:`` mapping into a typed config."""
    if data is None:
        return PipelineControlConfig()
    if not isinstance(data, dict):
        raise ValueError("control block must be a mapping")

    unknown = set(data) - _CONTROL_KEYS
    if unknown:
        keys = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"unsupported control key(s): {keys}")

    stage_policies, stage_policy_fields = _parse_stage_policies(data.get("stage_policies"))
    return PipelineControlConfig(
        hitl_mode=data.get("hitl_mode", "full-auto"),
        smart_pause_action=data.get("smart_pause_action", "report"),
        custom_gate_stages=_tuple_of_ints(data.get("custom_gate_stages")),
        stage_policies=stage_policies,
        stage_policy_fields=stage_policy_fields,
    )


def _load_control_from_yaml(path: Path) -> PipelineControlConfig:
    if not path.exists():
        return PipelineControlConfig()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"pipeline YAML must be a mapping: {path}")
    return control_config_from_dict(raw.get("control"))


def _merge_control_configs(
    base: PipelineControlConfig,
    overlay: PipelineControlConfig,
) -> PipelineControlConfig:
    stage_policies = dict(base.stage_policies)
    stage_policy_fields = dict(base.stage_policy_fields)
    for stage_num, policy in overlay.stage_policies.items():
        overlay_fields = overlay.stage_policy_fields.get(stage_num) or _non_default_stage_policy_fields(policy)
        if stage_num in stage_policies:
            stage_policies[stage_num] = _merge_stage_policy(
                stage_policies[stage_num],
                policy,
                overlay_fields=overlay_fields,
            )
        else:
            stage_policies[stage_num] = policy
        stage_policy_fields[stage_num] = stage_policy_fields.get(stage_num, frozenset()) | overlay_fields
    return PipelineControlConfig(
        hitl_mode=overlay.hitl_mode if overlay.hitl_mode != "full-auto" else base.hitl_mode,
        smart_pause_action=(
            overlay.smart_pause_action if overlay.smart_pause_action != "report" else base.smart_pause_action
        ),
        custom_gate_stages=overlay.custom_gate_stages or base.custom_gate_stages,
        stage_policies=stage_policies,
        stage_policy_fields=stage_policy_fields,
    )


def _merge_stage_policy(
    base: StagePolicy,
    overlay: StagePolicy,
    *,
    overlay_fields: frozenset[str],
) -> StagePolicy:
    values = {
        field_name: getattr(base, field_name)
        for field_name in StagePolicy.__dataclass_fields__
        if not field_name.startswith("_")
    }
    for field_name in overlay_fields:
        values[field_name] = getattr(overlay, field_name)
    return StagePolicy(**values)


def _parse_stage_policies(raw: Any) -> tuple[dict[int, StagePolicy], dict[int, frozenset[str]]]:
    if raw is None:
        return {}, {}
    if not isinstance(raw, dict):
        raise ValueError("control.stage_policies must be a mapping")
    policies: dict[int, StagePolicy] = {}
    explicit_fields: dict[int, frozenset[str]] = {}
    for stage_key, payload in raw.items():
        if not isinstance(payload, dict):
            raise ValueError(f"stage policy for {stage_key!r} must be a mapping")
        unknown = set(payload) - _STAGE_POLICY_KEYS
        if unknown:
            keys = ", ".join(sorted(str(key) for key in unknown))
            raise ValueError(f"unsupported stage policy key(s): {keys}")
        if type(stage_key) is not int and not (isinstance(stage_key, str) and stage_key.isdecimal()):
            raise ValueError("Stage policy keys must be positive integer identities")
        stage_num = int(stage_key)
        if stage_num <= 0 or stage_num in policies:
            raise ValueError("Stage policy keys must be unique positive integers")
        policies[stage_num] = StagePolicy(**payload)
        explicit_fields[stage_num] = frozenset(str(key) for key in payload)
    return policies, explicit_fields


def _non_default_stage_policy_fields(policy: StagePolicy) -> frozenset[str]:
    default = StagePolicy()
    return frozenset(
        field_name
        for field_name in StagePolicy.__dataclass_fields__
        if not field_name.startswith("_") and getattr(policy, field_name) != getattr(default, field_name)
    )


def _tuple_of_ints(value: Any) -> tuple[int, ...]:
    if value is None:
        return ()
    if isinstance(value, list | tuple):
        if any(type(item) is not int or item <= 0 for item in value) or len(set(value)) != len(value):
            raise ValueError("custom_gate_stages must contain unique positive integers")
        return tuple(value)
    raise ValueError("custom_gate_stages must be a list of integers")
