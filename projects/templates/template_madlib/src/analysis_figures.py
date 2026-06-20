from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from config import MadlibConfig
from tokens import TokenPlan


_PAPER = "#fbfaf7"
_INK = "#17202a"
_MUTED = "#59636e"
_GRID = "#cfd6dd"
_TEAL = "#2f6f73"
_DARK_TEAL = "#214f52"
_LIGHT_TEAL = "#dcefed"
_AMBER = "#d98c4a"
_LIGHT_AMBER = "#f7e5cf"
_TITLE_KW: dict[str, Any] = {"fontsize": 13, "fontweight": "bold", "color": _INK, "va": "top"}


def write_token_density_figure(plan: TokenPlan, output_path: Path | str) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    counts = plan.category_counts
    categories = sorted(counts, key=lambda category: (counts[category], category))
    values = [counts[category] for category in categories]

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.barh(categories, values, color=_TEAL, alpha=0.92)
    ax.set_title("Token vocabulary is uneven by design", loc="left", color=_INK, pad=12)
    ax.set_xlabel("Selected token choices")
    ax.set_ylabel("")
    ax.set_xlim(0, max(values + [1]) + 1.3)
    ax.grid(axis="x", alpha=0.18, color=_GRID)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    for row_index, value in enumerate(values):
        ax.text(value + 0.12, row_index, str(value), va="center", color=_INK, fontsize=10)
    ax.text(
        0,
        1.02,
        "Counts come from the seeded TokenPlan, not from hand-authored figure labels.",
        transform=ax.transAxes,
        color=_MUTED,
        fontsize=9,
    )
    return _save_figure(fig, plt, output)


def write_cover_overview_figure(
    config: MadlibConfig,
    plan: TokenPlan,
    counts: dict[str, int],
    output_path: Path | str,
) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(_PAPER)

    ax.text(
        0.04,
        0.94,
        "Template Madlib maps config fields to manuscript evidence",
        fontsize=14,
        fontweight="bold",
        color=_INK,
        va="top",
    )
    ax.text(
        0.04,
        0.89,
        "The same generated data explains YAML declarations, token choices, IMRAD bodies, gates, and outputs.",
        fontsize=9.5,
        color=_MUTED,
        va="top",
    )

    nodes = [
        ("Config", f"{counts['explicit']} explicit paths\n{len(config.lexicon)} lexicon lists", 0.06),
        ("TokenPlan", f"{len(plan.choices)} choices\nseed {plan.seed}", 0.26),
        (
            "IMRAD",
            f"{len(config.enabled_sections)}/{len(config.section_conditions)} sections\nconditional bodies",
            0.46,
        ),
        ("Evidence", f"{len(config.method_protocol)} method\n{len(config.quality_probes)} QA probes", 0.66),
        ("Outputs", "PDF + HTML\nslides + copy", 0.84),
    ]
    y = 0.70
    for index, (title, body, x) in enumerate(nodes):
        _draw_box(ax, x, y, 0.14, 0.14, title, body, fill=_LIGHT_TEAL if index < 3 else _LIGHT_AMBER)
        if index < len(nodes) - 1:
            _draw_arrow(ax, x + 0.14, y + 0.07, nodes[index + 1][2], y + 0.07)

    _draw_origin_panel(ax, 0.05, 0.33, 0.22, 0.25, counts)
    _draw_density_panel(ax, 0.30, 0.33, 0.22, 0.25, plan)
    _draw_section_panel(ax, 0.55, 0.33, 0.19, 0.25, config, plan)
    _draw_gate_panel(ax, 0.77, 0.33, 0.18, 0.25, config)

    ax.text(
        0.05,
        0.16,
        "Cover claim",
        fontsize=9,
        fontweight="bold",
        color=_INK,
    )
    ax.text(
        0.05,
        0.115,
        "The figure is generated from the same source-owned inventory, token plan, and QA schema that hydrate the manuscript.",
        fontsize=9,
        color=_MUTED,
        wrap=True,
    )
    ax.text(
        0.05,
        0.065,
        "No external validation, DOI, or reader-quality result is implied by this local render.",
        fontsize=8.5,
        color=_AMBER,
    )
    return _save_figure(fig, plt, output)


