"""contract.py — Figure 6: Tool Contract — stdin/stdout/exit-code flow per tool."""

from __future__ import annotations

import pathlib

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    BLUE,
    BLUE_LIGHT,
    NEUTRAL,
    NEUTRAL_LIGHT,
    TEAL,
    WHITE,
    _resolve_output,
    _save,
    mpatches,
    plt,
)

__all__ = [
    "generate_tool_contract",
]


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
