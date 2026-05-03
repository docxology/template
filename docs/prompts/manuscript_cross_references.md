# Prompt: Manuscript registry and cross-references

## Purpose

Audit or author manuscript text when the project uses a **YAML registry plus inline tokens** (figures, equations, sections, theorems, citations) instead of (or in addition to) Pandoc-crossref `@fig:` / `@eq:` / `@sec:` and `references.bib` only.

Exemplar: projects that ship `manuscript/refs/labels.yaml`, `manuscript/refs/citations.yaml`, and body tokens such as `[[FIG:…]]`, `[[FIGREF:…]]`, `[[EQ:…]]`, `[[EQREF:…]]`, `[[SECREF:…]]`, `[[SEC:…]]`, `[[THM:…]]`, `[[THMREF:…]]`, `[[CITELIST:…]]`, `[@citekey]`, `[[VAR:…]]`.

## Context

- [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md) — Pandoc / `pandoc-crossref` / `[@key]` conventions for template exemplars.
- [`../rules/manuscript_style.md`](../rules/manuscript_style.md) — house style.
- Project-local `manuscript/refs/README.md` (when present) — token grammar for that tree.

## Copy-paste prompt

```
You are working on a manuscript that uses a labels/citations registry (YAML) and injector tokens in Markdown.

SCOPE: [path or project name, e.g. projects/<name>/manuscript/]

Rules:
1. Single source of truth: refs/labels.yaml (figures, equations, sections, theorems) and refs/citations.yaml (or references.bib if hybrid). Every token label must exist in the registry; every [@citekey] must resolve.
2. Do not hard-code theorem, section, figure, or equation numbers in running prose (e.g. "Theorem 7.3", "§8", "Figure 2", "Eq. (3)") unless the house style explicitly keeps them only in INDEX/nav tables. Prefer [[THMREF:…]], [[SECREF:…]], [[FIGREF:…]], [[EQREF:…]].
3. Figure captions stored in YAML cannot rely on [[…]] expansion unless the renderer documents a second pass; prefer neutral captions that do not duplicate numbering that can drift.
4. Keep subsection headings and labels.yaml `sections:` / `theorems:` numbers in sync; after renumbering, grep the manuscript for stale numbers.
5. Bibliography: if 99_* uses [[CITELIST:all]] or generator output, do not hand-maintain a parallel list that can diverge.

Tasks:
- List any missing, orphan, or duplicate registry keys.
- List any hard-coded § / Theorem / Fig. / Eq. in body files that should be tokenized.
- Propose concrete edits (file + snippet) for alignment.

Verification (adjust paths):
  uv run python scripts/validate_manuscript.py
  # or project-local equivalent under projects/<name>/scripts/
  uv run python -m infrastructure.validation.cli markdown projects/<name>/manuscript/
```

## Checklist

- [ ] Every `[[FIG:…]]` / `[[EQ:…]]` label exists under `figures:` / `equations:` in `labels.yaml`.
- [ ] Every `[[SECREF:…]]` / `[[SEC:…]]` maps to `sections:`.
- [ ] Every `[[THMREF:…]]` maps to `theorems:`; displayed numbers are unique per logical statement where readers expect it.
- [ ] Citations: YAML/BibTeX keys match body `[@…]`; no orphan YAML keys for cited works.
- [ ] Post-injection output (if used) builds without unresolved `[[MISSING:…]]` markers.

## See also

- [`manuscript_creation.md`](manuscript_creation.md) — full manuscript scaffold prompt.
- [`validation_quality.md`](validation_quality.md) — broader QA.
- [`literature_synthesis.md`](literature_synthesis.md) — LLM blocks for search corpora.
