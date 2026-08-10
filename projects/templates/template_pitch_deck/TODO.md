# template_pitch_deck TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
next action, proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

## Integrity and template-status gaps

- Keep PPTX ZIP-member timestamps normalized and require two-run PDF/PPTX
  digest equality in the deterministic artifact gate.
- Keep all three lengths in the raster QA matrix and fail on clipping or overlap
  when the configured raster toolchain is available.
- Mermaid diagram rendering requires `mmdc` (mermaid-cli) + a resolvable Chrome/Chromium on PATH; `scripts/15_generate_diagrams.py` degrades to a logged warning (not a hard failure) when unavailable, so a fresh clone without those tools still renders all six artifacts, just without the diagram figure embedded. Confirmed this degradation path fires correctly (session 4): `mmdc` itself started hanging past its internal 90s timeout in this dev environment mid-session (traced to ~190 leaked Chrome/puppeteer processes accumulated across many `15_generate_diagrams.py` invocations this long session — each successful run's Chrome subprocess wasn't being reaped) — the script logged the timeout and continued rather than crashing, exactly as designed. Killing the stray processes (`pkill -9 -f "Chrome for Testing"` / `puppeteer_dev_chrome_profile"`) is the fix when this recurs; the existing `output/figures/*.png` files remain valid (unchanged Mermaid source) even when a given regeneration attempt can't complete.
- Keep publication DOI/repository metadata source-bound and distinguish an
  unavailable deposit from a real owner-authorized publication receipt.
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

- Keep deterministic generated-sequence tests proving budget filtering is
  prefix-preserving and non-mutating across boundary and oversized decks.
- `mermaid_figure.py`'s real-render tests are skipped when `mmdc` is absent; CI coverage of that path depends on the runner having mermaid-cli installed.
- Keep adversarial token sequences in the regression suite so generated decks
  cannot leak unresolved braces.

## Minor upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Medium upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Major upcoming

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
