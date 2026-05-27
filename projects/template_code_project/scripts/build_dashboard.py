#!/usr/bin/env python3
"""CLI for the code-project interactive dashboard builder.

Dashboard payload and rendering behavior lives in ``src/dashboard.py``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parent.parent):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

import numpy as np  # noqa: E402

from src.dashboard import (  # noqa: E402
    CFG_DEFAULT,
    DATA_DIR,
    OUTPUT,
    REP_DIR,
    WEB_DIR,
    _build_dashboard,
    _compute_payload,
    _load_yaml_defaults,
    _to_dashboard_invariant,
    _to_diagonal_A,
)
from src.experiment_config import ExperimentConfig  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    cfg = _load_yaml_defaults(CFG_DEFAULT)
    a_diag = np.diag(cfg.A_array()).tolist()
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--step-sizes", type=float, nargs="+", default=list(cfg.step_sizes))
    p.add_argument("--A", type=float, nargs="+", default=[float(v) for v in a_diag])
    p.add_argument("--b", type=float, nargs="+", default=list(cfg.quadratic_b))
    p.add_argument("--x0", type=float, nargs="+", default=[cfg.initial_point])
    p.add_argument("--tol", type=float, default=float(cfg.tolerance))
    p.add_argument("--max-iter", type=int, default=int(cfg.max_iterations))
    p.add_argument("--alpha-sweep-min", type=float, default=0.005)
    p.add_argument("--alpha-sweep-max", type=float, default=1.95)
    p.add_argument("--alpha-sweep-num", type=int, default=40)
    p.add_argument("--landscape-x-min", type=float, default=-3.0)
    p.add_argument("--landscape-x-max", type=float, default=5.0)
    p.add_argument("--landscape-num", type=int, default=200)
    p.add_argument("--html-out", type=Path, default=WEB_DIR / "dashboard.html")
    p.add_argument("--json-out", type=Path, default=DATA_DIR / "dashboard_payload.json")
    p.add_argument("--invariants-out", type=Path, default=REP_DIR / "dashboard_invariants.txt")
    p.add_argument("--summary-out", type=Path, default=REP_DIR / "dashboard_summary.txt")
    args = p.parse_args(argv)
    if not args.step_sizes:
        p.error("--step-sizes must list at least one positive α")
    if any(a <= 0 for a in args.step_sizes):
        p.error("every --step-sizes value must be > 0")
    if len(args.A) != len(args.b):
        p.error(f"--A length ({len(args.A)}) must equal --b length ({len(args.b)})")
    if len(args.x0) != len(args.b):
        p.error(f"--x0 length ({len(args.x0)}) must equal --b length ({len(args.b)})")
    if args.alpha_sweep_max <= args.alpha_sweep_min:
        p.error("--alpha-sweep-max must be > --alpha-sweep-min")
    if args.alpha_sweep_num < 2:
        p.error("--alpha-sweep-num must be ≥ 2")
    return args


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    payload = _compute_payload(args)
    d = _build_dashboard(args, payload)
    out = d.write(
        html_path=args.html_out,
        json_path=args.json_out,
        invariants_path=args.invariants_out,
        txt_path=args.summary_out,
    )
    for k in ("html", "json", "invariants", "summary"):
        if k in out:
            print(out[k])

    failed = [i for i in d.evaluate_invariants() if not i["passed"]]
    if failed:
        names = ", ".join(i["name"] for i in failed)
        print(f"FAILED INVARIANTS: {names}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "CFG_DEFAULT",
    "DATA_DIR",
    "OUTPUT",
    "REP_DIR",
    "WEB_DIR",
    "_build_dashboard",
    "_compute_payload",
    "_load_yaml_defaults",
    "_parse_args",
    "_to_dashboard_invariant",
    "_to_diagonal_A",
    "ExperimentConfig",
    "main",
]


if __name__ == "__main__":
    main()
