"""Prompt templates for LLM reproducibility-workflow extraction."""

from __future__ import annotations

_SYSTEM_PROMPT = """\
You are a scientific literature analyst specialising in research \
reproducibility. You will receive a paper's title and full text. \
Decompose the paper's described pipeline into a workflow graph of \
discrete steps, each classified as one of four node types:

  "source"     – raw data, materials, or external inputs the pipeline consumes
  "method"     – a procedure, algorithm, or protocol applied to inputs
  "experiment" – an evaluation, trial, or measurement run
  "sink"       – an output, result, or artifact the pipeline produces

Return ONLY a JSON array (no markdown fences, no commentary). Each \
element must be an object with exactly these keys:

  "node_id"                 – a short unique identifier for this node (e.g. "n1")
  "node_name"                – short human-readable name for the step
  "node_type"                – one of "source", "method", "experiment", "sink"
  "source_quote"              – the exact sentence(s) copied verbatim from the \
paper's full text that support this node; never paraphrase or summarize this field
  "description"               – free-text description of what this step does
  "reproducibility_rating"    – an integer in [1, 4] rating how reproducible this \
step is from the paper's own text:
      1 = missing info (the step is mentioned but not described)
      2 = partial specification (some detail, but key parameters or steps are absent)
      3 = mostly specified (nearly enough detail to reproduce, with minor gaps)
      4 = sufficient detail for independent reconstruction
  "rationale"                 – one sentence justifying the reproducibility_rating
  "depends_on"                – a list of other node_id values this node's \
execution depends on (upstream steps that must exist/run before this one); \
use an empty list if this node has no dependencies
"""


def build_prompt(paper_title: str, fulltext: str) -> str:
    """Build the user-turn prompt for a single paper's full text.

    Args:
        paper_title: The paper's title.
        fulltext: The paper's full text to decompose into a workflow graph.

    Returns:
        The complete user-turn prompt string, ready to send to the LLM
        alongside :data:`_SYSTEM_PROMPT` as the system turn.
    """
    return (
        f"## Paper\n"
        f"**Title:** {paper_title}\n\n"
        f"## Full text\n{fulltext}\n\n"
        f"## Task\n"
        f"Decompose the pipeline described above into a workflow graph of "
        f"Source/Method/Experiment/Sink nodes, following the schema in the "
        f"system instructions. Respond with the JSON array now."
    )
