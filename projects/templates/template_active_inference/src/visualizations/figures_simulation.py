"""Simulation-mechanism publication figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .figure_helpers import add_note, add_value_labels, configure_axis, save_styled_figure
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def figure_efe_decomposition(project_root: Path) -> Path:
    """Expected Free Energy term decomposition across T-maze policies.

    Left panel: ``G(pi) = risk + ambiguity`` as a stacked bar per policy, with the
    EFE-minimising policy marked. Right panel: the equal-and-opposite
    ``G(pi) = -(pragmatic_value + epistemic_value)`` decomposition. Computed in
    closed form (no sampling) so the figure is byte-deterministic.
    """
    from simulation.efe_decomposition import decompose_all_policies
    from simulation.tmaze_model import build_tmaze_generative_model

    root = project_root.resolve()
    style = load_figure_style(root)
    result = decompose_all_policies(build_tmaze_generative_model())
    rows = result["rows"]
    labels = ["".join(str(a) for a in row["policy"]) for row in rows]
    risk = [float(row["risk"]) for row in rows]
    ambiguity = [float(row["ambiguity"]) for row in rows]
    pragmatic = [float(row["pragmatic_value"]) for row in rows]
    epistemic = [float(row["epistemic_value"]) for row in rows]
    totals = [r + a for r, a in zip(risk, ambiguity)]
    best_label = "".join(str(a) for a in result["efe_minimizing_policy"])
    best_idx = labels.index(best_label)
    x = np.arange(len(labels))

    out = figure_output_path(root, "efe_decomposition")
    with apply_style(style):
        fig, (ax_g, ax_pe) = plt.subplots(1, 2, figsize=(9.5, 4))
        ax_g.bar(x, risk, color=style.color("secondary"), label="risk (pragmatic deviation)")
        ax_g.bar(x, ambiguity, bottom=risk, color=style.color("accent"), label="ambiguity (epistemic)")
        ax_g.scatter(
            [x[best_idx]],
            [totals[best_idx]],
            color=style.color("fail"),
            zorder=3,
            s=45,
            label=f"min G at policy {best_label}",
        )
        ax_g.set_xticks(x)
        ax_g.set_xticklabels(labels)
        configure_axis(
            ax_g,
            style,
            title=r"$G(\pi)$ = risk + ambiguity",
            xlabel="Policy (action sequence)",
            ylabel="Expected free energy (nats)",
        )
        for idx, total in enumerate(totals):
            ax_g.text(
                idx,
                total + 0.015,
                f"{total:.2f}",
                ha="center",
                va="bottom",
                fontsize=style.text_size("annotation"),
            )
        ax_g.legend(frameon=False, fontsize=style.text_size("legend"))

        width = 0.4
        ax_pe.bar(x - width / 2, pragmatic, width, color=style.color("primary"), label="pragmatic value")
        ax_pe.bar(x + width / 2, epistemic, width, color=style.color("muted"), label="epistemic value")
        ax_pe.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        ax_pe.set_xticks(x)
        ax_pe.set_xticklabels(labels)
        configure_axis(
            ax_pe,
            style,
            title=r"$G(\pi)$ = -(pragmatic + epistemic)",
            xlabel="Policy (action sequence)",
            ylabel="Value (nats)",
        )
        ax_pe.legend(frameon=False, fontsize=style.text_size("legend"))
        add_note(ax_pe, f"identity residual <= {float(result['max_identity_residual']):.1e}", style, x=0.05, y=0.95)

        save_styled_figure(fig, out, style)
    return out


def figure_precision_sweep(project_root: Path) -> Path:
    """Policy-posterior sharpening as precision (gamma) increases.

    Left axis: Shannon entropy ``H[q]`` of ``q(pi) = softmax(-gamma G)`` vs gamma,
    with the ``ln(|optimal set|)`` saturation floor marked. Right axis: the EFE
    optimal-set mass vs gamma, with the precision at which it crosses the
    selection threshold marked. Computed in closed form (no sampling), so the
    figure is byte-deterministic.
    """
    from simulation.precision_sweep import sweep_precision
    from simulation.tmaze_model import build_tmaze_generative_model

    root = project_root.resolve()
    style = load_figure_style(root)
    result = sweep_precision(build_tmaze_generative_model())
    rows = result["rows"]
    gammas = [float(r["gamma"]) for r in rows]
    entropy = [float(r["entropy"]) for r in rows]
    opt_mass = [float(r["optimal_set_mass"]) for r in rows]
    floor = float(result["entropy_floor"])
    threshold = float(result["selection_mass_threshold"])
    gamma_det = result["gamma_deterministic_selection"]

    out = figure_output_path(root, "precision_sweep")
    with apply_style(style):
        fig, ax_h = plt.subplots(figsize=(7.5, 4))
        ax_h.plot(gammas, entropy, color=style.color("secondary"), marker="o", markersize=3, label="entropy H[q]")
        ax_h.axhline(
            floor,
            color=style.color("reference"),
            linewidth=0.9,
            linestyle="--",
            label=r"floor $\ln|\Pi^\star|$",
        )
        configure_axis(
            ax_h,
            style,
            title=r"Precision sharpens policy posterior $q(\pi)=\mathrm{softmax}(-\gamma G)$",
            xlabel=r"Precision $\gamma$ (inverse temperature)",
            ylabel="Posterior entropy (nats)",
        )

        ax_m = ax_h.twinx()
        ax_m.plot(gammas, opt_mass, color=style.color("accent"), marker="s", markersize=3, label="optimal-set mass")
        ax_m.axhline(threshold, color=style.color("muted"), linewidth=0.8, linestyle=":")
        ax_m.set_ylabel("EFE optimal-set mass")
        ax_m.set_ylim(0.0, 1.02)
        if gamma_det is not None:
            ax_m.scatter(
                [float(gamma_det)],
                [threshold],
                color=style.color("fail"),
                zorder=3,
                s=45,
                label=rf"mass $\geq$ {threshold:g} at $\gamma$={float(gamma_det):g}",
            )
            ax_h.axvline(float(gamma_det), color=style.color("fail"), linewidth=0.8, linestyle=":")

        lines_h, labels_h = ax_h.get_legend_handles_labels()
        lines_m, labels_m = ax_m.get_legend_handles_labels()
        ax_h.legend(
            lines_h + lines_m,
            labels_h + labels_m,
            frameon=False,
            fontsize=style.text_size("legend"),
            loc="upper right",
        )
        add_note(ax_h, f"{result['optimal_set_size']} tied optima create the entropy floor.", style, x=0.04, y=0.23)

        save_styled_figure(fig, out, style)
    return out


def figure_cue_tmaze_advantage(project_root: Path) -> Path:
    """Epistemic necessity in the cue-then-reward T-maze.

    Left panel: cue information gain I(context; o_cue) > 0 and the measured
    behavioural advantage (epistemic vs greedy expected reward log-preference).
    Right panel: the documented flat-EFE blind spot -- decompose_policy_efe scores
    the cue-first and greedy policies identically, so the sophisticated evaluator
    is what makes epistemic value strictly necessary. Closed form (no sampling),
    byte-deterministic.
    """
    from simulation.cue_tmaze_model import compare_cue_vs_greedy

    root = project_root.resolve()
    style = load_figure_style(root)
    adv = compare_cue_vs_greedy()

    out = figure_output_path(root, "cue_tmaze_advantage")
    with apply_style(style):
        fig, (ax_adv, ax_flat) = plt.subplots(1, 2, figsize=(9.5, 4))

        adv_labels = ["cue info gain\nI(ctx;o)", "epistemic\nreward", "greedy\nreward"]
        adv_values = [
            adv.cue_information_gain,
            adv.epistemic_reward_log_pref,
            adv.greedy_reward_log_pref,
        ]
        adv_colors = [style.color("accent"), style.color("pass"), style.color("fail")]
        bars = ax_adv.bar(np.arange(3), adv_values, color=adv_colors)
        ax_adv.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        ax_adv.set_xticks(np.arange(3))
        ax_adv.set_xticklabels(adv_labels, fontsize=style.text_size("tick"))
        configure_axis(
            ax_adv,
            style,
            title=f"Cue is required: +{adv.behavioral_advantage:.2f} nat advantage",
            ylabel="Value (nats)",
            title_loc="left",
            title_size=style.text_size("subtitle"),
        )
        add_value_labels(ax_adv, bars)

        flat_values = [adv.flat_efe_cue, adv.flat_efe_greedy]
        flat_bars = ax_flat.bar(
            ["cue-first\npolicy", "greedy\npolicy"],
            flat_values,
            color=[style.color("secondary"), style.color("muted")],
        )
        configure_axis(
            ax_flat,
            style,
            title=f"Flat EFE blind spot: {'identical' if adv.flat_efe_indistinguishable else 'differs'}",
            ylabel="Flat EFE $G(\\pi)$ (nats)",
            title_loc="left",
            title_size=style.text_size("subtitle"),
        )
        add_value_labels(ax_flat, flat_bars)

        save_styled_figure(fig, out, style)
    return out


def figure_dirichlet_convergence(project_root: Path) -> Path:
    """KL(true A || learned A) versus Dirichlet update step (log-y).

    The deterministic Dirichlet likelihood-learning run drives the expected
    likelihood toward the true T-maze ``A``; the per-step KL falls monotonically
    toward zero. Computed in closed form (fixed expected-count stream, no
    sampling) so the figure is byte-deterministic.
    """
    from simulation.dirichlet_learning import CONVERGENCE_KL_ATOL, summarize_learning
    from simulation.tmaze_model import build_tmaze_generative_model

    root = project_root.resolve()
    style = load_figure_style(root)
    summary = summarize_learning(build_tmaze_generative_model())
    kls = [float(v) for v in summary["kl_trajectory"]]
    steps = np.arange(len(kls))
    converge_step = int(summary["steps_to_converge"])

    out = figure_output_path(root, "dirichlet_convergence")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(7, 3.6))
        ax.semilogy(steps, kls, marker="o", color=style.color("primary"), linewidth=2, label="KL(true || learned)")
        ax.axhline(
            CONVERGENCE_KL_ATOL,
            color=style.color("reference"),
            linewidth=1,
            linestyle="--",
            label=f"convergence tol {CONVERGENCE_KL_ATOL:g}",
        )
        if converge_step < len(kls):
            ax.scatter(
                [steps[converge_step]],
                [kls[converge_step]],
                color=style.color("pass"),
                zorder=3,
                s=45,
                label=f"converged at step {converge_step}",
            )
        configure_axis(
            ax,
            style,
            title="Dirichlet likelihood learning converges to true A",
            xlabel="Dirichlet update step",
            ylabel="KL to true likelihood (nats)",
            integer_x=True,
        )
        ax.legend(frameon=False, fontsize=style.text_size("legend"))
        add_note(ax, f"final KL={kls[-1]:.2e}; deterministic expected-count stream", style, x=0.48, y=0.95, width=36)
        save_styled_figure(fig, out, style)
    return out
