"""Declarative pipeline DAG — reads ``pipeline.yaml`` and produces an ordered stage list.

This module sits between the YAML configuration and the ``PipelineExecutor``.
It performs:

1. YAML parsing & validation
2. Tag-based filtering (e.g. exclude ``llm`` stages when ``--mode core``)
3. Topological ordering of stages respecting ``depends_on`` constraints
4. Conversion to ``list[StageSpec]`` ready for the executor
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any, Callable, cast

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.types import StageContract, StageHooks

if TYPE_CHECKING:
    from infrastructure.core.pipeline.outcomes import StageOutcome

logger = get_logger(__name__)


def opt_in_tags_from_mapping(data: Mapping[str, Any] | None) -> frozenset[str]:
    """Return the YAML ``opt_in_tags`` set, or empty when the key is absent."""
    raw = (data or {}).get("opt_in_tags", [])
    return frozenset(_string_list(raw, "pipeline opt_in_tags"))


def load_opt_in_tags(yaml_path: Path) -> frozenset[str]:
    """Read ``opt_in_tags`` from a pipeline YAML file."""
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return frozenset()
    return opt_in_tags_from_mapping(raw)


_CONTRACT_KEYS = frozenset(
    {
        "input_artifacts",
        "output_artifacts",
        "mutable_artifacts",
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


_STAGE_KEYS = frozenset(
    {"name", "key", "script", "method", "args", "allow_skip", "depends_on", "tags", "failure_mode", "contract", "hooks"}
)


def _string_list(value: Any, label: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings")
    if nonempty and any(not item.strip() for item in value):
        raise ValueError(f"{label} must contain non-empty strings")
    return list(value)


def _string(value: Any, label: str, *, optional: bool = False, empty: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f"{label} must be a {'possibly empty' if empty else 'non-empty'} string")
    return value


def _integer(value: Any, label: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def parse_stage_definition(entry: Any, *, index: int = 1, source: Path = Path("<memory>")) -> "StageDefinition":
    """Parse a strict core/plugin declaration without coercing YAML types."""
    if not isinstance(entry, dict):
        raise ValueError(f"Each pipeline stage entry must be a mapping (stage #{index} in {source})")
    unknown = set(entry) - _STAGE_KEYS
    if unknown:
        raise ValueError(f"Pipeline stage #{index} has unsupported key(s): {sorted(map(str, unknown))}")
    name = _string(entry.get("name"), f"Pipeline stage #{index} in {source} 'name'")
    assert name is not None
    stage = StageDefinition(
        name=name,
        key=entry.get("key"),
        script=entry.get("script"),
        method=entry.get("method"),
        args=entry.get("args", []),
        allow_skip=entry.get("allow_skip", False),
        depends_on=entry.get("depends_on", []),
        tags=entry.get("tags", []),
        failure_mode=entry.get("failure_mode"),
        contract=_parse_contract(entry.get("contract"), name),
        hooks=_parse_hooks(entry.get("hooks"), name),
    )
    _validate_definition(stage)
    return stage


def _validate_definition(stage: "StageDefinition") -> None:
    label = f"Stage '{stage.name}'"
    _string(stage.name, f"{label} name")
    if (stage.script is None) == (stage.method is None):
        raise ValueError(f"{label} must declare exactly one of script or method, not both or neither")
    if not isinstance(stage.key, str) or re.fullmatch(r"[a-z][a-z0-9_-]*", stage.key) is None:
        raise ValueError(f"{label} key must be a stable lowercase identifier")
    if stage.script is not None:
        script = _string(stage.script, f"{label} script")
        assert script is not None
        path = Path(script)
        if (
            path.is_absolute()
            or len(path.parts) < 2
            or ".." in path.parts
            or "\\" in script
            or "\0" in script
            or path.suffix != ".py"
        ):
            raise ValueError(f"{label} script must be a repository-relative Python path without traversal")
    if stage.method is not None:
        method = _string(stage.method, f"{label} method")
        assert method is not None
        if not method.isidentifier():
            raise ValueError(f"{label} method must be a Python identifier")
    _string_list(stage.args, f"{label} args", nonempty=False)
    for key, value in (("depends_on", stage.depends_on), ("tags", stage.tags)):
        _string_list(value, f"{label} {key}")
        if len(value) != len(set(value)):
            raise ValueError(f"{label} {key} contains duplicates")
    if type(stage.allow_skip) is not bool:
        raise ValueError(f"{label} allow_skip must be a boolean")
    _string(stage.failure_mode, f"{label} failure_mode", optional=True)
    if not isinstance(stage.contract, StageContract) or not isinstance(stage.hooks, StageHooks):
        raise ValueError(f"{label} requires StageContract and StageHooks values")
    contract = asdict(stage.contract)
    for key in ("input_artifacts", "output_artifacts", "mutable_artifacts"):
        if not isinstance(contract[key], tuple):
            raise ValueError(f"{label} contract {key} must be a tuple of strings")
        contract[key] = list(contract[key])
    _parse_contract(contract, stage.name)
    hooks = asdict(stage.hooks)
    for key in ("pre_stage", "post_stage", "on_fail", "on_pause"):
        if not isinstance(hooks[key], tuple) or any(not isinstance(command, tuple) for command in hooks[key]):
            raise ValueError(f"{label} hooks {key} must be tuples of argv tuples")
        hooks[key] = [list(command) for command in hooks[key]]
    _parse_hooks(hooks, stage.name)


@dataclass
class StageDefinition:
    """A single stage parsed from ``pipeline.yaml``.

    ``failure_mode`` is documentation-only metadata: it is rendered into
    generated stage tables (see :mod:`infrastructure.documentation.stage_table`)
    and never interpreted by the executor.
    """

    name: str
    key: str | None = None
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
    """Validate declarations, preserve explicit filtering, and topologically order stages."""

    def __init__(
        self,
        stages: list[StageDefinition],
        *,
        opt_in_tags: frozenset[str] | None = None,
    ) -> None:
        self.stages = list(stages)
        self.opt_in_tags = frozenset(opt_in_tags) if opt_in_tags is not None else frozenset()
        # ``(stage, missing_dep)`` edges dropped by the most recent
        # ``sorted_stages()`` call — see the property of the same name.
        self._dropped_dependency_edges: list[tuple[str, str]] = []
        self._validate()

    # ── Construction helpers ─────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PipelineDAG":
        """Load a pipeline definition from a YAML file."""
        logger.info(f"Loading pipeline definition from {yaml_path}")
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("stages"), list):
            raise ValueError(f"pipeline.yaml must have a top-level 'stages' list: {yaml_path}")

        definitions: list[StageDefinition] = []
        for index, entry in enumerate(raw["stages"], start=1):
            definitions.append(parse_stage_definition(entry, index=index, source=yaml_path))
        logger.debug(f"Parsed {len(definitions)} stage definition(s) from {yaml_path.name}")
        return cls(definitions, opt_in_tags=opt_in_tags_from_mapping(raw))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineDAG":
        """Construct an in-memory definition with the same checks as YAML."""
        if not isinstance(data, dict) or not isinstance(data.get("stages"), list):
            raise ValueError("pipeline definition must have a top-level 'stages' list")
        definitions: list[StageDefinition] = []
        for index, entry in enumerate(data["stages"], start=1):
            definitions.append(parse_stage_definition(entry, index=index))
        return cls(definitions, opt_in_tags=opt_in_tags_from_mapping(data))

    # ── Filtering ────────────────────────────────────────────────────────

    def filter_tags(
        self,
        *,
        exclude: set[str] | None = None,
        include_only: set[str] | None = None,
    ) -> None:
        """Explicitly remove excluded stages or retain only included tags."""
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
        """Return a stable topological order and record intentionally removed edges."""
        name_to_stage = {s.name: s for s in self.stages}
        remaining_names = set(name_to_stage)

        # Build adjacency
        in_degree: dict[str, int] = {s.name: 0 for s in self.stages}
        dependents: dict[str, list[str]] = {s.name: [] for s in self.stages}

        dropped_edges: list[tuple[str, str]] = []
        for stage in self.stages:
            for dep in stage.depends_on:
                if dep in remaining_names:
                    in_degree[stage.name] += 1
                    dependents[dep].append(stage.name)
                else:
                    # A retained stage declares a dependency on a stage absent
                    # from the current set (tag-filtered or removed). The
                    # ordering constraint cannot be honored — record it so the
                    # drop is observable instead of silently discarded.
                    dropped_edges.append((stage.name, dep))

        self._dropped_dependency_edges = dropped_edges
        if dropped_edges:
            logger.warning(
                "Pipeline DAG: %d declared dependency edge(s) reference stages "
                "absent from the current set and were dropped (ordering for the "
                "dependent stage is no longer constrained): %s",
                len(dropped_edges),
                ", ".join(f"{stage}->{dep}" for stage, dep in dropped_edges),
            )

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

    @property
    def dropped_dependency_edges(self) -> list[tuple[str, str]]:
        """Edges removed by explicit filtering, as recorded by the latest sort."""
        return list(self._dropped_dependency_edges)

    # ── Conversion ───────────────────────────────────────────────────────

    def to_stage_specs(
        self,
        executor: Any,
    ) -> list[Any]:
        """Bind sorted declarations to executor callables without changing outcome types."""
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
                    key=stage.key,
                    allow_skip=stage.allow_skip,
                )
            )

        return specs

    # ── Internals ────────────────────────────────────────────────────────

    def _resolve_stage_func(self, stage: StageDefinition, executor: Any) -> Callable[[], bool | StageOutcome]:
        """Build a zero-arg callable for a stage definition."""
        if stage.script:
            # Build a closure over the script + args
            script = stage.script
            args_list = list(stage.args)
            if "--project" not in args_list:
                args_list.extend(["--project", executor.config.project_name])
            allow_skip = stage.allow_skip

            def _run(
                _script: str = script,
                _args: list[str] = args_list,
                _allow_skip: bool = allow_skip,
            ) -> bool | StageOutcome:
                return cast("bool | StageOutcome", executor._run_script(_script, *_args, allow_skip_code=_allow_skip))

            return _run

        if stage.method:
            method = getattr(executor, stage.method, None)
            if not callable(method):
                raise ValueError(
                    f"Stage '{stage.name}' references method '{stage.method}' but executor has no such method"
                )
            return cast("Callable[[], bool | StageOutcome]", method)

        raise ValueError(f"Stage '{stage.name}' must define either 'script' or 'method'")

    def _validate(self) -> None:
        """Ensure stage names are unique and deps reference existing stages."""
        for stage in self.stages:
            _validate_definition(stage)
        names = [s.name for s in self.stages]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate stage names: {sorted({n for n in names if names.count(n) > 1})}")
        keys = [stage.key for stage in self.stages]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate stage keys: {sorted(str(key) for key in keys if keys.count(key) > 1)}")
        for stage in self.stages:
            for dep in stage.depends_on:
                if dep not in names:
                    raise ValueError(f"Stage '{stage.name}' depends_on unknown stage '{dep}'")
                if dep == stage.name:
                    raise ValueError(f"Stage '{stage.name}' cannot depend on itself")


def stage_label(stage_name: str, project_name: str = "project", repo_root: Path | None = None) -> str:
    """Return a stage position from the selected DAG, or a diagnostic fallback."""
    if repo_root is None:
        return f"{stage_name} stage"

    from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source

    candidates: list[Path] = []
    try:
        project_source = resolve_pipeline_source(
            repo_root,
            repo_root / "projects" / project_name,
            purpose=PipelinePurpose.EXECUTION,
        ).path
        candidates.append(project_source)
        default_source = resolve_pipeline_source(repo_root, purpose=PipelinePurpose.EXECUTION).path
        if default_source not in candidates:
            candidates.append(default_source)
        for yaml_path in candidates:
            dag = PipelineDAG.from_yaml(yaml_path)
            names = [s.name for s in dag.stages]
            total = len(names)
            if stage_name in names:
                idx = names.index(stage_name) + 1
                return f"Stage {idx}/{total}: {stage_name}"
            # Stage not found in this YAML — try next candidate
    except Exception as exc:  # noqa: BLE001 — diagnostic-only; never fatal
        logger.debug("Could not resolve stage index from pipeline.yaml: %s", exc)

    # Fallback: drop the numeric prefix rather than print a stale "8/9".
    return f"{stage_name} stage"


def load_telemetry_config(yaml_path: Path) -> Any:
    """Load optional telemetry data; diagnostics remain nonblocking."""
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


def _parse_contract(raw: Any, stage_name: str) -> StageContract:
    """Validate contract types, artifact paths and bounded retry counts."""
    if raw is None:
        return StageContract()
    if not isinstance(raw, dict):
        raise ValueError(f"Stage '{stage_name}' contract must be a mapping")
    unknown = set(raw) - _CONTRACT_KEYS
    if unknown:
        raise ValueError(f"Stage '{stage_name}' has unsupported contract key(s): {sorted(map(str, unknown))}")
    artifacts: dict[str, tuple[str, ...]] = {}
    for key in ("input_artifacts", "output_artifacts", "mutable_artifacts"):
        values = _string_list(raw.get(key, []), f"Stage '{stage_name}' contract {key}")
        for value in values:
            if Path(value).is_absolute() or ".." in Path(value).parts or "\\" in value or "\0" in value:
                raise ValueError(f"Stage '{stage_name}' contract {key} requires repository-relative paths")
        artifacts[key] = tuple(values)
    return StageContract(
        **artifacts,
        definition_of_done=_string(raw.get("definition_of_done", ""), "definition_of_done", empty=True) or "",
        failure_code=_string(raw.get("failure_code", ""), "failure_code", empty=True) or "",
        retry_policy=_integer(raw.get("retry_policy", 0), "retry_policy", minimum=0),
        gate=_string(raw.get("gate"), "gate", optional=True),
        rollback_to=_string(raw.get("rollback_to"), "rollback_to", optional=True),
    )


def _normalize_hook_commands(value: Any, *, key: str, stage_name: str) -> tuple[tuple[str, ...], ...]:
    """Normalize a string, argv list, or list of argv commands to immutable tuples."""
    if value is None:
        return ()
    if isinstance(value, str):
        _string(value, f"Stage '{stage_name}' hook {key}")
        return ((value,),)
    if not isinstance(value, list):
        raise ValueError(f"Stage '{stage_name}' hook key '{key}' must be string or list")
    if not value:
        return ()
    if all(isinstance(item, str) for item in value):
        return (tuple(_string_list(value, f"Stage '{stage_name}' hook {key}")),)
    commands: list[tuple[str, ...]] = []
    for item in value:
        if isinstance(item, str):
            commands.append((item,))
            continue
        if not isinstance(item, list) or not all(isinstance(part, str) for part in item):
            raise ValueError(f"Stage '{stage_name}' hook key '{key}' command entries must be strings or string lists")
        if not item:
            raise ValueError(f"Stage '{stage_name}' hook {key} command must not be empty")
        commands.append(tuple(_string_list(item, f"Stage '{stage_name}' hook {key}")))
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

    if type(raw.get("run_in_ci", False)) is not bool:
        raise ValueError(f"Stage '{stage_name}' hook run_in_ci must be a boolean")
    return StageHooks(
        pre_stage=_normalize_hook_commands(raw.get("pre_stage"), key="pre_stage", stage_name=stage_name),
        post_stage=_normalize_hook_commands(raw.get("post_stage"), key="post_stage", stage_name=stage_name),
        on_fail=_normalize_hook_commands(raw.get("on_fail"), key="on_fail", stage_name=stage_name),
        on_pause=_normalize_hook_commands(raw.get("on_pause"), key="on_pause", stage_name=stage_name),
        timeout_seconds=_integer(raw.get("timeout_seconds", 30), "hook timeout_seconds", minimum=1),
        run_in_ci=raw.get("run_in_ci", False),
    )
