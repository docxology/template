#!/usr/bin/env python3
"""Monte Carlo reference distribution for rational proximity statistics (thin orchestrator)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

project_root = Path(
    os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent)
).resolve()

os.environ.setdefault("MPLBACKEND", "Agg")

# Analysis imports (src/ on PYTHONPATH via pipeline or local dev)
sys.path.insert(0, str(project_root / "src"))

import matplotlib.pyplot as plt
import numpy as np
import yaml

from constants import constant_lookup, named_constants
from sampling import beta_unit_samples, random_quadratic_mod1, uniform_unit_samples
from statistics_compare import (
    batch_min_q_squared_errors,
    batch_min_rational_distances,
    compare_constant_table,
    reference_distribution_summary,
)

try:
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

DEFAULT_QUADRATIC_CANDIDATES = [2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19]

# (registry key, color, legend label) — same markers on all proximity figures for comparability
_FIGURE_MARKERS: tuple[tuple[str, str, str], ...] = (
    ("pi", "#276749", "pi"),
    ("e", "#dd6b20", "e"),
    ("golden_ratio", "#c05621", "golden_ratio"),
    ("sqrt2", "#805ad5", "sqrt2"),
    ("sqrt3", "#2b6cb0", "sqrt3"),
    ("ln2", "#2d3748", "ln2"),
)


def _log10_delta(dist: np.ndarray) -> np.ndarray:
    return np.log10(np.maximum(dist, 1e-18))


def _log10_mu(q2: np.ndarray) -> np.ndarray:
    return np.log10(np.maximum(q2, 1e-18))


def _apply_figure_style() -> None:
    plt.grid(True, alpha=0.35, linestyle="--", linewidth=0.7)


def _mark_constants_delta(
    lookup: dict[str, float],
    q_max: int,
    *,
    compare_mod1: bool,
) -> None:
    for key, color, label in _FIGURE_MARKERS:
        if key not in lookup:
            continue
        xv = float(lookup[key])
        if compare_mod1:
            xv = xv - np.floor(xv)
        d = float(batch_min_rational_distances(np.array([xv]), q_max)[0])
        plt.axvline(
            _log10_delta(np.array([d]))[0],
            color=color,
            linewidth=1.6,
            label=f"{label}",
        )


def _mark_constants_mu(
    lookup: dict[str, float],
    q_max: int,
    *,
    compare_mod1: bool,
) -> None:
    for key, color, label in _FIGURE_MARKERS:
        if key not in lookup:
            continue
        xv = float(lookup[key])
        if compare_mod1:
            xv = xv - np.floor(xv)
        m = float(batch_min_q_squared_errors(np.array([xv]), q_max)[0])
        plt.axvline(
            _log10_mu(np.array([m]))[0],
            color=color,
            linewidth=1.6,
            label=f"{label}",
        )


def _load_experiment_config(project_root: Path) -> dict:
    path = project_root / "manuscript" / "config.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_pooled_reference_1d(
    rng: np.random.Generator,
    n_uniform: int,
    n_quadratic: int,
    n_beta: int,
    beta_a: float,
    beta_b: float,
    quadratic_candidates: list[int],
) -> np.ndarray:
    u = uniform_unit_samples(n_uniform, rng)
    qref = random_quadratic_mod1(quadratic_candidates, rng, n_quadratic)
    chunks: list[np.ndarray] = [u, qref]
    if n_beta > 0:
        chunks.append(beta_unit_samples(n_beta, beta_a, beta_b, rng))
    return np.concatenate(chunks)


def run_proximity_study(
    project_dir: Path,
    seed: int = 20260322,
    q_max: int = 120,
    n_uniform: int = 4000,
    n_quadratic: int = 2000,
    n_beta: int = 0,
    beta_a: float = 0.5,
    beta_b: float = 0.5,
    quadratic_candidates: list[int] | None = None,
    compare_mod1: bool = False,
    q_sensitivity: list[int] | None = None,
) -> dict[str, Any]:
    """Compute reference min-distances, optional $q^2$-error ranks, and optional multi-$Q$ table."""
    cand = list(quadratic_candidates or DEFAULT_QUADRATIC_CANDIDATES)
    rng = np.random.default_rng(seed)
    pooled = _build_pooled_reference_1d(
        rng, n_uniform, n_quadratic, n_beta, beta_a, beta_b, cand
    )
    d_pool = batch_min_rational_distances(pooled, q_max)
    q2_pool = batch_min_q_squared_errors(pooled, q_max)
    const = {k: v.value for k, v in named_constants().items()}
    rows = compare_constant_table(
        const,
        q_max,
        d_pool,
        q2_pool,
        use_fractional_part=compare_mod1,
    )
    summary: dict[str, Any] = {
        "seed": seed,
        "q_max": q_max,
        "n_uniform": n_uniform,
        "n_quadratic": n_quadratic,
        "n_beta": int(n_beta),
        "beta_a": float(beta_a),
        "beta_b": float(beta_b),
        "quadratic_candidates": cand,
        "compare_mod1": bool(compare_mod1),
        "reference_combined_n": int(pooled.size),
        "reference_summary": reference_distribution_summary(d_pool),
        "reference_q_squared_summary": reference_distribution_summary(q2_pool),
        "constants": rows,
    }
    if q_sensitivity:
        sens: dict[str, Any] = {}
        for q in sorted(set(q_sensitivity)):
            if q < 1:
                continue
            dq = batch_min_rational_distances(pooled, q)
            q2q = batch_min_q_squared_errors(pooled, q)
            sens[str(q)] = {
                "reference_summary": reference_distribution_summary(dq),
                "constants": compare_constant_table(
                    const, q, dq, q2q, use_fractional_part=compare_mod1
                ),
            }
        summary["q_sensitivity"] = sens
    return summary


def save_outputs(project_dir: Path, summary: dict) -> tuple[Path, Path, Path, Path, Path]:
    data_dir = project_dir / "output" / "data"
    fig_dir = project_dir / "output" / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / "proximity_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_path = data_dir / "proximity_constants.csv"
    rows = summary["constants"]
    if rows:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    cap = int(summary.get("histogram_uniform_cap", 8000))
    rng = np.random.default_rng(summary["seed"])
    u = uniform_unit_samples(min(summary["n_uniform"], cap), rng)
    d_u = batch_min_rational_distances(u, summary["q_max"])
    quad_cand = summary["quadratic_candidates"]
    nq = min(summary["n_quadratic"], max(1, cap // 4))
    qref = random_quadratic_mod1(quad_cand, rng, nq)
    pooled_xy = np.concatenate([u, qref])
    d_pooled = batch_min_rational_distances(pooled_xy, summary["q_max"])
    mu_pooled = batch_min_q_squared_errors(pooled_xy, summary["q_max"])

    lookup = constant_lookup()
    cm1 = bool(summary.get("compare_mod1"))
    q_cap = int(summary["q_max"])

    fig_path = fig_dir / "proximity_histogram.png"
    plt.figure(figsize=(8.2, 4.6))
    plt.hist(
        _log10_delta(d_u),
        bins=60,
        color="#2c5282",
        alpha=0.88,
        label="Uniform(0,1) subsample",
    )
    _mark_constants_delta(lookup, q_cap, compare_mod1=cm1)
    plt.xlabel(r"$\log_{10}\,\delta_Q(x)$")
    plt.ylabel("count")
    plt.title(f"Uniform reference: $\\delta_Q$ with $Q={q_cap}$ (histogram subsample)")
    _apply_figure_style()
    plt.legend(loc="upper left", fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=160)
    plt.close()

    fig_pooled = fig_dir / "proximity_histogram_pooled.png"
    plt.figure(figsize=(8.2, 4.6))
    plt.hist(
        _log10_delta(d_pooled),
        bins=60,
        color="#285e61",
        alpha=0.88,
        label="Uniform + quadratic mod 1 (subsample)",
    )
    _mark_constants_delta(lookup, q_cap, compare_mod1=cm1)
    plt.xlabel(r"$\log_{10}\,\delta_Q(x)$")
    plt.ylabel("count")
    plt.title(
        f"Pooled visualization subsample: uniform + "
        f"$\\{{\\sqrt{{k}}\\}}$ mod 1, $Q={q_cap}$"
    )
    _apply_figure_style()
    plt.legend(loc="upper left", fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(fig_pooled, dpi=160)
    plt.close()

    fig_mu = fig_dir / "proximity_histogram_mu.png"
    plt.figure(figsize=(8.2, 4.6))
    plt.hist(
        _log10_mu(mu_pooled),
        bins=60,
        color="#553c9a",
        alpha=0.88,
        label=r"$\mu_Q$ on same subsample as pooled $\delta_Q$",
    )
    _mark_constants_mu(lookup, q_cap, compare_mod1=cm1)
    plt.xlabel(r"$\log_{10}\,\mu_Q(x)$")
    plt.ylabel("count")
    plt.title(f"Weighted error $\\mu_Q$ (Lagrange scale), $Q={q_cap}$")
    _apply_figure_style()
    plt.legend(loc="upper left", fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(fig_mu, dpi=160)
    plt.close()

    return json_path, csv_path, fig_path, fig_pooled, fig_mu


def main(project_dir: Path | None = None) -> None:
    base = project_dir.resolve() if project_dir is not None else project_root
    cfg = _load_experiment_config(base)
    exp = cfg.get("experiment") or {}
    seed = int(exp.get("rng_seed", 20260322))
    q_max = int(exp.get("q_max", 120))
    n_uniform = int(exp.get("n_uniform", 4000))
    n_quadratic = int(exp.get("n_quadratic", 2000))
    n_beta = int(exp.get("n_beta", 0))
    beta_a = float(exp.get("beta_a", 0.5))
    beta_b = float(exp.get("beta_b", 0.5))
    q_cand = list(exp.get("quadratic_candidates") or DEFAULT_QUADRATIC_CANDIDATES)
    compare_mod1 = bool(exp.get("compare_mod1", False))
    q_sens = exp.get("q_sensitivity")
    q_sensitivity = [int(x) for x in q_sens] if isinstance(q_sens, list) else None
    hist_cap = int(exp.get("histogram_uniform_cap", 8000))

    logger.info(
        "Running proximity study seed=%s q_max=%s n_uniform=%s n_quadratic=%s n_beta=%s mod1=%s",
        seed,
        q_max,
        n_uniform,
        n_quadratic,
        n_beta,
        compare_mod1,
    )
    summary = run_proximity_study(
        base,
        seed,
        q_max,
        n_uniform,
        n_quadratic,
        n_beta=n_beta,
        beta_a=beta_a,
        beta_b=beta_b,
        quadratic_candidates=q_cand,
        compare_mod1=compare_mod1,
        q_sensitivity=q_sensitivity,
    )
    summary["histogram_uniform_cap"] = hist_cap
    paths = save_outputs(base, summary)
    for p in paths:
        print(str(p))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monte Carlo proximity study")
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Project root (default: directory containing scripts/)",
    )
    args = parser.parse_args()
    main(args.project_dir)
