---
name: template-manuscript-cross-references
description: |
  Audit or author registry-driven manuscript cross-refs — labels.yaml, [[FIG:]], [[THMREF:]],
  [[VAR:]] tokens. USE WHEN fixing figure/equation/theorem numbering, orphan registry keys,
  hard-coded "Theorem 7.3" in prose, or [[MISSING:]] injection failures — even for Pandoc
  projects that also use a YAML registry.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - registry-audit
  related_skills:
    - template-validation-quality
    - template-manuscript-claim-verification
---

# Manuscript cross-references (registry tokens)

For Pandoc-crossref `@fig:` / `[@key]` exemplars, see [`docs/guides/manuscript-semantics.md`](../../guides/manuscript-semantics.md). This skill is for **YAML registry + inline tokens**.

> **Convention, not built-in infrastructure.** `refs/labels.yaml` and `[[FIG:]]`/`[[THMREF:]]`/`[[VAR:]]` tokens are a project-authored convention, not a dedicated parser in `infrastructure/`: no current public exemplar under `projects/templates/` uses this style (all ship Pandoc-crossref), and there is no `labels.yaml`-specific validator. Validation for a project that adopts this convention still runs through the generic `infrastructure.validation.cli markdown`/`prerender` checks below plus project-local test coverage the project author writes — token expansion is the project's own `manuscript_variables.py`-style substitution, not a shared registry engine.

## Natural invoke

- "Audit [[FIG:]] tokens in actinf_policy_entanglement_lean manuscript"
- "Hard-coded section numbers in prose — tokenize them"
- "labels.yaml has orphan keys"

## Inputs to confirm

- **Scope** — `projects/<name>/manuscript/` path or project name.
- **Style** — confirm registry/token vs pure Pandoc-crossref (do not mix styles in repairs).

## Workflow

1. **Registry truth** — `refs/labels.yaml` (figures, equations, sections, theorems) and `refs/citations.yaml` or hybrid `references.bib`. Every token label must exist; every `[@citekey]` must resolve.

2. **No hard-coded numbers** — prefer `[[THMREF:…]]`, `[[SECREF:…]]`, `[[FIGREF:…]]`, `[[EQREF:…]]` over "Theorem 7.3", "§8", "Figure 2" in body prose.

3. **Captions** — YAML-stored captions may not expand `[[…]]` unless renderer documents second pass.

4. **Sync** — subsection headings and `labels.yaml` section/theorem numbers aligned; grep for stale numbers after renumbering.

5. **Bibliography** — if `99_*` uses `[[CITELIST:all]]`, do not hand-maintain a parallel list.

6. **Report** — missing/orphan/duplicate keys; hard-coded numbers to tokenize; concrete edits (file + snippet).

## Verification commands

```bash
uv run python -m infrastructure.validation.cli markdown projects/<name>/manuscript/
uv run python -m infrastructure.validation.cli prerender projects/<name>/manuscript --repo-root .
```

## When NOT to use

- **Full manuscript scaffold** → [manuscript-creation](../manuscript-creation/SKILL.md)
- **Triple-check every factual claim** → [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)

## References

- [`docs/rules/manuscript_style.md`](../../rules/manuscript_style.md)
- Project-local `manuscript/refs/README.md` when present
