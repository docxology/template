# template_autopoiesis TODO

Forward-only backlog for the combinatoric-grammar exemplar that deterministically generates whole runnable child projects (`src/`, `tests/`, `scripts/`, `manuscript/`) with recompute-based provenance verification and a falsifiable honesty manifest.

## Current validation evidence

- Project tests and coverage: the exemplar gate collected 512 items; observed 511 passed, 1 skipped, 0 failed, with 96.81% coverage on the exemplar-only run. The one skip is the pre-existing signal-domain first-primitive negative-control parametrization (the second signal primitive supplies that control). The manuscript's `{{TEST_COUNT}}` / `{{COVERAGE_PCT}}` tokens come from the render-time measurement in `src/manuscript_variables.py::measure_test_summary`, never a hand-authored number.
- Prerender validation passed: no render-blocking pitfalls or undefined citations.
- Stage-02 analysis completed 7/7 declared scripts (coverage measurement, figure assets, cover art, archetype realization, full-child realization, sealing, manuscript variables).
- Stage-03 rendered the combined PDF (19 pages) and HTML successfully; render logs contain 0 `^! ` errors and the PDF contains 0 `??` markers.
- Stage-04 passed PDF, transmission-bookend, Markdown, output-structure, figure-registry, evidence-registry, design-overlay, and artifact-manifest checks.
- Stage-05 copied 48 publication files to `output/templates/template_autopoiesis/`.
- Strict template drift reported no drift.
- The renderer still reports non-blocking preamble-recovery warnings because `preamble.md` is not fenced as one LaTeX block; this remains a cleanup item below.

## Integrity and template-status gaps

- Keep the grammar the single source of truth in `manuscript/config.yaml` (`autopoiesis:` block) and all generation logic in `src/` (`grammar.py`, `expand.py`, `materialize.py`, `realize.py`, `sealing.py`, `verify.py`, `honesty.py`) — scripts stay thin orchestrators.
- **Shipped:** materialization consumes `src/emit_templates.py::emit_all` for every child-facing analysis, test, project, and manuscript file, so the standalone emitter and generated child cannot drift silently.
- Keep provenance recompute-based: verification must re-derive the tree hash from disk at check time and never trust a recorded manifest hash.

## Configurable-surface gaps

- Keep the placeholder-safe `manuscript/config.yaml.example` synchronized with the live config shape, including the list-form slot and dependency syntax.
- Add an optional archetype-selection filter so forks can materialize a subset of the combinatoric product space rather than one child per domain.

## Documentation and signposting gaps

- Keep README and `SYNTAX.md` clear that Stage 02 expands the grammar and materializes/verifies children, while Stage 03 renders the descriptive manuscript PDF.
- Finish the remaining `SPEC.md` Phase 10 items and keep them in step with the shipped grammar surface.
- Consider fencing `manuscript/preamble.md` as a complete LaTeX block to eliminate renderer recovery warnings.

## Dependency-mode gaps

- `dep_mode="template"` remains intentionally loud (`NotImplementedError`) until a seam contract is defined that does not require parent infrastructure at child runtime.

## Test and validator gaps

- **Shipped:** figure fallback handling has no redundant list-shape branch and explicitly labels empty-array summaries; malformed and under-specified grammar shapes fail before expansion with real negative controls.
- Strengthen the mutation meta-gate with an additional stubbed-kernel case per domain, so green-by-construction theater cannot slip through as new domains are added.
- Eliminate the remaining meta-gate skip by selecting the first available negative-control primitive per domain (the signal domain's first primitive has none).

## Ordered improvement ladder

1. Eliminate the remaining test skip by selecting the first available negative-control primitive per domain, then regenerate measured outputs.
2. Extend mutation meta-gate coverage across all domains and kernels.
3. Add the archetype-selection filter to the configurable surface.
4. Finish `SPEC.md` Phase 10 and re-sync it with the shipped grammar.
