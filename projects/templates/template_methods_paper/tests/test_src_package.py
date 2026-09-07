"""Tests for src/__init__.py — the top-level `from src import ...` re-export surface.

src/methods_dsl/AGENTS.md's re-export rule: "Re-export the public surface
from src/__init__.py so callers write `from src import compile_method`
regardless of internal layout." Every other test in this suite imports
directly from `src.methods_dsl.<module>`, so this file is the only place the
top-level re-export contract — and the exact `from src import (...)` usage
example documented in `src/AGENTS.md` — is exercised.

Regression: `export_receipt` / `EXPORT_RECEIPT_SCHEMA` were once missing from
the top-level surface while being listed in `methods_dsl.__all__` and the
`src/AGENTS.md` API table, so `from src import export_receipt` raised
ImportError. The first test below fails loudly if the surface drifts again.
"""

from __future__ import annotations

import src
from src.methods_dsl import __all__ as methods_dsl_all


def test_src_all_reexports_every_methods_dsl_public_symbol():
    missing = set(methods_dsl_all) - set(src.__all__)
    assert not missing, f"src/__init__.py is missing re-exports for: {sorted(missing)}"


def test_documented_usage_example_from_src_agents_md():
    from src import (
        all_example_methods,
        compile_method,
        export_receipt,
        EXPORT_RECEIPT_SCHEMA,
        run_all_gates,
    )

    method = all_example_methods()[0]
    gates = run_all_gates(method)
    assert all(g.passed for g in gates)
    plan = compile_method(method)
    assert plan.plan_hash
    receipt = export_receipt(plan)
    assert receipt["schema"] == EXPORT_RECEIPT_SCHEMA


def test_export_receipt_end_to_end_from_top_level_package():
    from src import all_example_methods, compile_method, export_receipt

    plan = compile_method(all_example_methods()[0])
    receipt = export_receipt(plan)
    assert receipt["schema"] == "template-methods-paper-export-receipt-v1"
    assert receipt["plan_hash"] == plan.plan_hash
