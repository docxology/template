"""Schema-validated plugin pipeline stages (PLUGIN-STAGES-1).

This module lets a project declare *extra* pipeline stages without editing any
core stage definition. A project drops an optional
``projects/{name}/pipeline_plugins.yaml`` file with a ``plugins:`` list; each
entry is validated and then merged into the execution plan.

DEFAULT-OFF / OPT-IN contract
-----------------------------
The feature is entirely driven by the presence of plugin declarations:

- No ``pipeline_plugins.yaml`` file  -> :func:`load_plugin_stages` returns ``[]``.
- An empty file or ``plugins: []``    -> ``[]``.
- ``[]`` declarations passed to :func:`merge_plugin_stages` leave the plan
  unchanged.

So with no declaration the built stage list is byte-identical to before this
module existed. Nothing in the default pipeline path changes.

Validation guarantees
---------------------
Each declaration must:

- be a mapping with a non-empty ``name`` and unique stable ``key``;
- declare exactly one of ``script`` or ``method`` (a stage needs a runner);
- use the core declaration types and supported runner, contract and hook keys;
- declare outputs, acceptance criteria and a failure code in an explicit contract;
- have a list-valued ``depends_on`` (when present);
- not duplicate another plugin's ``name``;
- not clobber an existing (core) stage name when merged;
- only ``depends_on`` stages that exist in the merged plan.

Invalid declarations raise :class:`PluginStageError` with a clear message.

Part of the infrastructure layer (Layer 1) — reusable across all projects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition, parse_stage_definition
from infrastructure.core.pipeline.types import StageContract, StageHooks

#: Filename a project drops next to its sources to declare plugin stages.
PLUGIN_STAGES_FILENAME = "pipeline_plugins.yaml"

#: Keys a single plugin declaration may contain. Mirrors the subset of
#: ``StageDefinition`` fields safe to expose to project-level declarations.
_ALLOWED_PLUGIN_KEYS = frozenset(
    {"name", "key", "script", "method", "args", "allow_skip", "depends_on", "tags", "contract", "hooks"}
)


class PluginStageError(ValueError):
    """Raised when a plugin stage declaration is malformed or conflicts."""


@dataclass(frozen=True)
class PluginStageDeclaration:
    """A validated plugin stage declaration.

    Mirrors the runnable subset of :class:`StageDefinition`. Construction does
    not validate; use :func:`parse_plugin_stages` for the schema checks.
    """

    name: str
    key: str
    script: str | None = None
    method: str | None = None
    args: tuple[str, ...] = ()
    allow_skip: bool = False
    depends_on: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    contract: StageContract = field(default_factory=StageContract)
    hooks: StageHooks = field(default_factory=StageHooks)

    def to_stage_definition(self) -> StageDefinition:
        """Convert into the core :class:`StageDefinition` used by the DAG."""
        return StageDefinition(
            name=self.name,
            key=self.key,
            script=self.script,
            method=self.method,
            args=list(self.args),
            allow_skip=self.allow_skip,
            depends_on=list(self.depends_on),
            tags=list(self.tags),
            contract=self.contract,
            hooks=self.hooks,
        )


def load_plugin_stages(project_dir: Path) -> list[PluginStageDeclaration]:
    """Load and validate plugin declarations for a project.

    Reads ``project_dir / pipeline_plugins.yaml`` if it exists.

    Returns:
        The validated declarations, or ``[]`` when no file/declarations exist
        (the default-off path).

    Raises:
        PluginStageError: if the file exists but is malformed.
    """
    plugin_file = project_dir / PLUGIN_STAGES_FILENAME
    if not plugin_file.exists():
        return []

    try:
        raw = yaml.safe_load(plugin_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - exercised via message
        raise PluginStageError(f"Could not parse {plugin_file}: {exc}") from exc

    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise PluginStageError(f"{plugin_file} must be a mapping with a top-level 'plugins' list")

    entries = raw.get("plugins", [])
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise PluginStageError(f"{plugin_file}: 'plugins' must be a list")

    return parse_plugin_stages(entries)


def parse_plugin_stages(entries: list[Any]) -> list[PluginStageDeclaration]:
    """Validate raw plugin entries into :class:`PluginStageDeclaration` objects.

    Args:
        entries: List of raw mappings (e.g. parsed YAML).

    Raises:
        PluginStageError: on any schema violation.
    """
    if not isinstance(entries, list):
        raise PluginStageError("Plugin stages must be a list")
    declarations: list[PluginStageDeclaration] = []
    seen_names: set[str] = set()
    seen_keys: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise PluginStageError(f"Plugin stage #{index} must be a mapping")
        unknown = set(entry) - _ALLOWED_PLUGIN_KEYS
        if unknown:
            raise PluginStageError(f"Plugin stage #{index} has unsupported key(s): {sorted(map(str, unknown))}")
        try:
            stage = parse_stage_definition(entry, index=index, source=Path(PLUGIN_STAGES_FILENAME))
        except ValueError as exc:
            raise PluginStageError(str(exc)) from exc
        if (
            "contract" not in entry
            or not stage.contract.definition_of_done.strip()
            or not stage.contract.failure_code.strip()
            or not stage.contract.output_artifacts
        ):
            raise PluginStageError(
                f"Plugin stage '{stage.name}' requires an explicit contract with output_artifacts, definition_of_done and failure_code"
            )
        assert stage.key is not None
        if stage.name in seen_names or stage.key in seen_keys:
            raise PluginStageError(f"Duplicate plugin stage name or key: '{stage.name}' / '{stage.key}'")
        seen_names.add(stage.name)
        seen_keys.add(stage.key)
        declarations.append(
            PluginStageDeclaration(
                name=stage.name,
                key=stage.key,
                script=stage.script,
                method=stage.method,
                args=tuple(stage.args),
                allow_skip=stage.allow_skip,
                depends_on=tuple(stage.depends_on),
                tags=tuple(stage.tags),
                contract=stage.contract,
                hooks=stage.hooks,
            )
        )
    return declarations


def merge_plugin_stages(dag: PipelineDAG, declarations: list[PluginStageDeclaration]) -> None:
    """Merge validated plugin stages into a :class:`PipelineDAG` in place.

    Args:
        dag: The core DAG built from ``pipeline.yaml``.
        declarations: Validated plugin declarations (``[]`` is a no-op).

    Raises:
        PluginStageError: if a plugin clobbers an existing stage name or
            declares a dependency on a stage absent from the merged plan.
    """
    if not declarations:
        return

    existing_names = {stage.name for stage in dag.stages}
    existing_keys = {stage.key for stage in dag.stages}
    for declaration in declarations:
        contract = declaration.contract
        if (
            not contract.output_artifacts
            or not contract.definition_of_done.strip()
            or not contract.failure_code.strip()
        ):
            raise PluginStageError(f"Plugin stage '{declaration.name}' requires an explicit complete contract")
        if declaration.name in existing_names or declaration.key in existing_keys:
            raise PluginStageError(
                f"Plugin stage '{declaration.name}' would clobber an existing core stage name or key"
            )
    try:
        # Validate a candidate before mutating the live DAG: failed merges are atomic.
        candidate = PipelineDAG(
            [*dag.stages, *(declaration.to_stage_definition() for declaration in declarations)],
            opt_in_tags=dag.opt_in_tags,
        )
        candidate.sorted_stages()
    except (TypeError, ValueError) as exc:
        raise PluginStageError(str(exc)) from exc
    dag.stages = candidate.stages


__all__ = [
    "PLUGIN_STAGES_FILENAME",
    "PluginStageDeclaration",
    "PluginStageError",
    "load_plugin_stages",
    "merge_plugin_stages",
    "parse_plugin_stages",
]
