"""Declarative pipeline DAG — reads ``pipeline.yaml`` and produces an ordered stage list.

This module sits between the YAML configuration and the ``PipelineExecutor``.
It performs:

1. YAML parsing & validation
2. Tag-based filtering (e.g. exclude ``llm`` stages when ``--core-only``)
3. Topological ordering of stages respecting ``depends_on`` constraints
4. Conversion to ``list[StageSpec]`` ready for the executor
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.types import StageContract, StageHooks

logger = get_logger(__name__)

_CONTRACT_KEYS = frozenset(
    {
        "input_artifacts",
        "output_artifacts",
        "definition_of_done",
        "failure_code",
        "retry_policy",
        "gate",
        "rollback_to",
    }
)
_HOOK_KEYS = frozenset(
    {
        "pre_stage",
        "post_stage",
        "on_fail",
        "on_pause",
        "timeout_seconds",
        "run_in_ci",
    }
)


@dataclass
class StageDefinition:
    """A single stage parsed from ``pipeline.yaml``.

    ``failure_mode`` is documentation-only metadata: it is rendered into
    generated stage tables (see :mod:`infrastructure.documentation.stage_table`)
    and never interpreted by the executor.
    """

    name: str
    script: str | None = None
    method: str | None = None
    args: list[str] = field(default_factory=list)
    allow_skip: bool = False
    depends_on: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    failure_mode: str | None = None
    contract: StageContract = field(default_factory=StageContract)
    hooks: StageHooks = field(default_factory=StageHooks)


class PipelineDAG:
    """Parse and topologically sort a declarative pipeline definition.

    Usage::

        dag = PipelineDAG.from_yaml(Path("pipeline.yaml"))
        dag.filter_tags(exclude={"llm"})
        specs = dag.to_stage_specs(executor)
    """

    def __init__(self, stages: list[StageDefinition]) -> None:
        self.stages = list(stages)
        self._validate()

    # ── Construction helpers ─────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PipelineDAG":
        """Load a pipeline definition from a YAML file."""
        logger.info(f"Loading pipeline definition from {yaml_path}")
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "stages" not in raw:
            raise ValueError(f"pipeline.yaml must have a top-level 'stages' list: {yaml_path}")

        definitions: list[StageDefinition] = []
        for entry in raw["stages"]:
            if not isinstance(entry, dict):
                raise ValueError("Each pipeline stage entry must be a mapping")
            definitions.append(
                StageDefinition(
                    name=entry["name"],
                    script=entry.get("script"),
                    method=entry.get("method"),
                    args=entry.get("args", []),
                    allow_skip=entry.get("allow_skip", False),
                    depends_on=entry.get("depends_on", []),
                    tags=entry.get("tags", []),
                    failure_mode=entry.get("failure_mode"),
                    contract=_parse_contract(entry.get("contract"), entry["name"]),
                    hooks=_parse_hooks(entry.get("hooks"), entry["name"]),
                )
            )
        logger.debug(f"Parsed {len(definitions)} stage definition(s) from {yaml_path.name}")
        return cls(definitions)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineDAG":
        """Construct from an in-memory dict (useful for tests)."""
        definitions: list[StageDefinition] = []
        for entry in data.get("stages", []):
            definitions.append(
                StageDefinition(
                    name=entry["name"],
                    script=entry.get("script"),
                    method=entry.get("method"),
                    args=entry.get("args", []),
                    allow_skip=entry.get("allow_skip", False),
                    depends_on=entry.get("depends_on", []),
                    tags=entry.get("tags", []),
                    failure_mode=entry.get("failure_mode"),
                    contract=_parse_contract(entry.get("contract"), entry["name"]),
                    hooks=_parse_hooks(entry.get("hooks"), entry["name"]),
                )
            )
        return cls(definitions)

    # ── Filtering ────────────────────────────────────────────────────────

    def filter_tags(
        self,
        *,
        exclude: set[str] | None = None,
        include_only: set[str] | None = None,
    ) -> None:
        """Remove stages whose tags match exclusion rules.

        Args:
            exclude: Remove any stage that has at least one of these tags.
            include_only: If provided, keep only stages that have at least one of these tags.
        """
        before = len(self.stages)
        if exclude:
            self.stages = [s for s in self.stages if not (set(s.tags) & exclude)]
        if include_only:
            self.stages = [s for s in self.stages if set(s.tags) & include_only]
        removed = before - len(self.stages)
        if removed:
            logger.info(f"Tag filter removed {removed} stage(s), {len(self.stages)} remaining")

    def remove_stage(self, name: str) -> None:
        """Remove a single stage by name."""
        self.stages = [s for s in self.stages if s.name != name]

    # ── Sorting ──────────────────────────────────────────────────────────

    def sorted_stages(self) -> list[StageDefinition]:
        """Return stages in topological order respecting ``depends_on``.

        Uses Kahn's algorithm. If the input is already linear, the original
        order is preserved.
        """
        name_to_stage = {s.name: s for s in self.stages}
        remaining_names = set(name_to_stage)

        # Build adjacency
        in_degree: dict[str, int] = {s.name: 0 for s in self.stages}
        dependents: dict[str, list[str]] = {s.name: [] for s in self.stages}

        for stage in self.stages:
            for dep in stage.depends_on:
                if dep in remaining_names:
                    in_degree[stage.name] += 1
                    dependents[dep].append(stage.name)
                # deps outside the filtered set are ignored (already removed)

        # Kahn's algorithm with stable ordering
        queue: list[str] = [n for n in [s.name for s in self.stages] if in_degree[n] == 0]
        result: list[StageDefinition] = []

        while queue:
            name = queue.pop(0)
            result.append(name_to_stage[name])
            for dep_name in dependents[name]:
                in_degree[dep_name] -= 1
                if in_degree[dep_name] == 0:
                    queue.append(dep_name)

        if len(result) != len(self.stages):
            cycle_nodes = [s.name for s in self.stages if s.name not in {r.name for r in result}]
            raise ValueError(f"Cycle detected in pipeline DAG involving: {cycle_nodes}")

        return result

    # ── Conversion ───────────────────────────────────────────────────────

    def to_stage_specs(
        self,
        executor: Any,
    ) -> list[Any]:
        """Convert sorted stages into ``StageSpec`` tuples the executor can run.

        For each ``StageDefinition``, resolves either:
        - ``method``: calls ``getattr(executor, method)``
        - ``script``: calls ``executor._run_script(script, *args)``

        Returns:
            List of ``StageSpec(name, func)`` tuples.
        """
        from infrastructure.core.pipeline.types import StageSpec

        sorted_stages = self.sorted_stages()
        specs: list[StageSpec] = []

        for stage in sorted_stages:
            func = self._resolve_stage_func(stage, executor)
            specs.append(
                StageSpec(
                    name=stage.name,
                    func=func,
                    contract=stage.contract,
                    hooks=stage.hooks,
                )
            )

        return specs

    # ── Internals ────────────────────────────────────────────────────────

    def _resolve_stage_func(self, stage: StageDefinition, executor: Any) -> Callable[[], bool]:
        """Build a zero-arg callable for a stage definition."""
        if stage.method:
            method = getattr(executor, stage.method, None)
            if method is None:
                raise ValueError(
                    f"Stage '{stage.name}' references method '{stage.method}' but executor has no such method"
                )
            return method

        if stage.script:
            # Build a closure over the script + args
            script = stage.script
            args_list = list(stage.args) + ["--project", executor.config.project_name]
            allow_skip = stage.allow_skip

            def _run(
                _script: str = script,
                _args: list[str] = args_list,
                _allow_skip: bool = allow_skip,
            ) -> bool:
                return executor._run_script(_script, *_args, allow_skip_code=_allow_skip)

            return _run

        raise ValueError(f"Stage '{stage.name}' must define either 'script' or 'method'")

    def _validate(self) -> None:
        """Ensure stage names are unique and deps reference existing stages."""
        names = [s.name for s in self.stages]
        if len(names) != len(set(names)):
            dupes = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate stage names: {set(dupes)}")

        name_set = set(names)
        for stage in self.stages:
            for dep in stage.depends_on:
                if dep not in name_set:
                    logger.debug(
                        f"Stage '{stage.name}' depends on '{dep}' which is not in the "
                        f"current stage set (may have been filtered)"
                    )


def load_telemetry_config(yaml_path: Path) -> Any:
    """Load the optional ``telemetry:`` block from a pipeline YAML file.

    Returns:
        A ``TelemetryConfig`` if the block exists, or ``None``.
    """
    from infrastructure.core.telemetry.config import TelemetryConfig

    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "telemetry" in raw:
            telem_data = raw["telemetry"]
            if isinstance(telem_data, dict):
                logger.debug(f"Loaded telemetry config from {yaml_path.name}")
                return TelemetryConfig.from_dict(telem_data)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Failed to load telemetry config from {yaml_path}: {e}")

    return None


def _as_str_tuple(value: Any, *, key: str, stage_name: str) -> tuple[str, ...]:
    """Normalize a YAML scalar/list value to a tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"Stage '{stage_name}' contract key '{key}' must contain strings")
        return tuple(value)
    raise ValueError(f"Stage '{stage_name}' contract key '{key}' must be string or list")


