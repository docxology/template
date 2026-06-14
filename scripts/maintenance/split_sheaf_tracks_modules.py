#!/usr/bin/env python3
"""One-shot splitter for roadmap_tracks.sheaf_tracks (thermo-nuclear remediation)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "projects/templates/template_active_inference/src/roadmap_tracks"
SOURCE = ROOT / "sheaf_tracks.py"


def _lines() -> list[str]:
    return SOURCE.read_text(encoding="utf-8").splitlines(keepends=True)


def _slice(start: int, end: int) -> str:
    return "".join(_lines()[start - 1 : end])


def _write(name: str, header: str, body: str) -> None:
    path = ROOT / name
    path.write_text(header + body, encoding="utf-8")
    line_count = path.read_text(encoding="utf-8").count("\n")
    print(f"wrote {path.name}: {line_count} lines")


def main() -> None:
    _write(
        "sheaf_tracks_registry.py",
        '''"""Canonical sheaf-track registry constants."""

from __future__ import annotations

import re

''',
        _slice(24, 147),
    )

    _write(
        "sheaf_tracks_io.py",
        '''"""Shared I/O and manuscript registry loaders for sheaf-track builders."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

''',
        _slice(150, 318),
    )

    _write(
        "sheaf_tracks_context.py",
        '''"""Provenance context for canonical sheaf-track artifact builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roadmap_tracks.sheaf_tracks_io import _config_digest, _deterministic_seed, _source_commit

''',
        _slice(321, 338),
    )

    _write(
        "sheaf_tracks_helpers.py",
        '''"""Shared helpers for sheaf-track artifact builders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext, _provenance_context
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _claim_ids_by_path,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, LEGACY_ARTIFACTS

''',
        _slice(341, 470),
    )

    _write(
        "sheaf_tracks_builders_provenance.py",
        '''"""Provenance and replay-matrix builders for canonical sheaf tracks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext
from roadmap_tracks.sheaf_tracks_helpers import _canonical_artifact_rows
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _load_json,
    _provenance_context,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_SCHEMA

''',
        _slice(472, 670),
    )

    _write(
        "sheaf_tracks_builders_toy.py",
        '''"""Toy sweep builders promoted into canonical sheaf tracks."""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_helpers import _entropy
from roadmap_tracks.sheaf_tracks_io import _load_json
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_SCHEMA

''',
        _slice(673, 810),
    )

    _write(
        "sheaf_tracks_builders_formal.py",
        '''"""Formal interop and adversarial builders for canonical sheaf tracks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_io import _load_json, _load_yaml
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_SCHEMA

''',
        _slice(812, 1090),
    )

    _write(
        "sheaf_tracks_builders_release.py",
        '''"""Release-bundle and evidence-field builders for canonical sheaf tracks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _claim_ids_by_path,
    _claim_ids_by_track,
    _claim_records,
    _load_json,
    _load_structured,
    _load_yaml,
    _registry_tracks,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_SCHEMA

''',
        _slice(1101, 1272),
    )

    _write(
        "sheaf_tracks_builders_graph.py",
        '''"""Graph, contract, and dependency builders for canonical sheaf tracks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext
from roadmap_tracks.sheaf_tracks_helpers import _copied_parity
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _bound_tracks,
    _bridge_reference_section_status,
    _claim_ids_by_path,
    _claim_ids_by_track,
    _claim_records,
    _load_json,
    _load_yaml,
    _manifest_sections,
    _pipeline_tracks,
    _registry_tracks,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import (
    CANONICAL_ARTIFACTS,
    CANONICAL_SCHEMA,
    CANONICAL_TRACKS,
    DEPENDENCY_SCHEMA,
    OPTIONAL_CLAIM_EXEMPT_TRACKS,
    PIPELINE_TRACK_SHEAF_ALIASES,
    REQUIRED_EDGE_TYPES,
)

''',
        _slice(1273, 1743),
    )

    _write(
        "sheaf_tracks_restrictions.py",
        '''"""Canonical restriction snapshot for semantic gluing gates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_io import (
    _bound_tracks,
    _bridge_reference_section_status,
    _claim_ids_by_path,
    _load_json,
    _registry_tracks,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_TRACKS, VERSIONED_TRACK_RE

''',
        _slice(1745, 1946),
    )

    _write(
        "sheaf_tracks_write.py",
        '''"""Deterministic multi-phase writer for canonical sheaf-track artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from roadmap_tracks.sheaf_tracks_builders_formal import (
    build_adversarial_audit,
    build_blocked_scope_manifest,
    build_counterexample_matrix,
    build_model_checking_witnesses,
)
from roadmap_tracks.sheaf_tracks_builders_graph import (
    build_artifact_contract_index,
    build_track_improvement_scope,
    build_track_lane_matrix,
    build_validation_dependency_graph,
)
from roadmap_tracks.sheaf_tracks_builders_provenance import build_artifact_provenance, build_replay_matrix
from roadmap_tracks.sheaf_tracks_builders_release import (
    build_evidence_field_index,
    build_release_bundle_manifest,
    build_theorem_traceability_matrix,
)
from roadmap_tracks.sheaf_tracks_builders_toy import build_sensitivity_sweep, build_uncertainty_summary
from roadmap_tracks.sheaf_tracks_context import (
    _ACTIVE_PROVENANCE_CONTEXT,
    _ProvenanceContext,
)
from roadmap_tracks.sheaf_tracks_helpers import _refresh_hydrated_manuscript, _remove_legacy_artifacts
from roadmap_tracks.sheaf_tracks_io import _config_digest, _deterministic_seed, _source_commit, _write_json
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS

