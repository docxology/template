"""Prompt templates for LLM hypothesis assessment."""

from __future__ import annotations

import knowledge_graph.hypothesis as _hypothesis_module
from literature.models import Paper

_SYSTEM_PROMPT = """\
You are a scientific literature analyst specialising in scientific literature \
and evidence synthesis. You will receive a paper's title and \
abstract, together with a list of research hypotheses. For each \
hypothesis, assess whether the paper provides evidence that supports, \
contradicts, or is neutral toward the hypothesis, or whether the paper \
is irrelevant to it.

Return ONLY a JSON array (no markdown fences, no commentary). Each \
element must be an object with exactly these keys:

  "hypothesis_id"  – the ID string provided
  "direction"      – one of "supports", "contradicts", "neutral", "irrelevant"
  "confidence"     – a float in [0.0, 1.0] reflecting how strong the evidence is
  "reasoning"      – one sentence justifying the assessment
"""


def build_prompt(paper: Paper, hypotheses: list[dict[str, str]]) -> str:
    """Build the user-turn prompt for a single paper."""
    hyp_block = "\n".join(f"  - {h['id']}: {h['name']} — {h['description']}" for h in hypotheses)
    return (
        f"## Paper\n"
        f"**Title:** {paper.title}\n"
        f"**Abstract:** {paper.abstract}\n\n"
        f"## Hypotheses to assess\n{hyp_block}\n\n"
        f"Respond with the JSON array now."
    )


def hypothesis_dicts() -> list[dict[str, str]]:
    """Convert configured hypotheses to prompt dicts."""
    return [
        {"id": h.hypothesis_id, "name": h.name, "description": h.description} for h in _hypothesis_module.HYPOTHESES
    ]
