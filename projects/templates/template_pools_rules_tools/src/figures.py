"""figures.py — Matplotlib-based architecture visualisations for the integration demo.

Public API
----------
generate_architecture_overview(output_dir=None, filename="architecture_overview.png")
generate_resource_counts(output_dir=None, filename="resource_counts.png", counts=None, _data=None)
generate_status_dashboard(
    output_dir=None,
    filename="status_dashboard.png",
    statuses=None,
    integration_result=None,
)
generate_fond_taxonomy(output_dir=None, filename="fond_taxonomy.png")
generate_rule_hierarchy(output_dir=None, filename="rule_hierarchy.png")
generate_tool_contract(output_dir=None, filename="tool_contract.png")
generate_resilience_layers(output_dir=None, filename="resilience_layers.png")
generate_pipeline_flow(output_dir=None, filename="pipeline_flow.png")
generate_cover_art(output_dir=None, filename="cover_art.png")
all_figures(output_dir=None, integration_result=None) -> dict[str, Path]
generate_all_figures(...)  -- alias for all_figures

All functions return pathlib.Path (or None if matplotlib unavailable).
"""

from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .cover_figure import generate_cover_art
from .rule_hierarchy_figure import generate_rule_hierarchy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Matplotlib availability guard
# ---------------------------------------------------------------------------
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False
    logger.warning("figures: matplotlib not available; all figure functions return None")

if TYPE_CHECKING:
    # Only needed for the `_save()` type annotation below; matplotlib's own
    # import above is intentionally guarded (this module must still import
    # cleanly when matplotlib is absent), so this stays behind TYPE_CHECKING
    # rather than adding an unconditional runtime import.
    from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Theme (matches docxology/template brand)
# ---------------------------------------------------------------------------
BLUE = "#1e3a8a"
BLUE_LIGHT = "#3b82f6"
TEAL = "#0f766e"
TEAL_LIGHT = "#14b8a6"
NEUTRAL = "#64748b"
NEUTRAL_LIGHT = "#94a3b8"
WHITE = "#ffffff"
BG = "#f8fafc"
GRID = "#e2e8f0"

STATUS_COLORS: dict[str, str] = {
    "ok": "#16a34a",
    "partial": "#d97706",
    "missing": "#dc2626",
}

STATUS_LABELS: dict[str, str] = {
    "ok": "Pass",
    "partial": "Partial",
    "missing": "Missing",
}


@dataclass(frozen=True)
class IntegrationFigureSpec:
    """Registry metadata for one generated integration figure."""

    label: str
    filename: str
    caption: str
    generated_by: str