def _parse_contract(raw: Any, stage_name: str) -> StageContract:
    """Parse and validate the optional ``contract:`` block for a stage."""
    if raw is None:
        return StageContract()
    if not isinstance(raw, dict):
        raise ValueError(f"Stage '{stage_name}' contract must be a mapping")

    unknown = set(raw) - _CONTRACT_KEYS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Stage '{stage_name}' has unsupported contract key(s): {names}")

    return StageContract(
        input_artifacts=_as_str_tuple(raw.get("input_artifacts"), key="input_artifacts", stage_name=stage_name),
        output_artifacts=_as_str_tuple(raw.get("output_artifacts"), key="output_artifacts", stage_name=stage_name),
        definition_of_done=str(raw.get("definition_of_done", "") or ""),
        failure_code=str(raw.get("failure_code", "") or ""),
        retry_policy=int(raw.get("retry_policy", 0) or 0),
        gate=str(raw["gate"]) if raw.get("gate") is not None else None,
        rollback_to=str(raw["rollback_to"]) if raw.get("rollback_to") is not None else None,
    )


def _normalize_hook_commands(value: Any, *, key: str, stage_name: str) -> tuple[tuple[str, ...], ...]:
    """Normalize hook command YAML to immutable argv tuples.

    Accepted forms:
    - ``["python", "script.py"]`` for one command
    - ``[["python", "a.py"], ["python", "b.py"]]`` for many commands
    - ``"python script.py"`` for a command that will be shell-split later
    """
    if value is None:
        return ()
    if isinstance(value, str):
        return ((value,),)
    if not isinstance(value, list):
        raise ValueError(f"Stage '{stage_name}' hook key '{key}' must be string or list")
    if not value:
        return ()
    if all(isinstance(item, str) for item in value):
        return (tuple(value),)
    commands: list[tuple[str, ...]] = []
    for item in value:
        if isinstance(item, str):
            commands.append((item,))
            continue
        if not isinstance(item, list) or not all(isinstance(part, str) for part in item):
            raise ValueError(f"Stage '{stage_name}' hook key '{key}' command entries must be strings or string lists")
        commands.append(tuple(item))
    return tuple(commands)


def _parse_hooks(raw: Any, stage_name: str) -> StageHooks:
    """Parse and validate the optional ``hooks:`` block for a stage."""
    if raw is None:
        return StageHooks()
    if not isinstance(raw, dict):
        raise ValueError(f"Stage '{stage_name}' hooks must be a mapping")

    unknown = set(raw) - _HOOK_KEYS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Stage '{stage_name}' has unsupported hook key(s): {names}")

    return StageHooks(
        pre_stage=_normalize_hook_commands(raw.get("pre_stage"), key="pre_stage", stage_name=stage_name),
        post_stage=_normalize_hook_commands(raw.get("post_stage"), key="post_stage", stage_name=stage_name),
        on_fail=_normalize_hook_commands(raw.get("on_fail"), key="on_fail", stage_name=stage_name),
        on_pause=_normalize_hook_commands(raw.get("on_pause"), key="on_pause", stage_name=stage_name),
        timeout_seconds=int(raw.get("timeout_seconds", 30) or 30),
        run_in_ci=bool(raw.get("run_in_ci", False)),
    )
