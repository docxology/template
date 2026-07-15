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

- be a mapping with a non-empty ``name``;
- declare exactly one of ``script`` or ``method`` (a stage needs a runner);
- use only supported keys (``name``, ``script``, ``method``, ``args``,
  ``allow_skip``, ``depends_on``, ``tags``);
- have a list-valued ``depends_on`` (when present);
- not duplicate another plugin's ``name``;
- not clobber an existing (core) stage name when merged;
- only ``depends_on`` stages that exist in the merged plan.

Invalid declarations raise :class:`PluginStageError` with a clear message.

Part of the infrastructure layer (Layer 1) — reusable across all projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition

logger = get_logger(__name__)

#: Filename a project drops next to its sources to declare plugin stages.
PLUGIN_STAGES_FILENAME = "pipeline_plugins.yaml"

#: Keys a single plugin declaration may contain. Mirrors the subset of
#: ``StageDefinition`` fields safe to expose to project-level declarations.
_ALLOWED_PLUGIN_KEYS = frozenset({"name", "script", "method", "args", "allow_skip", "depends_on", "tags"})


class PluginStageError(ValueError):
    """Raised when a plugin stage declaration is malformed or conflicts."""


@dataclass(frozen=True)
class PluginStageDeclaration:
    """A validated plugin stage declaration.

    Mirrors the runnable subset of :class:`StageDefinition`. Construction does
    not validate; use :func:`parse_plugin_stages` for the schema checks.
    """

    name: str
    script: str | None = None
    method: str | None = None
    args: tuple[str, ...] = ()
    allow_skip: bool = False
    depends_on: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def to_stage_definition(self) -> StageDefinition:
        """Convert into the core :class:`StageDefinition` used by the DAG."""
        return StageDefinition(
            name=self.name,
            script=self.script,
            method=self.method,
            args=list(self.args),
            allow_skip=self.allow_skip,
            depends_on=list(self.depends_on),
            tags=list(self.tags),
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

    declarations = parse_plugin_stages(entries)
    if declarations:
        logger.info(
            "Loaded %d plugin stage declaration(s) from %s",
            len(declarations),
            plugin_file.name,
        )
    return declarations


def parse_plugin_stages(entries: list[Any]) -> list[PluginStageDeclaration]:
    """Validate raw plugin entries into :class:`PluginStageDeclaration` objects.

    Args:
        entries: List of raw mappings (e.g. parsed YAML).

    Raises:
        PluginStageError: on any schema violation.
    """
    declarations: list[PluginStageDeclaration] = []
    seen: set[str] = set()

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise PluginStageError(f"Plugin stage #{index + 1} must be a mapping, got {type(entry).__name__}")

        unknown = set(entry) - _ALLOWED_PLUGIN_KEYS
        if unknown:
            names = ", ".join(sorted(unknown))
            raise PluginStageError(f"Plugin stage #{index + 1} has unsupported key(s): {names}")

        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise PluginStageError(f"Plugin stage #{index + 1} must have a non-empty 'name'")

        script = entry.get("script")
        method = entry.get("method")
        if script is not None and method is not None:
            raise PluginStageError(f"Plugin stage '{name}' must declare 'script' or 'method', not both")
        if script is None and method is None:
            raise PluginStageError(f"Plugin stage '{name}' must declare either 'script' or 'method'")
        if script is not None and not isinstance(script, str):
            raise PluginStageError(f"Plugin stage '{name}' 'script' must be a string")
        if method is not None and not isinstance(method, str):
            raise PluginStageError(f"Plugin stage '{name}' 'method' must be a string")

        depends_on = _as_str_list(entry.get("depends_on"), key="depends_on", stage_name=name)
        tags = _as_str_list(entry.get("tags"), key="tags", stage_name=name)
        args = _as_str_list(entry.get("args"), key="args", stage_name=name)

        allow_skip = entry.get("allow_skip", False)
        if not isinstance(allow_skip, bool):
            raise PluginStageError(f"Plugin stage '{name}' 'allow_skip' must be a boolean")

        if name in seen:
            raise PluginStageError(f"Duplicate plugin stage name: '{name}'")
        seen.add(name)

        declarations.append(
            PluginStageDeclaration(
                name=name,
                script=script,
                method=method,
                args=tuple(args),
                allow_skip=allow_skip,
                depends_on=tuple(depends_on),
                tags=tuple(tags),
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

    existing_names = {s.name for s in dag.stages}
    _check_no_clobber(declarations, existing_names)
    _check_dependencies(declarations, existing_names)

    dag.stages.extend(decl.to_stage_definition() for decl in declarations)
    # Re-run structural validation (unique names, cycle detection happens at sort).
    dag._validate()
    logger.info("Merged %d plugin stage(s) into the pipeline DAG", len(declarations))


def _as_str_list(value: Any, *, key: str, stage_name: str) -> list[str]:
    """Normalize an optional YAML list-of-strings field."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PluginStageError(f"Plugin stage '{stage_name}' '{key}' must be a list of strings")
    return list(value)


def _check_no_clobber(declarations: list[PluginStageDeclaration], existing_names: set[str]) -> None:
    for decl in declarations:
        if decl.name in existing_names:
            raise PluginStageError(
                f"Plugin stage '{decl.name}' would clobber an existing core stage name; "
                f"plugin stages must use new, unique names"
            )


def _check_dependencies(declarations: list[PluginStageDeclaration], existing_names: set[str]) -> None:
    plugin_names = {decl.name for decl in declarations}
    resolvable = existing_names | plugin_names
    for decl in declarations:
        for dep in decl.depends_on:
            if dep not in resolvable:
                raise PluginStageError(
                    f"Plugin stage '{decl.name}' declares depends_on '{dep}', which is not a "
                    f"known core stage or plugin stage"
                )


__all__ = [
    "PLUGIN_STAGES_FILENAME",
    "PluginStageDeclaration",
    "PluginStageError",
    "load_plugin_stages",
    "merge_plugin_stages",
    "parse_plugin_stages",
]
