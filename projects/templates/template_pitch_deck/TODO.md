# template_pitch_deck TODO

Forward-only integrity backlog for the pitch-deck generation exemplar.

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_pitch_deck/tests/ --cov=projects/templates/template_pitch_deck/src --cov-fail-under=90` (derive the live result; do not copy an old count here).
- Infra rendering tests: `uv run pytest tests/infra_tests/rendering/test_slide_deck.py tests/infra_tests/rendering/test_pptx_deck.py tests/infra_tests/rendering/test_pptx_determinism.py`.
- Content audit: `uv run python projects/templates/template_pitch_deck/scripts/10_audit_deck_content.py` — token resolution + cliche lint, all three lengths clean (170 text fields in the long deck alone).
- Diligence audit: `uv run python projects/templates/template_pitch_deck/scripts/30_audit_diligence.py` — 100% fact-citation coverage across all three lengths (this check also runs *inside* `render_orchestration.py` as a real `DiligenceAuditFailure` gate, added session 3).
- Render: `uv run python projects/templates/template_pitch_deck/scripts/20_render_decks.py` — six real artifacts (short/medium/long × PDF/PPTX) + one standalone `.md` page per slide (104 total: 11+37+56), PDF↔PPTX slide-count parity verified.
- Full real pipeline gate: `uv run python scripts/pipeline/stage_01_test.py --project templates/template_pitch_deck --project-only`.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_pitch_deck --strict` — no drift detected (session 4 found and fixed a real thin-orchestrator violation: `scripts/16_generate_charts.py` grew to 202 lines/3 non-trivial functions before the drift checker caught it — moved the actual plotting logic to `src/chart_rendering.py`, leaving the script as a thin fetch→render→save dispatcher).
- Session 3: Advisor (`Inference.ts --level smart`) flagged 5 precision issues in the "Scientific integrity" content (all fixed); Cato (`codex exec --sandbox read-only`, MANDATORY E4 gate) found a real bug (`DiligenceAuditFailure` not caught in `20_render_decks.py` — fixed) plus 3 more precision issues (all fixed). Session 2's Forge in-family fallback (2 MEDIUM + 5 LOW, 5/5 fixed) remains documented in `ISA.md` Decisions.
- Session 4 (font size, chart variety, infrastructure/ introspection, expanded ask): three new visualizations (test-count-vs-coverage scatter, infrastructure/ subpackage donut), a new `src/infra_facts.py` module reusing `infrastructure.documentation.counts_doc`'s own introspection functions, and an expanded "ask" (funding conversations + consulting availability, all three lengths) with no fabricated numbers or committed terms.
- Session 5 (this deck's own DOI, full-roster case study): new `PITCH_DECK_DOI_STATUS` token — reads `template_pitch_deck`'s own `manuscript/config.yaml` `publication.doi` live, honestly reporting "not yet reserved" (verified: no `ZENODO_TOKEN` credential is configured in this environment, so a real DOI cannot be minted right now — the mechanism is built and will pick up a real value automatically the moment a deposit is recorded, exactly like every other live-sourced token in this deck). New `EXEMPLAR_ROSTER` token (all 20 exemplar names, sorted) replaces the prior single-cherry-picked `{{SECOND_EXEMPLAR_NAME}}` case-study framing across all three lengths — the "Case study: X" slides are now "The full roster, not one cherry-picked example," citing `docs/_generated/active_projects.md`. Added a new "Cite this deck" slide to all three lengths.

## Integrity and template-status gaps

- **Shipped 2026-07-11:** PPTX output is byte-reproducible. `pptx_deck.render_pptx()` normalizes every OOXML ZIP-member timestamp, a real archive regression test proves differing source timestamps collapse to identical bytes, and two complete pitch-deck renders separated in time produced identical PDF and PPTX SHA-256 digests.
- **Verified 2026-07-11:** all three PPTX lengths were rasterized through LibreOffice into five thumbnail grids and visually inspected. Slide counts were 11, 37, and 56; no clipping or overlap was visible at grid scale.
- Mermaid diagram rendering requires `mmdc` (mermaid-cli) + a resolvable Chrome/Chromium on PATH; `scripts/15_generate_diagrams.py` degrades to a logged warning (not a hard failure) when unavailable, so a fresh clone without those tools still renders all six artifacts, just without the diagram figure embedded. Confirmed this degradation path fires correctly (session 4): `mmdc` itself started hanging past its internal 90s timeout in this dev environment mid-session (traced to ~190 leaked Chrome/puppeteer processes accumulated across many `15_generate_diagrams.py` invocations this long session — each successful run's Chrome subprocess wasn't being reaped) — the script logged the timeout and continued rather than crashing, exactly as designed. Killing the stray processes (`pkill -9 -f "Chrome for Testing"` / `puppeteer_dev_chrome_profile"`) is the fix when this recurs; the existing `output/figures/*.png` files remain valid (unchanged Mermaid source) even when a given regeneration attempt can't complete.
- Publication status (updated 2026-07-10): this deck now HAS a published concept DOI (`10.5281/zenodo.21281509`, version `10.5281/zenodo.21281510`) and a public standalone repo (`docxology/template-pitch-deck`) recorded in `manuscript/config.yaml`'s `publication:` block; the README PUBLISHING-STATUS block reflects it and `PITCH_DECK_DOI_STATUS` resolves to the live DOI. Historical note: earlier sessions deliberately kept the block empty rather than shipping a placeholder that would falsely flip the status to published.
- PPTX content-slide figure placement is fixed-position while PDF's is flow-positioned below the bullet list (Forge LOW-2) — latent, not currently triggered (all current figures are on `diagram`-kind slides, none on `content`-kind), but a future content slide combining many bullets + a figure would overlap in PPTX only. Fix when content grows: flow the PPTX figure below the body textbox instead of a fixed y-offset.
- QR codes were verified structurally (real annotation/click-action URLs match the intended target exactly, in both PDF and PPTX) but not visually decoded with a QR reader — no `pyzbar`/`cv2`/zbar-based decoder is installed in this environment. The rendered QR's finder-pattern structure was visually raster-checked (page screenshot) and looks correct; a real phone-camera scan test is still recommended before relying on this in an actual presentation.
- Per-slide QR codes link to `output/slides_standalone/*.md` pages that are currently local-only — the deck's own content is explicit about this ("the QR only resolves once it is actually published"), but the QR won't actually scan-through to anything until this project's `output/` directory is committed and pushed to the real GitHub remote. Not a code gap — a publication-sequencing dependency to remember before presenting the deck as-is.
- `render_all_decks` runs short → medium → long sequentially and each length's own audit/diligence gate is independent (Cato finding, session 3): if e.g. `medium`'s diligence check fails, `short`'s PDF/PPTX (already rendered first) remain on disk even though the overall run reports failure. Each length's own gate is real and blocking (verified), but there's no cross-length "audit everything first, render nothing until all lengths pass" transaction. Low practical impact (a failing audit is a authoring bug caught immediately in this small, fully-owned content set) but worth fixing if this schema is ever forked to a much larger multi-length content set where partial output could be mistaken for a complete deck.

## Configurable-surface gaps

- Only one pitch subject (`template_template`) is authored; the schema (`manuscript/deck_content_*.yaml` + `src/deck_tokens.py`) supports adding a second, broader meta-science-group deck by adding a new subject key to `manuscript/config.yaml`'s `deck:` block — not yet done.
- Theme is currently monochrome-red (black + white + 3× the same highlight, `manuscript/config.yaml`'s `deck.theme` block); `config.yaml.example` demonstrates a distinct 3-accent palette as a starting point for forks.
- `SlideBudget` (short/medium/long max-slide counts, currently 11/38/58) lives in `infrastructure/rendering/slide_deck.py`, not per-project config — a fork wanting different length budgets currently edits the shared infrastructure constant.

## Documentation and signposting gaps

- `manuscript/README.md` and `src/README.md` are new, minimal — expand with worked examples if this exemplar gains a second pitch subject.
- No architecture diagram doc yet beyond the in-deck Mermaid figure itself; consider a `docs/architecture.md` mirroring `template_newspaper`'s.

## Test and validator gaps

- **Shipped:** deterministic generated-sequence tests prove budget filtering is
  prefix-preserving and non-mutating across boundary and oversized decks.
- `mermaid_figure.py`'s real-render tests are skipped when `mmdc` is absent; CI coverage of that path depends on the runner having mermaid-cli installed.
- **Shipped:** generated adversarial uppercase token sequences assert complete
  resolution without leaked braces.

## Ordered improvement ladder

1. Add the second pitch-subject deck (a broader meta-science-group pitch) to prove the schema generalizes beyond `template_template`.
2. Add a `docs/architecture.md` walkthrough of the theme/slide-kind/diligence system.
3. Add hypothesis-based property tests for budget filtering and token resolution.
