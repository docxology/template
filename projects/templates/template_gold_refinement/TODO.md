# template_gold_refinement TODO

Forward-only backlog for the metallurgical gold-refining analogy exemplar:
manuscript composition modeled as ore → smelting → assaying → cupellation →
nine-nines certification, with karat grading and deterministic mega-madlib
token composition.

## Current validation evidence

- Project tests and coverage (read live counts from
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not a
  pinned number here):
  `uv run pytest projects/templates/template_gold_refinement/tests/ --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90`
- Stage-02 refinery analysis (figures, token injection, evidence/figure registries):
  `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_gold_refinement`
- Stage-03 manuscript render (ore → nine-nines certification, zero unresolved `{{TOKEN}}` vars):
  `uv run python scripts/pipeline/stage_03_render.py --project templates/template_gold_refinement`
- Confidentiality and drift guards:
  `uv run python scripts/audit/check_tracked_all.py` and
  `uv run python scripts/audit/check_template_drift.py --strict`

## 2026-08-02 review-and-render pass

- Validation evidence (measured on this pass): 328 project tests passing,
  coverage ≥ 90% project gate; pre-render CLI reports no render-blocking
  pitfalls; drift check reports no drift; combined PDF renders with 0 `^! `
  log lines and 0 unresolved `??` markers (41 pages); stage-04 output
  validation passes all checks.
- Added the two missing `.agents/` catalog READMEs (`.agents/README.md`,
  `.agents/skills/README.md`) so every exemplar catalog level carries
  AGENTS.md + README.md per the shared template contract.
- Synchronized `manuscript/config.yaml.example` with the live config shape:
  both files carry `publication.repository_url`, `publication.repository_label`,
  a placeholder `publication.published_artifacts` map, and
  `gold_refinement.narrative_moves` covering all ten configured sections
  (`evaluation` and `authoring_contract` added to the live config so
  `narrative_moves` matches `section_conditions`/`section_titles` and the fork
  template). Outputs were regenerated through stages 02-05 after the config
  change.
- Replaced placeholder cross-reference examples in `manuscript/SYNTAX.md` and
  `docs/syntax_guide.md` with real project labels (`eq:purity_functional`,
  `eq:monotone_refinery`, `fig:purity_progression`, `tbl:formalism_registry`).
- Verified the full surface programmatically: every relative Markdown link
  resolves; scripts/tests AGENTS listings match the files on disk; version
  markers agree across pyproject.toml, config.yaml, CITATION.cff,
  codemeta.json, .zenodo.json, and the figure registry; all documented
  `src/`/`scripts/` symbols exist; manuscript tokens all resolve to generated
  variables.

## Integrity and template-status gaps

- Keep the refinery pipeline (ore → smelting → assaying → cupellation →
  nine-nines certification) as the gated default path, with purity monotonic
  across stages.
- Keep mega-madlib token injection deterministic, seeded, and config-owned
  (lexicon in config, no hardcoded selections).
- Keep `src/evidence.py` cross-checking every manuscript contribution claim
  against its evidence source, including dotted Python member paths.
- Add transmission bookends (`transmission_begin` / `transmission_end`
  manuscript sections) framing the certified output.
- Preserve the no-mocks / deterministic-seed policy for any new refinery stage
  or assay probe.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` aligned with the shipped config blocks
  (`contribution_claims`, `pipeline_phases`, `audit_rules`, `steganography`,
  `evaluation`, `authoring_contract`, and explicit LLM-review gates) when code
  defaults change.
- Extend the implemented prefix-constrained reverse assay with an optional
  config-selected target and generated report surface.
- Extend the implemented noncompensatory `PurityVector` with domain-selected
  dimensions only after a fork supplies evidence for those dimensions.

## Documentation and signposting gaps

- Keep README and AGENTS clear that Stage 02 generates figures and the
  evidence/figure registries while Stage 03 renders the certified manuscript.
- Keep `docs/domain_fork_guide.md` and `src/domain_adapter.py` cross-linked so
  forkers can remap stages (clinical evidence, legal citation, engineering spec).
- Keep the analogy-break boundary documented: where gold-refining fails as a
  model for manuscript composition.

## Test and validator gaps

- Add references (published or recorded) for the planned documented
  commercial/book platforms — `amazon_kdp`, `google_play_books`, `gumroad`,
  `leanpub`, `lulu`, `draft2digital`, `stripe`, `ingramspark` — so the
  publishing-status block is verifiable rather than aspirational.
- Add a validator for the analogy-break boundary formalized as a theorem: for
  what class of manuscript quality processes does the refining analogy hold?
- Connect the refinery to real manuscript validation infrastructure
  (`infrastructure.validation`) and measure actual purity on a real paper.

## Ordered improvement ladder

1. Keep the refinery pipeline, deterministic token injection, and evidence
   registry green under the 90% project coverage gate.
2. Add transmission bookend manuscript sections.
3. Publish or record references for the planned documented platforms.
4. Expose the implemented reverse assay (target purity → shortest ordered prefix) through config and a generated report.
5. Add config selection for the implemented multi-objective purity vector without introducing an unvalidated aggregate score.
6. Formalize the analogy-break boundary as a theorem with a matching validator.
7. Wire the refinery to `infrastructure.validation` and measure purity on a
   real manuscript.
