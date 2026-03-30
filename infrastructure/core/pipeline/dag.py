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

logger = get_logger(__name__)


@dataclass
class StageDefinition:
    """A single stage parsed from ``pipeline.yaml``."""

    name: str
    script: str | None = None
    method: str | None = None
    args: list[str] = field(default_factory=list)
    allow_skip: bool = False
    depends_on: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


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
            definitions.append(
                StageDefinition(
                    name=entry["name"],
                    script=entry.get("script"),
                    method=entry.get("method"),
                    args=entry.get("args", []),
                    allow_skip=entry.get("allow_skip", False),
                    depends_on=entry.get("depends_on", []),
                    tags=entry.get("tags", []),
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
            self.stages = [
                s for s in self.stages if not (set(s.tags) & exclude)
            ]
        if include_only:
            self.stages = [
                s for s in self.stages if set(s.tags) & include_only
            ]
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
            specs.append(StageSpec(name=stage.name, func=func))

        return specs

    # ── Internals ────────────────────────────────────────────────────────

    def _resolve_stage_func(
        self, stage: StageDefinition, executor: Any
    ) -> Callable[[], bool]:
        """Build a zero-arg callable for a stage definition."""
        if stage.method:
            method = getattr(executor, stage.method, None)
            if method is None:
                raise ValueError(
                    f"Stage '{stage.name}' references method '{stage.method}' "
                    f"but executor has no such method"
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

        raise ValueError(
            f"Stage '{stage.name}' must define either 'script' or 'method'"
        )

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

