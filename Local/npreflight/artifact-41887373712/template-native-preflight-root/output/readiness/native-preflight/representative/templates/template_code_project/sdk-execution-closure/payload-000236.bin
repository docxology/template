"""Freeze declaration bytes and source identity before any plan policy parsing."""

from __future__ import annotations

import os
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.control import control_config_from_dict, merge_control_configs
from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source
from infrastructure.core.pipeline.execution_environment import effective_environment_identity
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint
from infrastructure.core.pipeline.plugins import PLUGIN_STAGES_FILENAME, merge_plugin_stages, parse_plugin_stages
from infrastructure.core.pipeline.types import PipelineConfig, PipelineControlConfig


def _paths(config: PipelineConfig) -> tuple[Path, Path, Path | None, Path]:
    selected = resolve_pipeline_source(
        config.repo_root, config.project_dir, explicit_path=config.pipeline_path, purpose=PipelinePurpose.EXECUTION
    ).path
    default = (
        selected
        if config.pipeline_path is not None
        else resolve_pipeline_source(config.repo_root, purpose=PipelinePurpose.EXECUTION).path
    )
    return (
        selected,
        default,
        None if config.pipeline_path is not None else config.project_dir / "pipeline.yaml",
        config.project_dir / PLUGIN_STAGES_FILENAME,
    )


def _read(path: Path) -> bytes | None:
    # lexists deliberately admits broken links to the confined reader's refusal.
    return read_bytes_confined(path.parent, path, max_bytes=8 * 1024 * 1024) if os.path.lexists(path) else None


def _mapping(raw: bytes | None, path: Path) -> dict[str, Any]:
    value = yaml.safe_load(raw) if raw is not None else None
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Pipeline declaration must be a mapping: {path}")
    return value


def _configuration_identity(config: PipelineConfig) -> str:
    # All selection/control fields, including deliberate programmatic overlays,
    # belong to the same compilation interval as the on-disk declarations.
    return _typed_identity(config)


def _typed_identity(value: PipelineConfig | PipelineControlConfig) -> str:
    def encode(item: object) -> object:
        if isinstance(item, Path):
            return str(item)
        if isinstance(item, frozenset | set):
            return sorted(item)
        raise TypeError(f"Unsupported plan configuration value: {type(item).__name__}")

    return canonical_digest(json.loads(json.dumps(asdict(value), default=encode, sort_keys=True)))


def configuration_control_identity(config: PipelineConfig, explicit: PipelineControlConfig | None) -> str:
    """Bind a preview cache to deliberate caller configuration and overrides."""
    return canonical_digest(
        {
            "config": _typed_identity(config),
            "explicit_control": _typed_identity(explicit) if explicit is not None else None,
        }
    )


@dataclass(frozen=True)
class FrozenPlanSources:
    """Original bytes are parsed once; rereads only verify their admission."""

    configuration: PipelineConfig
    paths: tuple[Path, Path, Path | None, Path]
    contents: tuple[tuple[Path, bytes | None], ...]
    source_identity: str
    environment_identity: str
    configuration_identity: str
    explicit_control: PipelineControlConfig | None
    explicit_identity: str | None

    @classmethod
    def capture(cls, config: PipelineConfig, explicit: PipelineControlConfig | None = None) -> FrozenPlanSources:
        configuration = _configuration_identity(config)
        frozen_config = deepcopy(config)
        copied = deepcopy(explicit)
        paths = _paths(frozen_config)
        source = source_fingerprint(frozen_config.repo_root, frozen_config.project_dir, definition_path=paths[0])
        environment = effective_environment_identity(
            frozen_config.repo_root, frozen_config.project_dir, mode=frozen_config.mode
        )
        unique = tuple(dict.fromkeys(path for path in paths if path is not None))
        return cls(
            frozen_config,
            paths,
            tuple((path, _read(path)) for path in unique),
            source,
            environment,
            configuration,
            copied,
            _typed_identity(copied) if copied is not None else None,
        )

    def control(self, config: PipelineConfig) -> PipelineControlConfig:
        config = self.configuration
        if self.explicit_control is not None:
            return self.explicit_control
        contents = dict(self.contents)
        control = PipelineControlConfig()
        for path in self.paths[1:3]:
            if path is not None:
                control = merge_control_configs(
                    control, control_config_from_dict(_mapping(contents[path], path).get("control"))
                )
        if config.hitl_mode and config.hitl_mode != "full-auto":
            control = replace(control, hitl_mode=config.hitl_mode)
        return (
            merge_control_configs(control, deepcopy(config.control))
            if config.control != PipelineControlConfig()
            else control
        )

    def dag(self) -> PipelineDAG:
        contents = dict(self.contents)
        selected, _, _, plugin = self.paths
        dag = PipelineDAG.from_dict(_mapping(contents[selected], selected))
        entries = _mapping(contents[plugin], plugin).get("plugins", [])
        if entries is None:
            entries = []
        if not isinstance(entries, list):
            raise ValueError(f"{plugin}: 'plugins' must be a list")
        merge_plugin_stages(dag, parse_plugin_stages(entries))
        return dag

    def verify(self, config: PipelineConfig, explicit: PipelineControlConfig | None = None) -> None:
        if (
            _configuration_identity(config) != self.configuration_identity
            or _paths(config) != self.paths
            or any(_read(path) != original for path, original in self.contents)
            or (_typed_identity(explicit) if explicit is not None else None) != self.explicit_identity
            or source_fingerprint(config.repo_root, config.project_dir, definition_path=self.paths[0])
            != self.source_identity
            or effective_environment_identity(config.repo_root, config.project_dir, mode=config.mode)
            != self.environment_identity
        ):
            raise ValueError("Plan source or control changed during compilation; compile a fresh execution plan")


__all__ = ["FrozenPlanSources", "configuration_control_identity"]