def write_token_injection_flow_figure(
    config: MadlibConfig,
    plan: TokenPlan,
    output_path: Path | str,
) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.04, 0.92, "Source-owned token injection has five reviewable stages", **_TITLE_KW)
    stages = [
        ("Schema parse", "validate YAML\nand defaults", 0.05),
        ("Slot expansion", f"{len(config.slots)} rules\n{len(plan.choices)} choices", 0.25),
        ("Section compose", f"{len(config.enabled_sections)} enabled\nIMRAD bodies", 0.45),
        ("Artifact write", "JSON, reports\nfigure registry", 0.65),
        ("Render gates", "PDF, HTML\nvalidation copy", 0.84),
    ]
    for index, (title, body, x) in enumerate(stages):
        _draw_box(ax, x, 0.52, 0.13, 0.20, title, body, fill=_LIGHT_TEAL if index < 3 else _LIGHT_AMBER)
        if index < len(stages) - 1:
            _draw_arrow(ax, x + 0.13, 0.62, stages[index + 1][2], 0.62)

    guards = [
        "config parser tests",
        "seed-stability tests",
        "placeholder scan",
        "figure registry",
        "evidence registry",
    ]
    for index, guard in enumerate(guards):
        x = stages[index][2] + 0.065
        ax.plot([x, x], [0.50, 0.36], color=_GRID, lw=1)
        ax.text(x, 0.30, guard, ha="center", color=_MUTED, fontsize=8)
    ax.text(
        0.04,
        0.13,
        "Every transition is regenerated from project-local source before the shared renderer sees the manuscript.",
        color=_MUTED,
        fontsize=9,
    )
    return _save_figure(fig, plt, output)


def write_section_token_allocation_figure(
    config: MadlibConfig,
    plan: TokenPlan,
    output_path: Path | str,
) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    sections = list(config.section_conditions)
    values = [plan.section_counts.get(section, 0) for section in sections]
    colors = [_TEAL if config.section_conditions[section] else "#d7dce0" for section in sections]

    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    positions = list(range(len(sections)))
    ax.barh(positions, values, color=colors)
    ax.set_yticks(positions, labels=[section.replace("_", " ") for section in sections])
    ax.invert_yaxis()
    ax.set_xlabel("Selected token choices")
    ax.set_title("Token allocation follows section purpose", loc="left", color=_INK, pad=12)
    ax.grid(axis="x", alpha=0.18, color=_GRID)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(values + [1]) + 1.5)
    for position, value in zip(positions, values, strict=True):
        ax.text(value + 0.12, position, str(value), va="center", color=_INK, fontsize=9)
    ax.text(
        0,
        1.02,
        "Active rows come from section_conditions; muted rows mark disabled sections.",
        transform=ax.transAxes,
        color=_MUTED,
        fontsize=9,
    )
    return _save_figure(fig, plt, output)


def write_provenance_trace_map(
    config: MadlibConfig,
    plan: TokenPlan,
    output_path: Path | str,
) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    categories = sorted(plan.category_counts, key=lambda category: (-plan.category_counts[category], category))
    sections = list(config.section_conditions)
    matrix = [
        [
            sum(1 for choice in plan.choices if choice.category == category and choice.section == section)
            for category in categories
        ]
        for section in sections
    ]
    max_value = max((value for row in matrix for value in row), default=1)

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=max_value)
    ax.set_title("Each token can be traced back to a category and section", loc="left", color=_INK, pad=12)
    ax.set_xticks(range(len(categories)), labels=categories, rotation=35, ha="right")
    ax.set_yticks(range(len(sections)), labels=[section.replace("_", " ") for section in sections])
    for row_index, row_values in enumerate(matrix):
        for col_index, value in enumerate(row_values):
            if value:
                color = "white" if value >= max_value * 0.55 else _INK
                ax.text(col_index, row_index, str(value), ha="center", va="center", color=color, fontsize=8)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Token choices")
    return _save_figure(fig, plt, output)


