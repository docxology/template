# Literature synthesis — prompt blocks

## Per-paper

```text
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
```

## Cross-paper synthesis

```text
You are a literature synthesiser. The corpus below contains {n} papers
indexed by citation key. Your task is to:

1. Group the papers into 3-7 thematic clusters. Name each cluster.
2. Within each cluster, summarise the dominant approach in 2-4 sentences.
3. Identify methodological agreements (≥2 papers) and disagreements.
4. List 3 open questions that no paper in the corpus answers cleanly.

Cite every claim using square-bracket citation keys, e.g.
[{example_key1}, {example_key2}]. Do NOT introduce papers outside the
corpus.

CORPUS
{joined_paper_blocks}
```

## Gap analysis

```text
The following research goal is given:

GOAL
{goal_paragraph}

The corpus below contains the {n} papers most closely related to this
goal. For each paper, decide:

- COVERS: which sub-claims of the goal does it address?
- LACKS: which sub-claims does it leave open?

Then propose 3 specific follow-up experiments that would close the
largest remaining gaps. Cite supporting / non-supporting papers by key.

CORPUS
{joined_paper_blocks}
```

## Programmatic sketch

```python
from infrastructure.llm import LLMClient, OllamaClientConfig

llm = LLMClient(OllamaClientConfig(default_model="gemma3:4b", seed=42, temperature=0.0))
# Format paper_block, call llm.query(PROMPT.format(...))
```
