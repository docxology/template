---
name: template-deep-research
description: |
  Template-native research intake, literature search, source verification, synthesis,
  fact-checking, and systematic-review planning. USE WHEN the user asks to research a
  topic, build a literature corpus, fact-check claims, prepare a PRISMA-style review,
  or clarify a research question before manuscript work.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: raw
  task_type: open-ended
  modes:
    - full
    - quick
    - lit-review
    - fact-check
    - guided
    - systematic-review
  related_skills:
    - template-literature-synthesis
    - template-academic-paper
    - template-academic-pipeline
---

# Deep research

Template-native research workflow. This skill routes to existing repository
systems instead of running an autonomous external agent suite.

## Natural invoke

- "Research this topic and build the source corpus"
- "Do a literature review with citation keys"
- "Fact-check these manuscript claims"
- "Guide me from vague research interest to answerable question"
- "Plan a systematic review with inclusion and exclusion criteria"

## Inputs to confirm

- **Research goal** - question, audience, and expected deliverable.
- **Mode** - full, quick, lit-review, fact-check, guided, or systematic-review.
- **Corpus source** - arXiv, Crossref, local JSON corpus, provided papers, or project artifacts.
- **Project target** - if results feed a manuscript, use `docs/_generated/active_projects.md`.

## Workflow

1. **Question framing** - turn vague topics into scoped research questions, explicit in/out boundaries, and search terms. Guided mode asks before converging.
2. **Source discovery** - use `infrastructure.search.literature` and project-local corpora; record query, backend, date, DOI/arXiv IDs, and failures.
3. **Source verification** - check DOI/arXiv metadata, citation keys, retraction or source-tier warnings where available; do not invent unavailable bibliographic fields.
4. **Synthesis** - hand off to [literature-synthesis](../literature-synthesis/SKILL.md) for per-paper notes, thematic clusters, contradictions, and gap analysis.
5. **Claim bridge** - when research supports manuscript prose, create citekey-linked notes that [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md) can audit later.

## Deliverables

- Research brief: question, scope, search strategy, corpus table, and evidence gaps.
- Literature synthesis with bracket-key citations and source-tier notes.
- Fact-check report: claim, source, verdict, uncertainty, action.
- For systematic review mode: protocol draft, inclusion/exclusion criteria, screening counts, and limitations.

## Verification commands

```bash
uv run python -m infrastructure.search.literature search "QUERY" --limit 20
uv run python -m infrastructure.reference.citation validate projects/<project>/manuscript/references.bib
uv run python -m infrastructure.validation.cli evidence projects/<project> --fail-on-issues
```

## References

- [MODE_REGISTRY.md](../MODE_REGISTRY.md)
- [literature-synthesis](../literature-synthesis/SKILL.md)
- [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
