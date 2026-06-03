"""Live integration test for the Hermes proposer.

Opt-in only: requires a running Ollama daemon with the Hermes model pulled
(``ollama pull hermes3``). Excluded from the default deterministic suite and
the coverage gate. No mocks — it exercises the real model round-trip.
"""

from __future__ import annotations

import os
import urllib.request

import pytest

from src.agents import HermesProposer
from src.state import Champion, SharedState


def _ollama_reachable() -> bool:
    """Return True when an Ollama daemon answers on the configured host."""
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        # nosec B310 - host is an operator-configured env var (default localhost), not user input
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=1.0):  # nosec B310
            return True
    except Exception:
        return False


@pytest.mark.requires_ollama
def test_hermes_proposes_in_scope_axis() -> None:
    # Opt-in live path: skip cleanly unless the infrastructure LLM bridge is
    # importable (it is not when the per-project gate runs under the project's
    # own rootdir without the repo root on the path) and Ollama is reachable.
    pytest.importorskip("infrastructure.llm.core.config")
    if not _ollama_reachable():
        pytest.skip("Ollama daemon not reachable; opt-in live test")
    state = SharedState(champion=Champion(params=(1.5, 1.5, 1.5, 1.5), metric=-9.0, experiment_index=-1))
    proposer = HermesProposer()
    proposal = proposer.propose(state, axes=[0, 1, 2, 3], proposer_id="hermes0")
    assert proposal.axis in (0, 1, 2, 3)
    assert isinstance(proposal.step, float)
    assert proposal.proposer == "hermes0"
