"""Algorithm complexity figure generator with richer backend profiles and analysis functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from ..experiment_config import ExperimentConfig
from ..optimizer import quadratic_optimum
from ..viz_config import VIZ_CONFIG, agency_category
from ._common import experiment_config, get_logger, project_root


# ---------------------------------------------------------------------------
# Backend profile definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BackendProfile:
    """Descriptor for a gradient-descent backend variant.

    Captures the algorithmic parameters (Hessian conditioning, step-size
    regime) and the display metadata used in complexity figures.

    Attributes:
        name: Short human-readable identifier shown on plot labels.
        hessian_scale: Diagonal scaling applied to the identity Hessian,
            i.e. ``A = hessian_scale * I``.  Values >1 simulate ill-conditioned
            problems; values <1 give a "preconditioned" regime.
        description: One-line description for legends and figure annotations.
        color: Matplotlib-compatible colour used for this profile in overlaid
            plots.  Falls back to the primary VIZ_CONFIG colour if ``None``.
        max_stable_alpha: Largest step size still guaranteed to converge for
            this Hessian profile.  Equals ``2 / hessian_scale`` for a diagonal
            quadratic.
        label_alpha: Representative step size used in the complexity annotation
            panels.  Defaults to ``0.5 * max_stable_alpha``.
    """

    name: str
    hessian_scale: float
    description: str
    color: str | None = None
    max_stable_alpha: float | None = None
    label_alpha: float | None = None

    def effective_max_stable_alpha(self) -> float:
        """Return stability boundary α < 2/L where L = hessian_scale."""
        if self.max_stable_alpha is not None:
            return self.max_stable_alpha
        return 2.0 / self.hessian_scale if self.hessian_scale > 0 else float("inf")

    def effective_label_alpha(self) -> float:
        """Return the representative α for annotation overlays."""
        if self.label_alpha is not None:
            return self.label_alpha
        return 0.5 * self.effective_max_stable_alpha()


# Canonical registry of backend profiles shipped with the exemplar.
# Callers may substitute their own list; these represent the full range of
# quadratic conditioning regimes that appear in the manuscript figures.
BACKEND_PROFILES: tuple[BackendProfile, ...] = (
    BackendProfile(
        name="Identity (H=I)",
        hessian_scale=1.0,
        description="Well-conditioned, L=1 — canonical gradient descent",
        color=VIZ_CONFIG["colors"]["primary"],
    ),
    BackendProfile(
        name="Mild cond. (H=2I)",
        hessian_scale=2.0,
        description="Mild conditioning, L=2 — tighter stable region",
        color=VIZ_CONFIG["colors"]["secondary"],
    ),
    BackendProfile(
        name="Moderate cond. (H=5I)",
        hessian_scale=5.0,
        description="Moderate conditioning, L=5 — practitioner regime",
        color=VIZ_CONFIG["colors"]["tertiary"],
    ),
    BackendProfile(
        name="Ill-conditioned (H=10I)",
        hessian_scale=10.0,
        description="Ill-conditioned, L=10 — small-α only",
        color=VIZ_CONFIG["colors"]["quaternary"],
    ),
)


# ---------------------------------------------------------------------------
# Pure analysis functions
# ---------------------------------------------------------------------------


def compute_contraction_factor(alpha: float, hessian_scale: float = 1.0) -> float:
    """Compute the per-step contraction factor ρ = |1 − α · L|.

    For a quadratic ``f(x) = ½ xᵀ (L·I) x − bᵀx`` the gradient-descent update
    contracts the error by ``ρ = |1 − α L|`` each step.

    Args:
        alpha: Step size α > 0.
        hessian_scale: Lipschitz constant L > 0 (= largest eigenvalue of A).

    Returns:
        Contraction factor in [0, ∞).  Values < 1 guarantee convergence.
    """
    return float(abs(1.0 - alpha * hessian_scale))


def compute_theoretical_complexity(alpha: float, hessian_scale: float = 1.0) -> float:
    """Estimate iteration count to reduce error by 1/e from the linear rate bound.

    Uses the closed-form bound ``O(1 / (2α·L·(1 − α·L)))`` valid when
    ``0 < α < 2/L``.

    Args:
        alpha: Step size α > 0.
        hessian_scale: Lipschitz constant L > 0.

    Returns:
        Estimated iteration count (float), or ``inf`` when α is outside the
        stable regime ``(0, 2/L)``.
    """
    rho = compute_contraction_factor(alpha, hessian_scale)
    if 0.0 < rho < 1.0:
        return 1.0 / (2.0 * alpha * hessian_scale * (1.0 - rho))
    return float("inf")


def compute_complexity_profile(
    step_sizes: list[float],
    results: dict[float, Any],
    f_star: float,
    hessian_scale: float = 1.0,
) -> dict[str, list[Any]]:
    """Build per-step-size complexity metrics for one backend profile.

    Computes four parallel lists aligned with ``step_sizes``:
    - ``iterations``: empirical iteration counts from ``results``
    - ``log_errors``: ``log₁₀|f(xₖ) − f*|``
    - ``theoretical_complexity``: analytic bound from :func:`compute_theoretical_complexity`
    - ``contraction_factors``: per-step contraction from :func:`compute_contraction_factor`

    Args:
        step_sizes: Ordered list of step sizes (x-axis).
        results: Mapping ``{step_size: OptimizationResult}``.
        f_star: Optimal objective value used as reference for error.
        hessian_scale: Lipschitz constant L for the backend profile.

    Returns:
        Dict with keys ``iterations``, ``log_errors``, ``theoretical_complexity``,
        ``contraction_factors``.
    """
    iterations: list[int] = []
    log_errors: list[float] = []
    theoretical_complexity: list[float] = []
    contraction_factors: list[float] = []

    for alpha in step_sizes:
        result = results[alpha]
        iterations.append(int(result.iterations))

        obj_val = float(result.objective_value)
        err = abs(obj_val - f_star)
        log_errors.append(float(np.log10(max(err, 1e-16))))

        theoretical_complexity.append(compute_theoretical_complexity(alpha, hessian_scale))
        contraction_factors.append(compute_contraction_factor(alpha, hessian_scale))

    return {
        "iterations": iterations,
        "log_errors": log_errors,
        "theoretical_complexity": theoretical_complexity,
        "contraction_factors": contraction_factors,
    }


def profile_stable_region(profile: BackendProfile) -> tuple[float, float]:
    """Return ``(alpha_min, alpha_max)`` of the strictly stable step-size interval.

    The stable region for gradient descent on a quadratic with Lipschitz
    constant ``L`` is ``(0, 2/L)``.  ``alpha_min`` is always ``0.0``.

    Args:
        profile: Backend profile to interrogate.

    Returns:
        Tuple ``(0.0, 2/L)``.
    """
    return (0.0, profile.effective_max_stable_alpha())


def optimal_step_size(profile: BackendProfile) -> float:
    """Return the theoretically optimal step size ``α* = 1/L``.

    For a quadratic with eigenvalues bounded by ``L``, the step ``α = 1/L``
    minimises the contraction factor giving ``ρ = 0`` and single-step
    convergence.

    Args:
        profile: Backend profile.

    Returns:
        Optimal step size ``1/L``.
    """
    return 1.0 / profile.hessian_scale


def compare_profiles_at_alpha(
    alpha: float,
    profiles: tuple[BackendProfile, ...] = BACKEND_PROFILES,
) -> list[dict[str, Any]]:
    """Compare all backend profiles at a single step size.

    Useful for manuscript tables and quick cross-profile sanity checks.

    Args:
        alpha: Step size to evaluate.
        profiles: Profiles to compare (defaults to :data:`BACKEND_PROFILES`).

    Returns:
        List of dicts with keys ``name``, ``hessian_scale``, ``alpha``,
        ``contraction``, ``theoretical_complexity``, ``optimal_alpha``,
        ``is_stable``.
    """
    rows: list[dict[str, Any]] = []
    for p in profiles:
        rho = compute_contraction_factor(alpha, p.hessian_scale)
        tc = compute_theoretical_complexity(alpha, p.hessian_scale)
        rows.append(
            {
                "name": p.name,
                "hessian_scale": p.hessian_scale,
                "alpha": alpha,
                "contraction": rho,
                "theoretical_complexity": tc,
                "optimal_alpha": optimal_step_size(p),
                "is_stable": rho < 1.0,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------


def _annotate_bars(
    ax: Any,
    bars: Any,
    values: list[float | int],
    *,
    fmt: str = "{:.1f}",
    offset_frac: float = 0.03,
) -> None:
    """Place value labels above/below each bar in a bar chart."""
    scale = max(abs(v) for v in values) if values else 1.0
    for bar, val in zip(bars, values):
        h = bar.get_height()
        sign = 1 if h >= 0 else -1
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + sign * scale * offset_frac,
            fmt.format(val),
            ha="center",
            va="bottom" if h >= 0 else "top",
            fontsize=9,
            fontweight="bold",
        )


def generate_complexity_visualization(
    results: Any,
    config: ExperimentConfig | None = None,
    *,
    profiles: tuple[BackendProfile, ...] = BACKEND_PROFILES,
) -> Any:
    """Generate algorithm performance analysis with six informative panels.

    The figure extends the original four-panel layout with two new panels:

    - Panel 1: Empirical convergence iterations (bar chart, colour-coded by
      agency category).
    - Panel 2: Solution accuracy as ``log₁₀|f(xₖ) − f*|`` (bar chart).
    - Panel 3: Theoretical vs empirical complexity on a log scale (line chart).
    - Panel 4: Per-step contraction factor ρ across step sizes (bar chart).
    - Panel 5: **Stable region width** per backend profile — shows how many
      valid step sizes exist below the ``2/L`` boundary (bar chart).
    - Panel 6: **Cross-profile contraction overlay** — plots ρ(α) curves for
      each backend profile so readers can see how conditioning shrinks the safe
      regime (line chart).

    Args:
        results: Mapping ``{step_size: OptimizationResult}`` from an experiment
            run.
        config: Optional :class:`ExperimentConfig`; loaded from config.yaml if
            not supplied.
        profiles: Backend profiles used for Panels 5 and 6.  Defaults to
            :data:`BACKEND_PROFILES`.

    Returns:
        ``pathlib.Path`` of the saved PNG figure.
    """
    logger = get_logger()
    logger.info("Generating algorithm complexity visualization...")

    cfg = config or experiment_config()
    conv_tol = float(cfg.convergence_tolerance)
    log_tol = float(np.log10(conv_tol))
    _, f_star = quadratic_optimum(cfg.A_array(), cfg.b_array())

    step_sizes = list(results.keys())

    # Primary profile (first in list — assumed H=I for the main experiment).
    primary_profile = profiles[0]
    profile_data = compute_complexity_profile(
        step_sizes,
        results,
        f_star,
        hessian_scale=primary_profile.hessian_scale,
    )
    iterations = profile_data["iterations"]
    log_errors = profile_data["log_errors"]
    theoretical_complexity = profile_data["theoretical_complexity"]
    contraction_factors = profile_data["contraction_factors"]

    # -----------------------------------------------------------------------
    # Build figure (3 × 2 grid → 6 panels)
    # -----------------------------------------------------------------------
    bar_color = VIZ_CONFIG["colors"]["primary"]
    theory_color = VIZ_CONFIG["colors"]["secondary"]
    success_color = VIZ_CONFIG["colors"]["success"]
    quaternary_color = VIZ_CONFIG["colors"]["quaternary"]

    fig, axes = plt.subplots(3, 2, figsize=(14, 16))
    ax1, ax2 = axes[0]
    ax3, ax4 = axes[1]
    ax5, ax6 = axes[2]

    fig.suptitle(
        "Algorithm Performance Analysis\nGradient Descent Convergence Characteristics",
        fontsize=14,
        fontweight="bold",
        y=1.01,
    )

    # ------------------------------------------------------------------
    # Panel 1 — Empirical convergence iterations
    # ------------------------------------------------------------------
    bar_colors = [agency_category(s)[1] for s in step_sizes]
    bars1 = ax1.bar(
        range(len(step_sizes)),
        iterations,
        tick_label=[f"α={s}" for s in step_sizes],
        color=bar_colors,
        alpha=0.85,
    )
    ax1.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Iterations", fontsize=11, fontweight="medium")
    ax1.set_title("Empirical Convergence Iterations", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3, axis="y")
    _annotate_bars(ax1, bars1, iterations, fmt="{:.0f}")

    # ------------------------------------------------------------------
    # Panel 2 — Solution accuracy (log error)
    # ------------------------------------------------------------------
    bar_colors_2 = [success_color if le < log_tol else theory_color if le < -3 else bar_color for le in log_errors]
    bars2 = ax2.bar(
        range(len(step_sizes)),
        log_errors,
        tick_label=[f"α={s}" for s in step_sizes],
        color=bar_colors_2,
        alpha=0.85,
    )
    ax2.axhline(
        y=log_tol,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label=f"ε = {conv_tol:.0e} tolerance",
    )
    ax2.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax2.set_ylabel("log₁₀ |f(x) − f(x*)|")
    ax2.set_title("Solution Accuracy\n(Lower = More Accurate)", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax2.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars2, log_errors):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            min(val, 0) - 0.5,
            f"{val:.1f}",
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
        )

    # ------------------------------------------------------------------
    # Panel 3 — Theoretical vs empirical complexity (log scale)
    # ------------------------------------------------------------------
    ax3.semilogy(
        step_sizes,
        iterations,
        color=bar_color,
        linewidth=2.5,
        marker="o",
        markersize=10,
        markerfacecolor="white",
        markeredgewidth=2,
        label="Empirical",
    )
    ax3.semilogy(
        step_sizes,
        theoretical_complexity,
        color=theory_color,
        linestyle="--",
        linewidth=2,
        marker="^",
        markersize=8,
        label="Theoretical 1/(2α·L·(1−αL))",
    )
    ax3.set_xlabel("Step Size (α)", fontsize=11, fontweight="medium")
    ax3.set_ylabel("Iterations (log)", fontsize=11, fontweight="medium")
    ax3.set_title("Theoretical vs Empirical Complexity", fontsize=12, fontweight="bold")
    ax3.legend(loc="upper right", framealpha=0.95, fontsize=9)
    ax3.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # Panel 4 — Contraction factor per step size
    # ------------------------------------------------------------------
    bars4 = ax4.bar(
        range(len(step_sizes)),
        contraction_factors,
        tick_label=[f"α={s}" for s in step_sizes],
        color=quaternary_color,
        alpha=0.85,
    )
    ax4.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax4.set_ylabel("Contraction Factor ρ", fontsize=11, fontweight="medium")
    ax4.set_title(
        f"Error Contraction per Step ({primary_profile.name})\nρ = |1 − αL|  (smaller ρ ⇒ faster)",
        fontsize=12,
        fontweight="bold",
    )
    ax4.set_ylim(0, max(1.05, max(contraction_factors, default=1.0) * 1.15))
    ax4.axhline(
        y=1.0,
        color=VIZ_CONFIG["colors"]["error"],
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label="ρ = 1 (divergence boundary)",
    )
    opt_alpha = optimal_step_size(primary_profile)
    ax4.axvline(
        x=step_sizes.index(min(step_sizes, key=lambda a: abs(a - opt_alpha))) if step_sizes else 0,
        color=VIZ_CONFIG["colors"]["success"],
        linestyle=":",
        linewidth=1.5,
        alpha=0.7,
        label=f"α* = {opt_alpha:.3g}",
    )
    ax4.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax4.grid(True, alpha=0.3, axis="y")
    _annotate_bars(ax4, bars4, contraction_factors, fmt="{:.3f}")

    # ------------------------------------------------------------------
    # Panel 5 — Stable region width per backend profile (NEW)
    # ------------------------------------------------------------------
    profile_names = [p.name for p in profiles]  # noqa: F841  — available for callers who extend this
    stable_widths = [p.effective_max_stable_alpha() for p in profiles]
    optimal_alphas = [optimal_step_size(p) for p in profiles]
    profile_colors = [p.color or VIZ_CONFIG["colors"]["primary"] for p in profiles]

    bars5 = ax5.bar(
        range(len(profiles)),
        stable_widths,
        tick_label=[p.name for p in profiles],
        color=profile_colors,
        alpha=0.80,
        label="Stable width 2/L",
    )
    ax5.bar(
        range(len(profiles)),
        optimal_alphas,
        color=profile_colors,
        alpha=0.35,
        hatch="///",
        label="Optimal α* = 1/L",
    )
    ax5.set_xlabel("Backend Profile", fontsize=11, fontweight="medium")
    ax5.set_ylabel("Step Size (α)", fontsize=11, fontweight="medium")
    ax5.set_title(
        "Stable Region Width per Backend Profile\n2/L boundary and optimal α* = 1/L",
        fontsize=12,
        fontweight="bold",
    )
    ax5.tick_params(axis="x", labelrotation=15, labelsize=8)
    ax5.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax5.grid(True, alpha=0.3, axis="y")
    _annotate_bars(ax5, bars5, stable_widths, fmt="{:.3g}")

    # ------------------------------------------------------------------
    # Panel 6 — Cross-profile contraction overlay (NEW)
    # ------------------------------------------------------------------
    alpha_fine = np.linspace(0.001, max(stable_widths) * 1.05, 300)
    for p in profiles:
        rho_curve = [compute_contraction_factor(float(a), p.hessian_scale) for a in alpha_fine]
        color = p.color or VIZ_CONFIG["colors"]["primary"]
        ax6.plot(
            alpha_fine,
            rho_curve,
            color=color,
            linewidth=2,
            label=f"{p.name}",
        )
        # Mark stable boundary
        boundary = p.effective_max_stable_alpha()
        ax6.axvline(
            x=boundary,
            color=color,
            linestyle=":",
            linewidth=1,
            alpha=0.5,
        )

    ax6.axhline(
        y=1.0,
        color=VIZ_CONFIG["colors"]["error"],
        linestyle="--",
        linewidth=1.5,
        alpha=0.8,
        label="ρ = 1 (divergence)",
    )
    ax6.set_xlabel("Step Size (α)", fontsize=11, fontweight="medium")
    ax6.set_ylabel("Contraction Factor ρ = |1 − αL|", fontsize=11, fontweight="medium")
    ax6.set_title(
        "Cross-Profile Contraction Curves\nDotted verticals = 2/L stability boundary",
        fontsize=12,
        fontweight="bold",
    )
    ax6.legend(loc="upper left", fontsize=8, framealpha=0.95)
    ax6.grid(True, alpha=0.3)
    ax6.set_ylim(0, 2.1)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    plt.tight_layout()
    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "algorithm_complexity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info("Saved algorithm complexity visualization to: %s", plot_path)
    return plot_path


__all__ = [
    "BACKEND_PROFILES",
    "BackendProfile",
    "compare_profiles_at_alpha",
    "compute_complexity_profile",
    "compute_contraction_factor",
    "compute_theoretical_complexity",
    "generate_complexity_visualization",
    "optimal_step_size",
    "profile_stable_region",
]
