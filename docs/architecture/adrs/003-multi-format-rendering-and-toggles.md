# ADR 003 — Multi-Format Rendering and Per-Format Toggles

- **Status:** Accepted
- **Date:** 2026-05-20
- **Amended:** 2026-08-14 — DOCX/EPUB now consume a fresh shared combined
  Markdown source and Stages 3–5 enforce one effective-format contract.
- **Extends:** the scope-implication of stage `PDF Rendering` in [ADR 002](002-declarative-dag-pipeline.md).

## Context

Through 2026-05, the rendering stage emitted three formats (PDF + HTML +
Slides) unconditionally. There was no per-format opt-out, and no path for
DOCX (the most-requested deliverable format for journal submission and
collaborative editing) or EPUB (long-form e-reader distribution).

User-facing pain:

- A project that wants only HTML still pays the xelatex cost on every run.
- A project that needs a Word document for a reviewer's markup pass has no
  pipeline support.
- The `Stage: PDF Rendering` label in `pipeline.yaml` undersells what the
  stage actually delivers.

Internally, the rendering pipeline already used **pandoc** for HTML output
and combined-PDF preprocessing. DOCX and EPUB are one pandoc invocation
away. The architectural delta was small; the documentation surface was the
larger task.

## Decision

1. **Single renderer engine: pandoc.** DOCX and EPUB are added as thin
   pandoc-backed renderer modules (`infrastructure/rendering/docx_renderer.py`,
   `infrastructure/rendering/epub_renderer.py`).
2. **Per-format toggles on `RenderingConfig`.** Five booleans:
   `enable_pdf`, `enable_html`, `enable_slides`, `enable_docx`, `enable_epub`.
3. **Config surface = `manuscript/config.yaml`.** A new `render.formats`
   block exposes the same booleans:

   ```yaml
   render:
     formats:
       pdf: true
       html: true
       slides: true
       docx: true
       epub: false
   ```

   Validated by `infrastructure/core/config/schema.py` with strict
   `additionalProperties: false` on the inner block.
4. **Default behaviour preserves the status quo.** PDF/HTML/Slides default
   `True`; DOCX/EPUB default `False`. Existing projects that don't add the
   `render` block see identical output to before.
5. **Env-var override.** `ENABLE_PDF=0/1`, …, `ENABLE_EPUB=0/1` override
   yaml; yaml overrides defaults. Useful for CI runs that need a subset.
6. **Stage name preserved.** `pipeline.yaml` still calls the stage
   `PDF Rendering` — renaming would churn ADR 002 reading order. This ADR
   records the name-vs-scope mismatch as intentional.
7. **Fresh shared source for non-PDF combined editions.** When DOCX or EPUB is
   enabled, Stage 3 builds `output/web/_combined_manuscript.md` from the current
   ordered manuscript inputs and records its composition. It does not reuse a
   prior PDF artifact or require PDF to be enabled.
8. **One effective-format contract across Stages 3–5.** Explicit environment
   values override YAML independently per format. Stage 3 removes stale
   renderer-owned deliverables before rendering, Stage 4 validates every
   enabled canonical deliverable and rejects disabled-format leftovers, and
   Stage 5 filters disabled renderer-owned artifacts from the fresh copied tree
   before validating it.

## Alternatives considered

| Alternative | Why rejected |
| --- | --- |
| Split into one DAG stage per format | Stage-count churn; breaks ADR 002 reading order; the cost is amortised inside one stage anyway |
| All five formats on by default | Surprises projects that don't ship a DOCX/EPUB pandoc toolchain; default-off is the safer migration |
| Renderer-per-format CLI flag (`--no-pdf`, `--with-docx`) | Per-project yaml is the existing config surface; flag-driven is less reproducible than config-driven |
| python-docx instead of pandoc | Pandoc already present; second engine = second source of truth for citation/crossref pipeline |

## Consequences

**Positive**

- Opt-in by default → zero-friction migration for existing projects.
- Five-format capability with one new config key.
- `RenderingConfig` is the single discovery point for format capability.
- The pandoc dependency stays unchanged; no new system-level tool needed.
- PDF, DOCX, and EPUB can be selected independently without publishing a stale
  artifact from a prior format configuration.

**Negative**

- The YAML stage label `PDF Rendering` is now historically narrow. This ADR
  is the durable record of why we kept it.
- The shared combined Markdown is an internal renderer-owned artifact, not a
  publication deliverable; its current-input composition receipt must remain
  coupled to the export that consumes it.

**Migration**

- The combined-export path in
  `infrastructure/rendering/_combined_exports.py` gates each renderer on
  `config.enable_<fmt>` and uses `prepare_shared_combined_markdown()` for
  current DOCX/EPUB inputs.
- `infrastructure/validation/output/render_formats.py` is the shared Stage 4/5
  loader, exact-deliverable validator, disabled-output rejector, and copied-tree
  filter.
- Schema diff: `infrastructure/core/config/schema.py` gained a `render`
  top-level key with a nested `formats` sub-schema.
- Per-project validator: `projects/templates/template_prose_project/src/config.py`
  has its own `_KNOWN_TOP_LEVEL_KEYS` whitelist that needed `"render"` added.
  Any future project with a similar whitelist must do the same.

## References

- Source: `infrastructure/rendering/docx_renderer.py`,
  `infrastructure/rendering/epub_renderer.py`,
  `infrastructure/rendering/config.py` (`RenderingConfig`),
  `infrastructure/rendering/_combined_exports.py`
  (`prepare_shared_combined_markdown`, `render_combined_outputs`), and
  `infrastructure/validation/output/render_formats.py`.
- Schema: `infrastructure/core/config/schema.py` (`render` property).
- Tests: `tests/infra_tests/rendering/test_docx_renderer.py`,
  `test_epub_renderer.py`, `test_format_toggles.py`,
  `test_combined_exports.py`;
  `tests/infra_tests/validation/test_render_formats.py`; and
  `tests/infra_tests/test_stage_05_copy_formats.py`.
- Docs: [`../../usage/output-formats.md`](../../usage/output-formats.md),
  [`../../operational/logging/output-design.md`](../../operational/logging/output-design.md).
- Related ADRs: [`002-declarative-dag-pipeline.md`](002-declarative-dag-pipeline.md)
  (stage definition).
