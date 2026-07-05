# `template_textbook/docs/` — Agent Guide

Documentation set for the **fillable book-length scaffold** exemplar. The book's
structure is data-driven from [`../manuscript/config.yaml`](../manuscript/config.yaml);
a tested `src/textbook` engine scaffolds/validates/illustrates the manuscript;
thin `scripts/` orchestrators wire it into the reproducible pipeline.

## Read order

| Doc | Purpose |
| --- | --- |
| [`README.md`](README.md) | Human entry point + guide index |
| [`architecture.md`](architecture.md) | Two-layer + thin-orchestrator design as applied here |
| [`manuscript_guide.md`](manuscript_guide.md) | Parts → chapters → labs → questions; per-chapter required-element contract |
| [`authoring_guide.md`](authoring_guide.md) | The fill-the-stubs workflow; growing the book while keeping the contract green |
| [`visualization_guide.md`](visualization_guide.md) | Deterministic figures + Mermaid; the `<part_id>_<stem>.png` filename contract |
| [`testing_guide.md`](testing_guide.md) | Test suite, no-mocks policy, 90% coverage gate, `audit_textbook_quality.py` |

## Contracts agents must honor

- **Single source of truth:** the book's parts/chapters/labs/figures are declared
  in `manuscript/config.yaml`. Do not hard-code structure in prose or scripts.
- **Thin orchestrators:** logic lives in `src/textbook/`; `scripts/*.py` only
  coordinate I/O, figure generation, and audits.
- **No mocks; deterministic:** real data, fixed seeds, `MPLBACKEND=Agg`.
- **Stub markers** are `<!-- STUB -->`, `TODO:`, `TKTK`; replace with real
  content when filling the book.

## Status

This exemplar is a **tracked public canonical project** (see
[`docs/_generated/active_projects.md`](../../../../docs/_generated/active_projects.md)).
Published on Zenodo (concept DOI `10.5281/zenodo.20533125`).

## See also

- [`../AGENTS.md`](../AGENTS.md) — project map + promotion checklist
- [`../../../../infrastructure`](../../../../infrastructure) — Layer-1 engine the scripts call
