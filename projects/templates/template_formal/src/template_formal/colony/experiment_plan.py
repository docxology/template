"""Typed validation for the formal exemplar's declared ablation plan.

The experiment modules contain the executable analyses; this module validates
the small YAML plan that documents which configuration axes those analyses are
allowed to vary.  Keeping the plan typed prevents a new axis from becoming a
prose-only promise or a misspelled ``ColonyTrialConfig`` field from silently
falling outside the real trial harness.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from template_formal.colony.experiment import ColonyTrialConfig

PLAN_SCHEMA_VERSION = 1
REQUIRED_ABLATION_PARAMETERS = frozenset({"deposit_amount", "decay", "sensing_noise_std", "sensed_concentration_cap"})


@dataclass(frozen=True, slots=True)
class AblationAxis:
    """One declared parameter axis and its real tested values."""

    name: str
    parameter: str
    values: tuple[float, ...]
    negative_control: str


@dataclass(frozen=True, slots=True)
class ExperimentPlan:
    """Validated experiment-plan metadata."""

    schema_version: int
    axes: tuple[AblationAxis, ...]

    @property
    def parameters(self) -> frozenset[str]:
        """Return the config fields covered by the declared axes."""
        return frozenset(axis.parameter for axis in self.axes)


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _number_values(value: object, label: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise ValueError(f"{label} must be a non-empty sequence")
    numbers: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            raise ValueError(f"{label} must contain only numbers")
        numbers.append(float(item))
    if len(set(numbers)) != len(numbers):
        raise ValueError(f"{label} must not contain duplicate values")
    return tuple(numbers)


def validate_experiment_plan(raw: object) -> ExperimentPlan:
    """Validate and normalize a YAML-loaded experiment plan."""
    mapping = _require_mapping(raw, "experiment plan")
    version = mapping.get("schema_version", PLAN_SCHEMA_VERSION)
    if isinstance(version, bool) or not isinstance(version, int) or version != PLAN_SCHEMA_VERSION:
        raise ValueError(f"unsupported experiment plan schema_version: {version!r}")
    raw_axes = mapping.get("ablation_axes")
    if isinstance(raw_axes, (str, bytes)) or not isinstance(raw_axes, Sequence) or not raw_axes:
        raise ValueError("experiment plan ablation_axes must be a non-empty sequence")

    known_parameters = {field.name for field in fields(ColonyTrialConfig) if field.name != "seed"}
    axes: list[AblationAxis] = []
    seen_names: set[str] = set()
    seen_parameters: set[str] = set()
    for index, raw_axis in enumerate(raw_axes):
        axis = _require_mapping(raw_axis, f"ablation_axes[{index}]")
        name = axis.get("name")
        parameter = axis.get("parameter")
        negative_control = axis.get("negative_control")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"ablation_axes[{index}].name must be a non-empty string")
        if name in seen_names:
            raise ValueError(f"duplicate ablation axis name: {name}")
        if not isinstance(parameter, str) or parameter not in known_parameters:
            raise ValueError(f"unknown ablation parameter: {parameter!r}")
        if parameter in seen_parameters:
            raise ValueError(f"duplicate ablation parameter: {parameter}")
        if not isinstance(negative_control, str) or not negative_control.strip():
            raise ValueError(f"ablation_axes[{index}].negative_control must be a non-empty string")
        axes.append(
            AblationAxis(
                name=name,
                parameter=parameter,
                values=_number_values(axis.get("values"), f"ablation_axes[{index}].values"),
                negative_control=negative_control,
            )
        )
        seen_names.add(name)
        seen_parameters.add(parameter)

    missing = sorted(REQUIRED_ABLATION_PARAMETERS - seen_parameters)
    if missing:
        raise ValueError(f"experiment plan omits required ablation parameter(s): {', '.join(missing)}")
    return ExperimentPlan(schema_version=int(version), axes=tuple(axes))


def load_experiment_plan(path: str | Path) -> ExperimentPlan:
    """Load and validate an experiment plan from YAML."""
    plan_path = Path(path)
    with plan_path.open(encoding="utf-8") as handle:
        return validate_experiment_plan(yaml.safe_load(handle))