FIGURE_REGISTRY_SCHEMA = "template-pools-rules-tools-figure-registry-v1"
INTEGRATION_FIGURE_SPECS: tuple[IntegrationFigureSpec, ...] = (
    IntegrationFigureSpec(
        label="fig:architecture",
        filename="architecture_overview.png",
        caption="Three-layer resource architecture with the integration layer.",
        generated_by="src.figures.generate_architecture_overview",
    ),
    IntegrationFigureSpec(
        label="fig:counts",
        filename="resource_counts.png",
        caption="Runtime counts for discovered fonds, rules, and tools.",
        generated_by="src.figures.generate_resource_counts",
    ),
    IntegrationFigureSpec(
        label="fig:pipeline",
        filename="status_dashboard.png",
        caption="Per-resource integration status dashboard.",
        generated_by="src.figures.generate_status_dashboard",
    ),
    IntegrationFigureSpec(
        label="fig:taxonomy",
        filename="fond_taxonomy.png",
        caption="Schema taxonomy across bibliography, contacts, and dataset fonds.",
        generated_by="src.figures.generate_fond_taxonomy",
    ),
    IntegrationFigureSpec(
        label="fig:rulehier",
        filename="rule_hierarchy.png",
        caption="Soft and strong branches of the template rule hierarchy.",
        generated_by="src.figures.generate_rule_hierarchy",
    ),
    IntegrationFigureSpec(
        label="fig:toolcontract",
        filename="tool_contract.png",
        caption="Input, behavior, output, and exit-code contracts for template tools.",
        generated_by="src.figures.generate_tool_contract",
    ),
    IntegrationFigureSpec(
        label="fig:resilience",
        filename="resilience_layers.png",
        caption="Three-level graceful-degradation design for shared resources.",
        generated_by="src.figures.generate_resilience_layers",
    ),
    IntegrationFigureSpec(
        label="fig:pipelineflow",
        filename="pipeline_flow.png",
        caption="Thin-script pipeline from source validation through publication rendering.",
        generated_by="src.figures.generate_pipeline_flow",
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _default_output_dir() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve().parents[1]
    return here / "manuscript" / "figures"


def _resolve_output(
    output_dir: str | pathlib.Path | None,
    filename: str,
    *,
    default_output_dir=_default_output_dir,
) -> pathlib.Path:
    if output_dir is None:
        output_dir = default_output_dir()
    out_dir = pathlib.Path(output_dir)
    _ensure_dir(out_dir)
    return out_dir / filename


def _save(fig: Figure, dest: pathlib.Path) -> pathlib.Path:
    fig.savefig(dest, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("figures: saved %s", dest)
    return dest


# ---------------------------------------------------------------------------
# Figure 1: Architecture Overview — three-panel diagram
# ---------------------------------------------------------------------------


def generate_architecture_overview(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "architecture_overview.png",
    *,
    default_output_dir=_default_output_dir,
) -> pathlib.Path | None:
    """Generate a three-panel figure showing fonds → rules → tools architecture."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename, default_output_dir=default_output_dir)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), facecolor=BG)
    panel_titles = (
        "Fonds (Data Pools)",
        "Rules (Specifications)",
        "Tools (Entrypoints)",
    )

    for ax, title, entries, color in zip(
        axes,
        panel_titles,
        [
            [("Bibliography", 8), ("Contacts", 5), ("Datasets", 5)],
            [("Project Rules", 4), ("Manuscript Rules", 4)],
            [("Code Executor", 2), ("Validator", 2), ("Skill", 2)],
        ],
        [BLUE, TEAL, BLUE_LIGHT],
        strict=True,
    ):
        ax.set_facecolor(WHITE)
        ax.set_title(title, fontsize=11, fontweight="bold", color=color, pad=12)
        labels_vals = [e[0] for e in entries]
        widths_vals = [e[1] for e in entries]
        y_pos = range(len(labels_vals))
        bars = ax.barh(
            y_pos,
            widths_vals,
            height=0.55,
            color=color,
            edgecolor="white",
            linewidth=0.5,
        )
        for bar, val in zip(bars, widths_vals, strict=True):
            ax.text(
                bar.get_width() + 0.3,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center",
                fontsize=9,
                color=NEUTRAL,
            )
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels_vals, fontsize=9)
        ax.tick_params(axis="x", colors=NEUTRAL, labelsize=8)
        ax.set_xlim(0, max(widths_vals) * 1.5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linewidth=0.4)

    fig.text(0.5, -0.02, "Resource Counts by Category", ha="center", fontsize=10, color=NEUTRAL)
    fig.suptitle(
        "Research Resource Architecture: Fonds × Rules × Tools",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
        y=1.02,
    )
    fig.tight_layout(pad=2)
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 2: Resource Counts — horizontal bar chart
# ---------------------------------------------------------------------------


def generate_resource_counts(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "resource_counts.png",
    counts: dict[str, int] | None = None,
    _data: object = None,
) -> pathlib.Path | None:
    """Generate a bar chart of resource counts."""
    if not _MPL_AVAILABLE:
        return None

    if counts is None:
        counts = {"Fonds": 3, "Tools": 3, "Rules": 2}

    dest = _resolve_output(output_dir, filename)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.set_facecolor(WHITE)

    names = list(counts.keys())
    vals = list(counts.values())
    colors_list = [BLUE, TEAL, BLUE_LIGHT, NEUTRAL, TEAL_LIGHT][: len(names)]

    bars = ax.bar(names, vals, color=colors_list, edgecolor="white", linewidth=1.2, width=0.55)
    for bar, val in zip(bars, vals, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.15,
            str(val),
            ha="center",
            fontsize=11,
            fontweight="bold",
            color=NEUTRAL,
        )

    ax.set_ylabel("Count", fontsize=10, color=NEUTRAL)
    ax.set_title(
        "Discovered Resources by Category",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
        pad=12,
    )
    ax.tick_params(colors=NEUTRAL, labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.4)
    ax.set_ylim(0, max(max(vals) * 1.4, 1) if vals else 5)
    fig.tight_layout()
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 3: Status Dashboard — component validation status
# ---------------------------------------------------------------------------


def generate_status_dashboard(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "status_dashboard.png",
    statuses: dict[str, str] | None = None,
    integration_result: object = None,
) -> pathlib.Path | None:
    """Generate a status dashboard of component validation results."""
    if not _MPL_AVAILABLE:
        return None

    if statuses is None:
        statuses = {
            "Bibliography Fond": "ok",
            "Contacts Fond": "ok",
            "Datasets Fond": "ok",
            "Project Rules": "ok",
            "Manuscript Rules": "ok",
            "Code Executor": "ok",
            "Validator": "ok",
            "Skill": "ok",
        }
    carried_statuses = getattr(integration_result, "statuses", None)
    if carried_statuses is not None:
        statuses = carried_statuses

    dest = _resolve_output(output_dir, filename)
    n = len(statuses)
    fig_height = max(3, n * 0.45)
    fig, ax = plt.subplots(figsize=(9, fig_height), facecolor=BG)
    ax.set_facecolor(WHITE)

    names = list(statuses.keys())
    colors_strip = [STATUS_COLORS.get(s, NEUTRAL) for s in statuses.values()]
    y_pos = range(n)

    bars = ax.barh(
        y_pos,
        [1] * n,
        height=0.65,
        color=colors_strip,
        edgecolor="white",
        linewidth=0.8,
    )
    for bar, name, st in zip(bars, names, statuses.values(), strict=True):
        label = STATUS_LABELS.get(st, st)
        ax.text(
            0.02,
            bar.get_y() + bar.get_height() / 2,
            name,
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )
        ax.text(
            0.98,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="right",
            fontsize=8,
            color="white",
            alpha=0.85,
        )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([""] * n)
    ax.set_xlim(0, 1)
    ax.set_title(
        "Component Validation Status",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
        pad=12,
    )
    ax.tick_params(colors=NEUTRAL, labelsize=8)
    ax.spines[:].set_visible(False)
    ax.set_xticks([])

    # Legend
    legend_patches = [
        mpatches.Patch(color=STATUS_COLORS.get(k, NEUTRAL), label=STATUS_LABELS.get(k, k))
        for k in ["ok", "partial", "missing"]
        if k in statuses.values() or k in STATUS_COLORS
    ]
    if legend_patches:
        ax.legend(handles=legend_patches, loc="lower right", framealpha=0.8, fontsize=8)

    fig.tight_layout()
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 4: Fond Taxonomy — schema comparison across the three fond types
# ---------------------------------------------------------------------------


def generate_fond_taxonomy(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "fond_taxonomy.png",
) -> pathlib.Path | None:
    """Generate a schema-comparison matrix across the three fond types."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)

    fonds = ["Bibliography", "Contacts", "Datasets"]
    fields: list[tuple[str, list[object]]] = [
        ("Manifest (`fonds.yaml`)", [True, True, True]),
        ("Required `type` field", [True, True, True]),
        ("Primary key", [True, True, True]),
        ("Source-of-truth format", ["BibTeX", "YAML", "YAML"]),
        ("Secondary mirror", ["CSV", "JSON", "—"]),
        ("Dedup key", ["cite key", "`id`", "`id`"]),
        ("Binary data committed", [False, False, False]),
    ]

    fig, ax = plt.subplots(figsize=(9, 0.62 * (len(fields) + 1) + 1), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, len(fonds) + 1.6)
    ax.set_ylim(0, len(fields) + 1)
    ax.axis("off")

    ax.text(
        0.05,
        len(fields) + 0.5,
        "Field",
        fontsize=10,
        fontweight="bold",
        color="#0f172a",
        va="center",
    )
    for i, name in enumerate(fonds):
        ax.text(
            1.6 + i + 0.5,
            len(fields) + 0.5,
            name,
            fontsize=10,
            fontweight="bold",
            color=[BLUE, TEAL, BLUE_LIGHT][i],
            va="center",
            ha="center",
        )
    ax.plot(
        [0, len(fonds) + 1.6], [len(fields) + 0.05, len(fields) + 0.05], color=GRID, linewidth=1.2
    )

    for row, (label, values) in enumerate(reversed(fields)):
        y = row + 0.5
        ax.text(0.05, y, label, fontsize=9, color="#0f172a", va="center")
        for i, val in enumerate(values):
            cx = 1.6 + i + 0.5
            if isinstance(val, bool):
                color = STATUS_COLORS["ok"] if val else STATUS_COLORS["missing"]
                marker = "✓" if val else "–"
                ax.text(
                    cx,
                    y,
                    marker,
                    fontsize=11,
                    fontweight="bold",
                    color=color,
                    va="center",
                    ha="center",
                )
            else:
                ax.text(cx, y, str(val), fontsize=8.5, color=NEUTRAL, va="center", ha="center")
        if row < len(fields) - 1:
            ax.plot([0, len(fonds) + 1.6], [y - 0.5, y - 0.5], color=GRID, linewidth=0.5)

    ax.set_title(
        "Fond Schema Taxonomy: Bibliography × Contacts × Datasets",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    fig.tight_layout()
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 6: Tool Contract — stdin/stdout/exit-code flow per tool
# ---------------------------------------------------------------------------


def generate_tool_contract(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "tool_contract.png",
) -> pathlib.Path | None:
    """Generate a flow diagram of the stdin/tool/stdout+exit-code contract."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    tools = [
        ("template_code_executor", "{code, language}", "{exit_code, stdout, stderr}"),
        ("template_validator", "document + schema paths", "human-readable report + exit code"),
        ("template_skill", "prompt string", "agent response text"),
    ]

    fig, axes = plt.subplots(len(tools), 1, figsize=(9, 1.5 * len(tools) + 0.5), facecolor=BG)
    if len(tools) == 1:
        axes = [axes]

    stage_colors = [BLUE_LIGHT, TEAL, BLUE]
    for ax, (name, stdin_label, stdout_label) in zip(axes, tools, strict=True):
        ax.set_facecolor(WHITE)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 2)
        ax.axis("off")

        stages = [
            ("stdin\n" + stdin_label, 1.4, NEUTRAL_LIGHT),
            (name, 5, stage_colors[0]),
            ("stdout / exit code\n" + stdout_label, 8.6, NEUTRAL_LIGHT),
        ]
        for i, (label, x, color) in enumerate(stages):
            width = 2.6 if i != 1 else 2.2
            ax.add_patch(
                mpatches.FancyBboxPatch(
                    (x - width / 2, 0.55),
                    width,
                    0.9,
                    boxstyle="round,pad=0.06",
                    facecolor=color,
                    edgecolor="none" if i == 1 else NEUTRAL_LIGHT,
                    linewidth=1.0,
                )
            )
            text_color = "white" if i == 1 else "#0f172a"
            ax.text(
                x,
                1.0,
                label,
                ha="center",
                va="center",
                color=text_color,
                fontsize=7.6,
                fontweight="bold" if i == 1 else "normal",
            )
            if i < len(stages) - 1:
                nxt_x = stages[i + 1][1]
                ax.annotate(
                    "",
                    xy=(nxt_x - (2.2 if i == 0 else 2.6) / 2 - 0.05, 1.0),
                    xytext=(x + width / 2 + 0.05, 1.0),
                    arrowprops={"arrowstyle": "-|>", "color": NEUTRAL, "linewidth": 1.4},
                )

    fig.suptitle(
        "Tool Invocation Contract: stdin → tool → stdout + exit code",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 7: Resilience Layers — three failure modes, three responses
# ---------------------------------------------------------------------------


def generate_resilience_layers(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "resilience_layers.png",
) -> pathlib.Path | None:
    """Generate a three-tier diagram of the integration layer's resilience design."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    layers = [
        (
            "Resource absence",
            "Fond / rule set / tool directory not yet created",
            "Return `None` / empty collection; log warning; continue",
        ),
        (
            "Schema malformation",
            "Manifest present but invalid YAML or missing fields",
            'Catch `yaml.YAMLError`; return degraded `status="partial"`',
        ),
        (
            "Script absence",
            "Tool declares entrypoints that do not exist on disk",
            "`validate_tool_scripts_exist()` reports `missing_scripts`",
        ),
    ]

    row_height = 1.55
    box_height = 1.3
    n = len(layers)
    fig, ax = plt.subplots(figsize=(9.5, 1.9 * n + 0.9), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, n * row_height + 0.5)
    ax.axis("off")

    colors_list = [BLUE, TEAL, BLUE_LIGHT]
    for i, (title, failure, response) in enumerate(layers):
        y = (n - i - 1) * row_height + 0.5 + box_height / 2
        width = 9.6 - i * 1.2
        x0 = (10 - width) / 2
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x0, y - box_height / 2),
                width,
                box_height,
                boxstyle="round,pad=0.07",
                facecolor=colors_list[i],
                edgecolor="none",
                alpha=0.92,
            )
        )
        ax.text(
            5,
            y + 0.42,
            f"Level {i + 1}: {title}",
            ha="center",
            va="center",
            color="white",
            fontsize=10,
            fontweight="bold",
        )
        ax.text(
            5, y + 0.06, failure, ha="center", va="center", color="white", fontsize=7.6, alpha=0.9
        )
        ax.text(
            5,
            y - 0.42,
            "→ " + response,
            ha="center",
            va="center",
            color="white",
            fontsize=7.4,
            style="italic",
            alpha=0.85,
        )

    ax.set_title(
        "Three-Level Resilience Design: Fail Informatively, Not Catastrophically",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    fig.tight_layout()
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 8: Pipeline Flow — the three-script orchestration sequence
# ---------------------------------------------------------------------------


def generate_pipeline_flow(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "pipeline_flow.png",
) -> pathlib.Path | None:
    """Generate a left-to-right flow diagram of the scripts/ orchestration sequence."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    stages = [
        ("01_validate_sources.py", "Validate presence + well-formedness", BLUE_LIGHT),
        ("02_run_integration.py", "run_integration_demo() → JSON summary", TEAL),
        ("03_generate_manuscript.py", "Write manuscript_variables.json", BLUE),
        ("04_validate_strong_rules.py", "Semantic strong-rule evaluation", NEUTRAL_LIGHT),
        ("05_generate_figures.py", "Render 8 figures + cover art", TEAL_LIGHT),
        ("z_generate_manuscript_...py", "Hydrate + inject {{TOKENS}}", BLUE_LIGHT),
        ("PDF render", "4-pass xelatex + bibtex", NEUTRAL),
    ]

    n = len(stages)
    step = 1.85
    box_w = 1.65
    fig, ax = plt.subplots(figsize=(2.0 * n, 3.4), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, n * step)
    ax.set_ylim(0, 2)
    ax.axis("off")

    for i, (name, desc, color) in enumerate(stages):
        cx = step / 2 + i * step
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (cx - box_w / 2, 0.55),
                box_w,
                0.9,
                boxstyle="round,pad=0.06",
                facecolor=color,
                edgecolor="none",
            )
        )
        ax.text(
            cx, 1.15, name, ha="center", va="center", color="white", fontsize=6.6, fontweight="bold"
        )
        ax.text(cx, 0.82, desc, ha="center", va="center", color="white", fontsize=5.8, alpha=0.92)
        if i < n - 1:
            ax.annotate(
                "",
                xy=(cx + step / 2 - 0.05, 1.0),
                xytext=(cx + box_w / 2 + 0.05, 1.0),
                arrowprops={"arrowstyle": "-|>", "color": NEUTRAL, "linewidth": 1.4},
            )

    ax.set_title(
        "Script Pipeline: Six Scripts, Each One Job, Ending in the Combined PDF",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    fig.tight_layout()
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Wrapper
# ---------------------------------------------------------------------------


def all_figures(
    output_dir: str | pathlib.Path | None = None,
    integration_result: object = None,
    counts: dict[str, int] | None = None,
    statuses: dict[str, str] | None = None,
) -> dict[str, pathlib.Path | None] | None:
    """Generate all figures (architecture + content + cover) and return {name: path}.

    *counts* and *statuses*, when provided, bind ``resource_counts`` and
    ``status_dashboard`` to real integration-run data instead of their
    illustrative defaults — see ``scripts/05_generate_figures.py`` for how
    they are derived from :func:`run_integration_demo`.

    Returns None if matplotlib is unavailable.
    """
    if not _MPL_AVAILABLE:
        return None

    if output_dir is not None:
        output_dir = pathlib.Path(output_dir)

    arch = generate_architecture_overview(output_dir=output_dir)
    counts_fig = generate_resource_counts(output_dir=output_dir, counts=counts)
    dash = generate_status_dashboard(
        output_dir=output_dir, statuses=statuses, integration_result=integration_result
    )
    taxonomy = generate_fond_taxonomy(output_dir=output_dir)
    rule_tree = generate_rule_hierarchy(output_dir=output_dir)
    tool_contract = generate_tool_contract(output_dir=output_dir)
    resilience = generate_resilience_layers(output_dir=output_dir)
    pipeline = generate_pipeline_flow(output_dir=output_dir)
    cover = generate_cover_art(output_dir=output_dir)

    return {
        "architecture_overview": arch,
        "resource_counts": counts_fig,
        "status_dashboard": dash,
        "fond_taxonomy": taxonomy,
        "rule_hierarchy": rule_tree,
        "tool_contract": tool_contract,
        "resilience_layers": resilience,
        "pipeline_flow": pipeline,
        "cover_art": cover,
    }


generate_all_figures = all_figures  # alias for script use
