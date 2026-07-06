from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analysis_fields import configured_field_counts, configured_field_inventory
from .composition import build_imrad_sections
from .config import MadlibConfig, load_madlib_config
from .tokens import TokenPlan, generate_token_plan


@dataclass(frozen=True)
class MadlibRun:
    project_root: Path
    config: MadlibConfig
    plan: TokenPlan
    sections: dict[str, str]
    field_inventory: list[dict[str, str]]
    field_counts: dict[str, int]


def build_run(project_root: Path | str) -> MadlibRun:
    root = Path(project_root)
    config = load_madlib_config(root)
    plan = generate_token_plan(config)
    sections = build_imrad_sections(config, plan)
    field_inventory = configured_field_inventory(config, plan)
    field_counts = configured_field_counts(config, field_inventory)
    return MadlibRun(
        project_root=root,
        config=config,
        plan=plan,
        sections=sections,
        field_inventory=field_inventory,
        field_counts=field_counts,
    )
