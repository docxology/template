"""LLM synthesis over enriched literature results.

Two layers:

* Pure prompt construction (``build_paper_block``, ``build_corpus_block``).
  No LLM dependency; testable with `assert == ...`.
* :func:`synthesise_per_paper` and :func:`synthesise_corpus`, which take a
  *callable* ``llm`` of shape ``(prompt: str) -> str`` and return
  :class:`SynthesisResult` records. The callable is intentionally
  duck-typed so tests can pass a deterministic local function and runtime
  callers can pass an :class:`infrastructure.llm.LLMClient` wrapped in a
  small adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from infrastructure.search.literature import Paper

PROMPT_PER_PAPER = """\
You are a careful research analyst. Read the paper below and write a
structured note in this exact form:

CONTRIBUTION: <one sentence — what does the paper claim is new?>
METHOD: <2-3 bullets — the approach in plain language>
EVIDENCE: <2-3 bullets — what experiments / proofs support the claim?>
LIMITATION: <one bullet — the most important caveat>
TAGS: <3-7 lowercase tags>

Cite the paper as [{citation_key}] in any in-line reference.

PAPER
{paper_block}
"""

PROMPT_CORPUS = """\
You are a literature synthesiser. The corpus below contains {n} papers
indexed by citation key. Your task is to:

1. Group the papers into 3-7 thematic clusters. Name each cluster.
2. Within each cluster, summarise the dominant approach in 2-4 sentences.
3. Identify methodological agreements (≥2 papers) and disagreements.
4. List 3 open questions that no paper in the corpus answers cleanly.

Cite every claim using square-bracket citation keys, e.g. [some2024key].
Do NOT introduce papers outside the corpus.

CORPUS
{joined_blocks}
"""


@dataclass
class SynthesisResult:
    """Outcome of an LLM synthesis call.

    Attributes:
        kind: ``"per_paper"`` or ``"corpus"``.
        prompt: The prompt sent to the LLM (kept for reproducibility).
        text: The LLM's response.
        paper_id: Populated for per-paper synthesis only.
    """

    kind: str
    prompt: str
    text: str
    paper_id: str | None = None


def build_paper_block(paper: Paper, citation_key: str, *, max_fulltext: int = 4000) -> str:
    """Render *paper* as a markdown block for prompt inclusion."""
    authors = ", ".join(paper.authors) if paper.authors else "(unknown authors)"
    locator = paper.doi or paper.url or "(no DOI/URL)"
    abstract = paper.abstract or "(no abstract available)"
    block = (
        f"### {citation_key} — {paper.title} ({paper.year or 'n.d.'})\n"
        f"**Authors:** {authors}\n"
        f"**DOI / URL:** {locator}\n"
        f"**Abstract:** {abstract}\n"
    )
    if paper.fulltext:
        truncated = paper.fulltext[:max_fulltext]
        suffix = "" if len(paper.fulltext) <= max_fulltext else "…"
        block += f"\n**Excerpt (truncated):**\n{truncated}{suffix}\n"
    return block


def build_corpus_block(
    papers: Iterable[Paper],
    citation_keys: dict[str, str],
    *,
    max_fulltext_per_paper: int = 1500,
) -> str:
    """Render *papers* as a single, citation-keyed corpus block.

    *citation_keys* is a mapping ``paper.id -> citation_key`` so the
    rendered text references each paper by its eventual BibTeX key.
    """
    blocks: list[str] = []
    for paper in papers:
        key = citation_keys.get(paper.id, paper.id)
        blocks.append(build_paper_block(paper, key, max_fulltext=max_fulltext_per_paper))
    return "\n\n".join(blocks)


def synthesise_per_paper(
    paper: Paper,
    citation_key: str,
    *,
    llm: Callable[[str], str],
    prompt_template: str = PROMPT_PER_PAPER,
) -> SynthesisResult:
    """Run per-paper synthesis using *llm*.

    *llm* must be a callable accepting a prompt string and returning the
    model's response. This keeps the function trivially testable.
    """
    block = build_paper_block(paper, citation_key)
    prompt = prompt_template.format(citation_key=citation_key, paper_block=block)
    text = llm(prompt)
    return SynthesisResult(kind="per_paper", prompt=prompt, text=text, paper_id=paper.id)


def synthesise_corpus(
    papers: Iterable[Paper],
    citation_keys: dict[str, str],
    *,
    llm: Callable[[str], str],
    prompt_template: str = PROMPT_CORPUS,
) -> SynthesisResult:
    """Run cross-corpus synthesis using *llm*."""
    paper_list = list(papers)
    block = build_corpus_block(paper_list, citation_keys)
    prompt = prompt_template.format(n=len(paper_list), joined_blocks=block)
    text = llm(prompt)
    return SynthesisResult(kind="corpus", prompt=prompt, text=text, paper_id=None)
