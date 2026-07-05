from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import MadlibConfig
from markdown_tables import artifact_markdown_tables
from tokens import TokenPlan


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _summary_markdown(config: MadlibConfig, plan: TokenPlan) -> str:
    density = "\n".join(f"- `{category}`: {count}" for category, count in sorted(plan.category_counts.items()))
    steps = "\n".join(f"- `{step.name}` -> `{step.output}`" for step in config.method_protocol)
    return "\n".join(
        [
            f"# {config.title} Madlib Generation Summary",
            "",
            f"- Seed: `{plan.seed}`",
            f"- Token choices: `{len(plan.choices)}`",
            f"- Enabled sections: `{len(config.enabled_sections)}`",
            f"- Method steps: `{len(config.method_protocol)}`",
            f"- Design principles: `{len(config.design_principles)}`",
            f"- Pipeline phases: `{len(config.pipeline_phases)}`",
            f"- Quality probes: `{len(config.quality_probes)}`",
            f"- Authoring obligations: `{len(config.authoring_obligations)}`",
            "- Category density:",
            density,
            "",
            "## Method Protocol",
            "",
            steps,
            "",
        ]
    )


def _configured_field_summary_markdown(
    config: MadlibConfig,
    counts: dict[str, int],
    inventory: list[dict[str, str]],
) -> str:
    rows = "\n".join(f"- `{row['path']}`: {row['origin']} ({row['scope']})" for row in inventory[:25])
    return "\n".join(
        [
            "# Configured Field Summary",
            "",
            f"- Explicit paths: `{counts['explicit']}`",
            f"- Defaulted paths: `{counts['defaulted']}`",
            f"- Enabled visualization flags: `{counts['visualized']}`",
            f"- Visualization flags: `{', '.join(config.visualizations.enabled_flags) or 'none'}`",
            "",
            "## First Inventory Rows",
            "",
            rows,
            "",
        ]
    )


__all__ = [
    "_configured_field_summary_markdown",
    "_summary_markdown",
    "_write_json",
    "artifact_markdown_tables",
]