def write_quality_gate_matrix(config: MadlibConfig, output_path: Path | str) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    fig, ax = plt.subplots(figsize=(8.1, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.04, 0.93, "Quality gates make the generated prose reviewable", **_TITLE_KW)
    ax.text(
        0.04,
        0.875,
        "Criteria, probes, and failure modes are declared in config and rendered as evidence tables.",
        fontsize=9,
        color=_MUTED,
    )

    columns = [
        ("Evaluation criteria", [criterion.name for criterion in config.evaluation_criteria], _LIGHT_TEAL),
        ("QA probes", [probe.name for probe in config.quality_probes], _LIGHT_AMBER),
        ("Failure modes", [mode.name for mode in config.failure_modes], "#f2ede6"),
    ]
    for col_index, (title, entries, fill) in enumerate(columns):
        x = 0.05 + col_index * 0.31
        _draw_list_panel(ax, x, 0.16, 0.27, 0.64, title, entries, fill)
    return _save_figure(fig, plt, output)


def write_configured_field_matrix(
    inventory: list[dict[str, str]],
    output_path: Path | str,
) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    scopes = ("schema", "section", "lexicon", "slot", "visualization")
    origins = ("explicit", "defaulted")
    values = [
        [sum(1 for row in inventory if row["scope"] == scope and row["origin"] == origin) for origin in origins]
        for scope in scopes
    ]

    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    image = ax.imshow(values, cmap="YlGnBu")
    ax.set_title("Configured fields are mostly explicit YAML", loc="left", color=_INK, pad=12)
    ax.set_xticks(range(len(origins)), labels=["Explicit", "Default"])
    ax.set_yticks(range(len(scopes)), labels=[scope.title() for scope in scopes])
    max_value = max((value for row_values in values for value in row_values), default=1)
    for row_index, row_values in enumerate(values):
        for col_index, value in enumerate(row_values):
            color = "white" if value >= max_value * 0.5 else "#0f172a"
            ax.text(col_index, row_index, str(value), ha="center", va="center", color=color)
    ax.text(
        0,
        1.02,
        "Cells count tracked config paths by schema scope and origin.",
        transform=ax.transAxes,
        color=_MUTED,
        fontsize=8.5,
    )
    ax.tick_params(axis="x", labelsize=8.5)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Field paths")
    return _save_figure(fig, plt, output)


def write_section_configuration_heatmap(
    config: MadlibConfig,
    plan: TokenPlan,
    output_path: Path | str,
) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    columns = ("condition", "title", "moves", "slots")
    values: list[list[int]] = []
    annotations: list[list[str]] = []
    for section in config.section_conditions:
        slot_count = plan.section_counts.get(section, 0)
        row_values = [
            int(f"madlib.section_conditions.{section}" in config.explicit_paths),
            int(f"madlib.section_titles.{section}" in config.explicit_paths),
            int(f"madlib.narrative_moves.{section}" in config.explicit_paths),
            int(slot_count > 0),
        ]
        values.append(row_values)
        annotations.append(["yes" if value else "default" for value in row_values[:-1]] + [str(slot_count)])

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    image = ax.imshow(values, cmap="BuGn", vmin=0, vmax=1)
    ax.set_title("Section configuration coverage is explicit", loc="left", color=_INK, pad=12)
    ax.set_xticks(range(len(columns)), labels=("Switch", "Title", "Moves", "Slots"))
    ax.set_yticks(
        range(len(config.section_conditions)),
        labels=[section.replace("_", " ") for section in config.section_conditions],
    )
    for row_index, row_annotations in enumerate(annotations):
        for col_index, label in enumerate(row_annotations):
            color = "white" if values[row_index][col_index] else "#0f172a"
            ax.text(col_index, row_index, label, ha="center", va="center", fontsize=8, color=color)
    ax.text(
        0,
        1.02,
        "Switches, titles, narrative moves, and slot counts are generated per section.",
        transform=ax.transAxes,
        color=_MUTED,
        fontsize=8.5,
    )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Configured")
    return _save_figure(fig, plt, output)


def write_field_origin_summary(counts: dict[str, int], output_path: Path | str) -> Path:
    plt = _pyplot()
    output = Path(output_path)
    labels = ("Explicit", "Defaulted")
    values = [counts["explicit"], counts["defaulted"]]

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    bars = ax.barh(labels, values, color=(_TEAL, _AMBER))
    ax.set_title("Configured fields are mostly explicit", loc="left", color=_INK, pad=12)
    ax.set_xlabel("Field paths")
    ax.set_xlim(0, max(values + [1]) + 4)
    ax.grid(axis="x", alpha=0.18, color=_GRID)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    for bar, value in zip(bars, values, strict=True):
        ax.text(value + 0.4, bar.get_y() + bar.get_height() / 2, str(value), va="center", color=_INK)
    return _save_figure(fig, plt, output)


def _figure_registry_entry(filename: str, caption: str, label: str, section: str) -> dict[str, str]:
    return {
        "filename": filename,
        "caption": caption,
        "label": label,
        "section": section,
        "generated_by": "scripts/01_generate_madlib_artifacts.py",
    }


def _draw_box(
    ax: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    fill: str,
) -> None:
    from matplotlib.patches import FancyBboxPatch

    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        linewidth=0.9,
        edgecolor=_DARK_TEAL,
        facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(x + width * 0.08, y + height * 0.72, title, fontsize=9, fontweight="bold", color=_INK)
    ax.text(x + width * 0.08, y + height * 0.38, body, fontsize=7.5, color=_MUTED, va="center")


def _draw_arrow(ax: Any, x1: float, y1: float, x2: float, y2: float) -> None:
    from matplotlib.patches import FancyArrowPatch

    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="-|>",
        mutation_scale=10,
        linewidth=1.1,
        color=_MUTED,
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arrow)


def _draw_panel_frame(
    ax: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    *,
    fill: str = "white",
) -> None:
    from matplotlib.patches import FancyBboxPatch

    panel = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=0.8,
        edgecolor=_GRID,
        facecolor=fill,
    )
    ax.add_patch(panel)
    ax.text(x + 0.012, y + height - 0.035, title, fontsize=8.5, fontweight="bold", color=_INK)


