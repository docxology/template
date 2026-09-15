#!/usr/bin/env python3
"""Record an answer for a tree node, freezing the result into the record.

Thin orchestrator over ``ExperimentTree.record_answer``. Refuses to answer
frozen nodes (preregistration invariant) — that refusal is the point.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from template_experiment_tree import load_tree, save_tree  # noqa: E402
from template_experiment_tree.store import default_store_path  # noqa: E402
from template_experiment_tree.tree import ExperimentTreeError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("node_id")
    parser.add_argument("answer")
    parser.add_argument("outcome", choices=("win", "loss", "dead_end"))
    parser.add_argument("--store", default=None, help="Override the tree store path.")
    args = parser.parse_args(argv)

    store = Path(args.store) if args.store else default_store_path(PROJECT_ROOT)
    tree = load_tree(store)
    try:
        node = tree.record_answer(args.node_id, args.answer, args.outcome)
    except ExperimentTreeError as exc:
        print(f"REFUSED: {exc}")
        return 1
    save_tree(tree, store)
    print(f"recorded {node.node_id} -> {node.outcome}: {node.answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
