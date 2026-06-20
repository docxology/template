"""Live integration test for the Hermes proposer.

Opt-in only: requires a running Ollama daemon with the Hermes model pulled
(``ollama pull hermes3``). Excluded from the default deterministic suite and
the coverage gate. No mocks — it exercises the real model round-trip.
"""

from __future__ import annotations

import json
import os
import urllib.request

import pytest

from src.state import Champion, SharedState


def _ollama_model_available(model: str = "hermes3") -> bool:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        # nosec B310 - host is an operator-configured env var (default localhost), not user input
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=1.0) as response:  # nosec B310
            payload = json.load(response)
    except Exception:
        return False
    model_names = {entry.get("name", "") for entry in payload.get("models", ())}
    return any(name == model or name.startswith(f"{model}:") for name in model_names)


@pytest.mark.requires_ollama
def test_hermes_proposes_in_scope_axis() -> None:
    # Opt-in live path: skip cleanly unless the infrastructure LLM bridge is
    # importable (it is not when the per-project gate runs under the project's
    # own rootdir without the repo root on the path) and Ollama is reachable.
    pytest.importorskip("infrastructure.llm.core.config")
    if not _ollama_model_available():
        pytest.skip("Ollama hermes3 model not available; run `ollama pull hermes3` for this opt-in test")
    from hermes_proposer import HermesProposer

    state = SharedState(champion=Champion(params=(1.5, 1.5, 1.5, 1.5), metric=-9.0, experiment_index=-1))
    proposer = HermesProposer()
    proposal = proposer.propose(state, axes=[0, 1, 2, 3], proposer_id="hermes0")
    assert proposal.axis in (0, 1, 2, 3)
    assert isinstance(proposal.step, float)
    assert proposal.proposer == "hermes0"
