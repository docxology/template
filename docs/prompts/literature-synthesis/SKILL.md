---
name: template-literature-synthesis
description: |
  LLM prompt blocks for per-paper and corpus literature synthesis after a search pipeline.
  USE WHEN synthesizing arXiv/Crossref results, writing per-paper notes, thematic clusters,
  gap analysis from a literature corpus, or wiring template_search_project synthesis — even
  without naming infrastructure.llm templates.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: redacted
  task_type: open-ended
  modes:
    - per-paper
    - corpus
    - gap-analysis
  related_skills:
    - template-deep-research
    - template-academic-paper
---

# Literature synthesis

Prompt blocks for `infrastructure.llm` or project `synthesis.py` after literature search.

## Natural invoke

- "Synthesize these 12 papers into thematic clusters with citation keys"
- "Per-paper structured notes: contribution, method, evidence, limitation"
- "Gap analysis: what experiments would close open questions?"

## Inputs to confirm

- **Corpus** — list of papers (title, authors, year, abstract, optional fulltext).
- **Goal paragraph** — for gap-analysis variant only.

## Paper block format

Each paper renders as:

```text
### {citation_key} — {title} ({year})
**Authors:** {authors}
**DOI / URL:** {doi or url}
**Abstract:** {abstract}
```

## Workflows

### Per-paper analysis

Structured note: CONTRIBUTION (one sentence), METHOD (2–3 bullets), EVIDENCE (2–3 bullets), LIMITATION (one bullet), TAGS (3–7 lowercase). Cite as `[{citation_key}]`.

### Cross-paper synthesis

Group into 3–7 thematic clusters; summarise dominant approach; agreements/disagreements; 3 open questions. Cite only corpus keys in square brackets.

### Gap analysis

Given GOAL + corpus: per paper COVERS/LACKS sub-claims; propose 3 follow-up experiments. Cite by key.

## Style

- Bracket-key citations only — not bare titles.
- Bound input: truncate fulltext; `temperature=0.0`, `seed=42` for replay.
- Optional second pass: `infrastructure.llm.validation.validate_complete`.

## Verification

- Outputs under `output/llm/` or project convention; keys match `references.bib`.
- See [`projects/templates/template_search_project/`](../../../projects/templates/template_search_project/) for wired implementation.

## When NOT to use

- **Running literature search backends** → `infrastructure/search/` and project search scripts
- **New manuscript from scratch** → [manuscript-creation](../manuscript-creation/SKILL.md)

## References

Full prompt text and programmatic example: [references/prompt-blocks.md](references/prompt-blocks.md)