''',
        _slice(1949, 2201),
    )

    facade = '''"""Canonical deterministic sheaf-track artifacts (public facade).

Track ids and artifact paths stay canonical so the manuscript cannot accumulate
parallel ``*_vN`` proof surfaces for the same concept. Implementation lives in
focused sibling modules; this module re-exports the stable public surface.
"""

from __future__ import annotations

from pathlib import Path

from roadmap_tracks.sheaf_tracks_builders_formal import (
    build_adversarial_audit,
    build_blocked_scope_manifest,
    build_counterexample_matrix,
    build_interop_roundtrip_report,
    build_model_checking_witnesses,
)
from roadmap_tracks.sheaf_tracks_builders_graph import (
    _pipeline_sheaf_tracks,
    build_artifact_contract_index,
    build_track_improvement_scope,
    build_track_lane_matrix,
    build_validation_dependency_graph,
)
from roadmap_tracks.sheaf_tracks_builders_provenance import build_artifact_provenance, build_replay_matrix
from roadmap_tracks.sheaf_tracks_builders_release import (
    build_evidence_field_index,
    build_release_bundle_manifest,
    build_theorem_traceability_matrix,
)
from roadmap_tracks.sheaf_tracks_builders_toy import build_sensitivity_sweep, build_uncertainty_summary
from roadmap_tracks.sheaf_tracks_context import (
    _ACTIVE_PROVENANCE_CONTEXT,
    _ProvenanceContext,
    _provenance_context,
)
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _bound_tracks,
    _claim_ids_by_path,
    _claim_ids_by_track,
    _config_digest,
    _deterministic_seed,
    _load_json,
    _load_structured,
    _load_yaml,
    _pipeline_tracks,
    _registry_tracks,
    _sha256,
    _source_commit,
)
from roadmap_tracks.sheaf_tracks_registry import (
    CANONICAL_ARTIFACTS,
    CANONICAL_SCHEMA,
    CANONICAL_TRACKS,
    DEPENDENCY_SCHEMA,
    LEGACY_ARTIFACTS,
    OPTIONAL_CLAIM_EXEMPT_TRACKS,
    PIPELINE_TRACK_SHEAF_ALIASES,
    REQUIRED_EDGE_TYPES,
    SEMANTIC_SCHEMA,
    SHEAF_TRACK_PRODUCER,
    VERSIONED_TRACK_RE,
)
from roadmap_tracks.sheaf_tracks_restrictions import _canonical_restrictions
from roadmap_tracks.sheaf_tracks_write import write_sheaf_track_artifacts

__all__ = [
    "CANONICAL_ARTIFACTS",
    "CANONICAL_SCHEMA",
    "CANONICAL_TRACKS",
    "DEPENDENCY_SCHEMA",
    "LEGACY_ARTIFACTS",
    "OPTIONAL_CLAIM_EXEMPT_TRACKS",
    "PIPELINE_TRACK_SHEAF_ALIASES",
    "REQUIRED_EDGE_TYPES",
    "SEMANTIC_SCHEMA",
    "SHEAF_TRACK_PRODUCER",
    "VERSIONED_TRACK_RE",
    "_ACTIVE_PROVENANCE_CONTEXT",
    "_ProvenanceContext",
    "_analysis_scripts",
    "_artifact_maps",
    "_bound_tracks",
    "_canonical_restrictions",
    "_claim_ids_by_path",
    "_claim_ids_by_track",
    "_config_digest",
    "_deterministic_seed",
    "_load_json",
    "_load_structured",
    "_load_yaml",
    "_pipeline_sheaf_tracks",
    "_pipeline_tracks",
    "_provenance_context",
    "_registry_tracks",
    "_sha256",
    "_source_commit",
    "build_adversarial_audit",
    "build_artifact_contract_index",
    "build_artifact_provenance",
    "build_blocked_scope_manifest",
    "build_counterexample_matrix",
    "build_evidence_field_index",
    "build_interop_roundtrip_report",
    "build_model_checking_witnesses",
    "build_release_bundle_manifest",
    "build_replay_matrix",
    "build_sensitivity_sweep",
    "build_theorem_traceability_matrix",
    "build_track_improvement_scope",
    "build_track_lane_matrix",
    "build_uncertainty_summary",
    "build_validation_dependency_graph",
    "validate_sheaf_track_artifacts",
    "validate_sheaf_track_source_contract",
    "write_sheaf_track_artifacts",
]

from .sheaf_track_validation import validate_sheaf_track_artifacts, validate_sheaf_track_source_contract  # noqa: E402,F401
'''
    SOURCE.write_text(facade, encoding="utf-8")
    print(f"wrote sheaf_tracks.py facade: {facade.count(chr(10))} lines")


if __name__ == "__main__":
    main()
