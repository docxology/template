#!/usr/bin/env python3
"""Split manuscript.sheaf.semantic into focused modules."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "projects/templates/template_active_inference/src/manuscript/sheaf"
SOURCE = ROOT / "semantic.py"


def _lines() -> list[str]:
    return SOURCE.read_text(encoding="utf-8").splitlines(keepends=True)


def _slice(start: int, end: int) -> str:
    return "".join(_lines()[start - 1 : end])


def main() -> None:
    (ROOT / "semantic_maps.py").write_text(
        '''"""Artifact producer/consumer/gate maps for semantic gluing."""

from __future__ import annotations

'''
        + _slice(22, 287),
        encoding="utf-8",
    )

    (ROOT / "semantic_restrictions.py").write_text(
        '''"""Low-level restriction helpers for semantic gluing certificates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gnn.parser import parse_gnn_file
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    BERNOULLI_SYMBOL_MAP,
    SI_EXPECTED_TERMS,
    SI_SYMBOL_MAP,
    load_section_ontology,
)

'''
        + _slice(290, 540),
        encoding="utf-8",
    )

    (ROOT / "semantic_core.py").write_text(
        '''"""Core semantic gluing builders, validators, and issue aggregation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from gnn.parser import parse_gnn_file
from manuscript.variables import generate_variables
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    BERNOULLI_SYMBOL_MAP,
    SI_EXPECTED_TERMS,
    SI_SYMBOL_MAP,
    validate_all_gnn_ontology,
)

from manuscript.sheaf.coverage import gray_cell_count, load_sheaf_coverage_context
from manuscript.sheaf.semantic_maps import (
    ARTIFACT_CONSUMERS,
    ARTIFACT_GATES,
    ARTIFACT_PRODUCERS,
    SEMANTIC_SCHEMA,
)
from manuscript.sheaf.semantic_restrictions import (
    _animation_frame_count,
    _expected_symbol_gaps,
    _gnn_symbols,
    _graph_world_restrictions,
    _lean_status,
    _load_json,
    _policy_comparison_restrictions,
    _policy_posterior_restrictions,
    _proof_obligation_rows,
    _pymdp_hash_restrictions,
    _rel,
    _restriction_class,
    _restriction_lane,
    _restriction_lane_assignments,
    _restriction_lane_summaries,
    _restriction_value_ok,
    _runtime_diagnostics_restrictions,
    _section_ontology_symbols,
)

'''
        + _slice(542, 1230),
        encoding="utf-8",
    )

    SOURCE.write_text(
        '''"""Semantic gluing certificate for the multi-track manuscript sheaf."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf.semantic_core import (
    build_evidence_crosswalk,
    build_semantic_gluing_certificate,
    build_validation_dependency_graph,
    semantic_gluing_issues,
    validate_configured_artifact_producers,
    validate_semantic_gluing,
    write_semantic_gluing_certificate,
    write_semantic_gluing_outputs,
)
from manuscript.sheaf.semantic_maps import (
    ARTIFACT_CONSUMERS,
    ARTIFACT_GATES,
    ARTIFACT_PRODUCERS,
    SEMANTIC_RESTRICTION_LANES,
    SEMANTIC_SCHEMA,
)

__all__ = [
    "ARTIFACT_CONSUMERS",
    "ARTIFACT_GATES",
    "ARTIFACT_PRODUCERS",
    "SEMANTIC_RESTRICTION_LANES",
    "SEMANTIC_SCHEMA",
    "build_evidence_crosswalk",
    "build_semantic_gluing_certificate",
    "build_validation_dependency_graph",
    "semantic_gluing_issues",
    "validate_configured_artifact_producers",
    "validate_semantic_gluing",
    "write_semantic_gluing_certificate",
    "write_semantic_gluing_outputs",
]
''',
        encoding="utf-8",
    )

    for name in ("semantic_maps.py", "semantic_restrictions.py", "semantic_core.py", "semantic.py"):
        path = ROOT / name
        print(f"{name}: {path.read_text(encoding='utf-8').count(chr(10))} lines")


if __name__ == "__main__":
    main()
