"""Security figure writers for the AutoResearch exemplar."""

from __future__ import annotations

from pathlib import Path

from .figures_core import _float_value, _mapping_list, palette_color, save_figure, styled_grid


def write_security_control_matrix_figure(figures_dir: Path, threat_model: dict[str, object]) -> Path:
    """Write the local security control matrix."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_security_control_matrix.png"
    controls = _mapping_list(threat_model.get("controls"))
    labels = [str(row.get("id", "control")).removeprefix("ctrl-") for row in controls]
    frameworks = [str(row.get("framework", "framework")).replace("_", " ") for row in controls]
    statuses = [str(row.get("status", "unknown")) for row in controls]

    ink = palette_color("ink", "#0f172a")
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.set_axis_off()
    ax.set_title("Local security controls by evidence surface", fontsize=12, pad=12)
    columns = (
        ("Control", 0.03, 0.24),
        ("Evidence surface", 0.29, 0.28),
        ("Framework cue", 0.61, 0.22),
        ("Status", 0.86, 0.11),
    )
    header_y = 0.91
    for header, x_pos, _width in columns:
        ax.text(x_pos, header_y, header, transform=ax.transAxes, fontsize=9, fontweight="bold", va="center")
    ax.hlines(
        header_y - 0.04, 0.02, 0.98, transform=ax.transAxes, color=palette_color("rule", "#94a3b8"), linewidth=1.0
    )

    row_top = 0.81
    row_gap = 0.105 if controls else 0.1
    for index, row in enumerate(controls):
        y_pos = row_top - index * row_gap
        fill = palette_color("box_face", "#f8fafc") if index % 2 == 0 else palette_color("row_alt", "#eef6f8")
        ax.add_patch(
            plt.Rectangle(
                (0.02, y_pos - 0.037),
                0.96,
                0.074,
                transform=ax.transAxes,
                facecolor=fill,
                edgecolor=palette_color("row_edge", "#e2e8f0"),
                linewidth=0.5,
            )
        )
        status = statuses[index]
        implemented = status == "implemented"
        status_fill = palette_color("ok_fill", "#d1fae5") if implemented else palette_color("warn_fill", "#fef3c7")
        status_edge = palette_color("positive", "#0f766e") if implemented else palette_color("warning", "#a16207")
        status_text = "implemented" if implemented else status
        ax.text(0.03, y_pos, labels[index], transform=ax.transAxes, fontsize=8.2, va="center", color=ink)
        ax.text(
            0.29,
            y_pos,
            str(row.get("evidence_key", "evidence")).replace("_", " "),
            transform=ax.transAxes,
            fontsize=8.2,
            va="center",
            color=ink,
        )
        ax.text(0.61, y_pos, frameworks[index], transform=ax.transAxes, fontsize=8.2, va="center", color=ink)
        ax.text(
            0.86,
            y_pos,
            status_text,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=7.8,
            color=palette_color("ok_ink", "#064e3b") if implemented else palette_color("warn_ink", "#713f12"),
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": status_fill,
                "edgecolor": status_edge,
                "linewidth": 0.8,
            },
        )
    ax.text(
        0.98,
        0.045,
        "local checksum and review controls only",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=8,
        color=palette_color("annotation", "#475569"),
    )
    fig.tight_layout()
    return save_figure(fig, path)


def write_security_integrity_chain_figure(figures_dir: Path, attestation: dict[str, object]) -> Path:
    """Write the local integrity attestation chain figure."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_integrity_chain.png"
    chain = (
        ("Inputs", "fixture + config"),
        ("Analysis", "deterministic loop"),
        ("Artifacts", "data + figures"),
        ("Checksums", "sha256"),
        ("Review", str(attestation.get("status", "pending"))),
    )
    box_face = palette_color("box_face", "#f8fafc")
    ok_face = palette_color("ok_face", "#ecfdf5")
    box_edge = palette_color("box_edge", "#334155")
    arrow_color = palette_color("arrow", "#475569")
    fig, (ax_chain, ax_counts) = plt.subplots(2, 1, figsize=(9.0, 4.6), gridspec_kw={"height_ratios": [1.4, 1.0]})
    ax_chain.set_axis_off()
    x_positions = [index / (len(chain) - 1) for index in range(len(chain))]
    for index, ((title, detail), x_pos) in enumerate(zip(chain, x_positions, strict=True)):
        facecolor = ok_face if title == "Review" and attestation.get("status") == "passed" else box_face
        ax_chain.text(
            x_pos,
            0.55,
            f"{title}\n{detail}",
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": facecolor,
                "edgecolor": box_edge,
                "linewidth": 1.0,
            },
        )
        if index < len(chain) - 1:
            ax_chain.annotate(
                "",
                xy=(x_positions[index + 1] - 0.07, 0.55),
                xytext=(x_pos + 0.07, 0.55),
                arrowprops={"arrowstyle": "->", "color": arrow_color, "linewidth": 1.2},
            )
    ax_chain.set_title("Local artifact integrity chain", fontsize=12, pad=8)

    labels = ("checked", "missing", "mismatch")
    values = (
        int(_float_value(attestation.get("checked_count", 0))),
        int(_float_value(attestation.get("missing_count", 0))),
        int(_float_value(attestation.get("mismatch_count", 0))),
    )
    colors = (
        palette_color("positive", "#0f766e"),
        palette_color("warning", "#a16207"),
        palette_color("negative", "#7c2d12"),
    )
    bars = ax_counts.bar(labels, values, color=colors)
    ax_counts.set_ylabel("file records")
    styled_grid(ax_counts, "y")
    ax_counts.set_axisbelow(True)
    ax_counts.set_ylim(0, max(values) + 1)
    for bar, value in zip(bars, values, strict=True):
        ax_counts.text(bar.get_x() + bar.get_width() / 2.0, value + 0.05, str(value), ha="center", fontsize=8)
    ax_counts.text(
        0.99,
        0.86,
        "no external signature",
        transform=ax_counts.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color=palette_color("annotation", "#475569"),
    )
    for spine in ax_counts.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return save_figure(fig, path)


__all__ = [
    "write_security_control_matrix_figure",
    "write_security_integrity_chain_figure",
]
