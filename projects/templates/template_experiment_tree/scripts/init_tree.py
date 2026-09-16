#!/usr/bin/env python3
"""Initialize the canonical experiment tree store with a seeded root record.

Thin orchestrator: all logic lives in ``src/template_experiment_tree``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from template_experiment_tree import (  # noqa: E402
    ExperimentTree,
    NodeStatus,
    default_store_path,
    save_tree,
)


def build_seed_tree() -> ExperimentTree:
    """Deterministic seed tree: one baseline with two planned children."""
    tree = ExperimentTree()
    tree.add_node(
        node_id="E001",
        title="Baseline: gradient step size sweep",
        run_command="python scripts/run_baseline.py --steps 5",
        round_number=1,
        notes=("Root of the experiment tree; all children refine the baseline.",),
    )
    tree.add_node(
        node_id="E002",
        title="Child: halve the step size",
        run_command="python scripts/run_baseline.py --steps 5 --scale 0.5",
        parent_id="E001",
        round_number=1,
    )
    tree.add_node(
        node_id="E003",
        title="Frozen preregistration: momentum follow-up",
        run_command="python scripts/run_baseline.py --steps 10 --scale 0.5 --momentum 0.9",
        parent_id="E001",
        status=NodeStatus.FROZEN,
        round_number=2,
    )
    return tree


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing store.")
    args = parser.parse_args(argv)

    store = default_store_path(PROJECT_ROOT)
    if store.exists() and not args.force:
        print(f"tree store already exists: {store} (pass --force to overwrite)")
        return 1
    tree = build_seed_tree()
    save_tree(tree, store)
    print(f"wrote {store} with {len(tree.nodes())} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