def _draw_origin_panel(ax: Any, x: float, y: float, width: float, height: float, counts: dict[str, int]) -> None:
    _draw_panel_frame(ax, x, y, width, height, "Field origins")
    values = [counts["explicit"], counts["defaulted"]]
    labels = ["explicit", "default"]
    max_value = max(values + [1])
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        bar_y = y + height - 0.09 - index * 0.07
        bar_w = (width - 0.105) * value / max_value
        ax.add_patch(plt_rectangle(x + 0.073, bar_y - 0.015, bar_w, 0.028, _TEAL if index == 0 else _AMBER))
        ax.text(x + 0.012, bar_y, label, fontsize=7.2, color=_MUTED, va="center")
        ax.text(x + 0.078 + bar_w, bar_y, str(value), fontsize=7.2, color=_INK, va="center")
    ax.text(x + 0.012, y + 0.014, f"{counts['total']} tracked paths", fontsize=7.5, color=_MUTED)


def _draw_density_panel(ax: Any, x: float, y: float, width: float, height: float, plan: TokenPlan) -> None:
    _draw_panel_frame(ax, x, y, width, height, "Token density")
    top_counts = Counter(plan.category_counts).most_common(3)
    max_value = max((value for _, value in top_counts), default=1)
    for index, (category, value) in enumerate(top_counts):
        bar_y = y + height - 0.08 - index * 0.045
        bar_w = (width - 0.095) * value / max_value
        ax.add_patch(plt_rectangle(x + 0.075, bar_y - 0.012, bar_w, 0.024, _TEAL))
        ax.text(x + 0.012, bar_y, _short_label(category, 10), fontsize=7.1, color=_MUTED, va="center")
        ax.text(x + 0.08 + bar_w, bar_y, str(value), fontsize=7.1, color=_INK, va="center")
    ax.text(x + 0.012, y + 0.014, f"{len(plan.category_counts)} categories", fontsize=7.5, color=_MUTED)


def _draw_section_panel(
    ax: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    config: MadlibConfig,
    plan: TokenPlan,
) -> None:
    _draw_panel_frame(ax, x, y, width, height, "Sections")
    enabled = len(config.enabled_sections)
    total = len(config.section_conditions)
    ax.text(x + 0.018, y + height - 0.11, f"{enabled}/{total}", fontsize=20, fontweight="bold", color=_TEAL)
    ax.text(x + 0.018, y + height - 0.155, "enabled sections", fontsize=7.5, color=_MUTED)
    rows = sorted(plan.section_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    row_summary = " | ".join(f"{_short_label(section, 5)} {value}" for section, value in rows)
    ax.text(x + 0.018, y + 0.075, "top slot use", fontsize=6.9, color=_MUTED)
    ax.text(x + 0.018, y + 0.043, row_summary, fontsize=6.5, color=_MUTED)


def _draw_gate_panel(ax: Any, x: float, y: float, width: float, height: float, config: MadlibConfig) -> None:
    _draw_panel_frame(ax, x, y, width, height, "Gates")
    values = [
        ("criteria", len(config.evaluation_criteria)),
        ("probes", len(config.quality_probes)),
        ("failures", len(config.failure_modes)),
    ]
    for index, (label, value) in enumerate(values):
        yy = y + height - 0.09 - index * 0.05
        ax.text(x + 0.018, yy, str(value), fontsize=12, fontweight="bold", color=_AMBER, va="center")
        ax.text(x + 0.062, yy, label, fontsize=7.5, color=_MUTED, va="center")
    ax.text(x + 0.018, y + 0.018, "local readiness only", fontsize=7.4, color=_MUTED)


def _draw_list_panel(
    ax: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    entries: list[str],
    fill: str,
) -> None:
    _draw_panel_frame(ax, x, y, width, height, f"{title} ({len(entries)})", fill=fill)
    for index, entry in enumerate(entries[:7], start=1):
        yy = y + height - 0.085 - (index - 1) * 0.067
        ax.text(x + 0.018, yy, f"{index}", fontsize=8, fontweight="bold", color=_TEAL, va="center")
        ax.text(x + 0.048, yy, _short_label(entry, 34), fontsize=7.5, color=_INK, va="center")
    if len(entries) > 7:
        ax.text(x + 0.048, y + 0.035, f"+ {len(entries) - 7} more", fontsize=7.4, color=_MUTED)


def plt_rectangle(x: float, y: float, width: float, height: float, color: str) -> Any:
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), width, height, linewidth=0, facecolor=color, alpha=0.92)


def _short_label(value: str, limit: int) -> str:
    clean = value.replace("_", " ")
    if len(clean) <= limit:
        return clean
    return clean[: max(1, limit - 1)].rstrip() + "."


def _pyplot() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _save_figure(fig: Any, plt: Any, output: Path) -> Path:
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200)
    plt.close(fig)
    return output
