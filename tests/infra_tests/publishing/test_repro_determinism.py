#!/usr/bin/env python3
"""Reproducibility guard for the repro-bundle surface (R9).

No mocks: every assertion reads the real committed tree and exercises the real
artifact-collection code on those bytes.

R9 — every public exemplar's repro manifest must declare at least one
``output-artifact`` so ``verify`` checks a non-empty reproduced product.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_scope import public_project_names
from infrastructure.publishing.repro_bundle import _KIND_OUTPUT_ARTIFACT, collect_entries

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_every_public_exemplar_declares_output_artifact() -> None:
    """Every public exemplar declares >= 1 present, hashed output-artifact (R9).

    A bundle that "verifies nothing" must never certify as reproducible, so each
    exemplar's repro manifest must resolve to at least one real, present, hashed
    output — a non-empty reproduced product.
    """
    names = public_project_names(REPO_ROOT)
    assert names, "no public exemplars discovered"

    without_real_output: list[str] = []
    for name in names:
        entries = collect_entries(REPO_ROOT, name)
        present_outputs = [
            entry for entry in entries if entry.kind == _KIND_OUTPUT_ARTIFACT and entry.present and entry.sha256
        ]
        if not present_outputs:
            without_real_output.append(name)

    assert not without_real_output, (
        f"public exemplars whose repro manifest declares no present output-artifact: {without_real_output}"
    )
