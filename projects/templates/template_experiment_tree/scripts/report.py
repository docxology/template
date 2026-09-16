#!/usr/bin/env python3
"""Render the living-record markdown report plus the tree-state figure.

Thin orchestrator: report text comes from ``src`` render functions; the
figure is a deterministic matplotlib projection of node counts per round.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib  # noqa: E402

matplotlib.use("Agg")

from template_experiment_tree import load_tree, render_markdown, summarize  # noqa: E402
from template_experiment_tree.store import default_store_path  # noqa: E402
from template_experiment_tree.tree import NodeStatus  # noqa: E402


def write_figure(tree, out_path: Path) -> None:
    """Deterministic stacked bars of node statuses per round."""
    import matplotlib.pyplot as plt

    rounds = sorted({node.round_number for node in tree.nodes()})
    statuses = (NodeStatus.ANSWERED, NodeStatus.FROZEN, NodeStatus.PROVISIONAL)
    counts = {
        status.value: [len([n for n in tree.nodes() if n.round_number == r and n.status is status]) for r in rounds]
        for status in statuses
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    bottom = [0] * len(rounds)
    for status in statuses:
        values = counts[status.value]
        ax.bar([str(r) for r in rounds], values, bottom=bottom, label=status.value)
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.set_xlabel("Round")
    ax.set_ylabel("Experiments")
    ax.set_title("Experiment tree state per round")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=None)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args(argv)

    store = Path(args.store) if args.store else default_store_path(PROJECT_ROOT)
    out_dir = Path(args.out_dir) if args.out_dir else PROJECT_ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    tree = load_tree(store)
    (out_dir / "experiment_record.md").write_text(render_markdown(tree), encoding="utf-8")
    write_figure(tree, out_dir / "tree_state.png")
    summary = summarize(tree)
    print(f"wrote {out_dir / 'experiment_record.md'} and tree_state.png")
    print(f"answered={summary['answered']} frozen={summary['frozen']} provisional={summary['provisional']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
