---
project: template_newspaper
effort: E5
phase: complete
progress: 44/44
mode: build
started: 2026-05-31
updated: 2026-05-31
---

# ISA — `template_newspaper` ("The Triplicate")

## Problem

The research-template monorepo had canonical exemplars for *code* projects and
*prose* projects, but nothing that demonstrated **designed, multi-column page
layout** — the discipline of turning structured content into a typeset,
print-ready artifact with mastheads, columns, modular boxes and figures. The
`template_newspaper` directory existed but was empty. A newspaper is the
hardest, most legible test of a layout engine: it needs a nameplate, spanning
headlines, flowing columns, rails, pull quotes, tables, halftone art and folios,
all on one page, repeated across a 12-page edition.

## Vision

Open `output/pdf/the-triplicate.pdf` and see, unmistakably, a real large-format
community newspaper: *The Triplicate* of Crescent City, California — nameplate
in elegant Didot, a tsunami-resilience lead with a halftone of the harbor, a
left rail of index and weather, an opinion page with a staff box and letters, a
dense classifieds spread, an almanac back page with a tide curve and a long
historical feature. The euphoric surprise: that all of it is rendered from plain
YAML by a few hundred lines of pure Python, so the reader instantly grasps that
*their* paper is one data edit away.

## Out of Scope

- Interactive/web output, HTML or EPUB newspaper rendering (PDF only).
- A WYSIWYG editor or GUI; content is authored as YAML.
- Real news, real bylines, or live data feeds — this is a template edition with
  illustrative, fictional content.
- Automatic column *balancing* (equal-height columns); flow is sequential by
  column, which is faithful to many real papers.
- Color separations / CMYK pre-press; output is monochrome newsprint.
- **Cross-page story continuation (jump-flow).** Stories flow across *columns*
  within a page; "Continued on Page X" is an authored label with a matching
  continuation story, not automatic cross-page text flow. Real jump-flow is
  deferred.

## Principles

- **Content is data, code is the press.** Editions live in `content/`; the
  engine is content-agnostic. (Substrate independence — a new title must require
  zero code changes.)
- **Degrade, never crash.** Missing fonts fall back to base-14; a missing image
  becomes a labelled placeholder; the render always produces a structurally
  valid PDF.
- **Furniture is drawn, body is flowed.** Fixed elements are placed by
  coordinate; prose flows through frames. This division is what makes spanning
  headlines and column rules coexist with automatic text flow.
- **Verify by looking.** Every layout claim is checked against a rendered raster,
  not asserted from code.

## Constraints

- Pure Python; ReportLab + Pillow + Matplotlib + PyYAML only (all already in the
  workspace `.venv`). No system pre-press tooling required for the newspaper PDF.
- Must satisfy the monorepo project contract: `src/` (Python) + `tests/`, with
  `scripts/` and `manuscript/` optional, so `discover_projects` finds it and the
  pipeline runs it.
- Page trim: US Tabloid 11″ × 17″ portrait by default (configurable).
- Edition is exactly **12 pages** for the canonical deliverable.
- mypy-clean, ruff-clean, ≥85% test coverage (workspace gate).

## Goal

Build `template_newspaper` as a complete, sibling-compatible exemplar that
renders a 12-page, large-format *Triplicate* edition to a print-ready PDF from
structured YAML — with full layout, typography, modular sections and figures —
verified visually page-by-page and green on tests, types and lint.

## Criteria

- [x] ISC-1: `discover_projects(repo_root)` returns `templates/template_newspaper`.
- [x] ISC-2: `validate_project_structure` returns `(True, ...)` for the project.
- [x] ISC-3: `src/newspaper/` is an importable package with the eight documented modules.
- [x] ISC-4: `geometry.py` has no ReportLab import (pure arithmetic).
- [x] ISC-5: `ColumnGrid` partitions width exactly (columns + gutters == width).
- [x] ISC-6: `register_fonts()` always returns usable font names (Didot/Georgia or base-14).
- [x] ISC-7: `build_stylesheet` defines every style the components reference.
- [x] ISC-8: Headline styles set `splitLongWords=0` (no mid-word breaks).
- [x] ISC-9: `load_edition` parses `content/edition.yaml` + 12 page files into an `Edition`.
- [x] ISC-10: Strict config rejects unknown `render` keys with a quoted message.
- [x] ISC-11: Content loaders reject bad template/level/box-kind with named errors.
- [x] ISC-12: `figures.generate_all` writes 6 PNGs (3 halftone scenes + 3 charts).
- [x] ISC-13: Halftone scenes render as 45° dot screens (visually verified).
- [x] ISC-14: Charts are grayscale, serif-labelled, newsprint-styled (visually verified).
- [x] ISC-15: `render_edition` produces a PDF beginning with `%PDF-`.
- [x] ISC-16: The PDF has exactly 12 pages (`pdfinfo` and token count agree).
- [x] ISC-17: Page size is 792 × 1224 pt (Tabloid).
- [x] ISC-18: `RenderResult.all_pages_fit` is True (no over-set pages drop copy).
- [x] ISC-19: Front page renders nameplate, ears, rail, spanning lead, drop cap, halftone (visual).
- [x] ISC-20: Inside pages render a section band + folio + column rules (visual).
- [x] ISC-21: Opinion page renders staff masthead box + letters + signed column (visual).
- [x] ISC-22: Classifieds render as dense flowing ads + directories + display boxes (visual).
- [x] ISC-23: Weather page renders 7-day chart + tide curve + data tables + history feature (visual).
- [x] ISC-24: All 12 pages are visually filled (no broken white gaps) — contact sheet verified.
- [x] ISC-25: `scripts/00_preflight.py` exits 0 and reports the loaded edition.
- [x] ISC-26: `scripts/10_generate_figures.py` writes all figures and exits 0.
- [x] ISC-27: `scripts/20_render_newspaper.py` renders the PDF + writes render_report.json.
- [x] ISC-28: `pytest` passes (28 tests).
- [x] ISC-29: Coverage ≥ 85% (measured 95.33%).
- [x] ISC-30: `mypy src/newspaper` is clean.
- [x] ISC-31: `ruff check` is clean on src/scripts/tests.
- [x] ISC-32: Anti: no module hard-codes a font name outside `typography.py`.
- [x] ISC-33: Anti: rendering never raises on a missing image or missing font (placeholder/fallback).
- [x] ISC-34: Render is byte-deterministic (invariant mode) — same content, identical bytes.
- [x] ISC-35: The over-set detector is flip-tested — an over-long story yields `all_pages_fit == False`.
- [x] ISC-36: Editorial pages render at a 4-column measure (classifieds dense at 6).
- [x] ISC-37: Color figures render as RGB (`ad_*` graphics, festival banner).
- [x] ISC-38: The `Ad` display-ad type renders for every border (box/double/thick/none).
- [x] ISC-39: Strict ad loader rejects a missing `sponsor` / unknown `border` with a named error.
- [x] ISC-40: `spot_color` actually changes rendered bytes (colored flag verified in teal).
- [x] ISC-41: Anti: an over-tall ad is over-set-detectable (non-splitting), not silently shrunk.
- [x] ISC-42: Front-page nameplate fits BETWEEN the boxed ears — no letter/ear overlap (visual + `pdftotext` strings present).
- [x] ISC-43: The sans face is an embedded TTF (Arial) where available, not base-14 Helvetica (renders portably).
- [x] ISC-44: Color PNGs are inserted and embedded as RGB in the PDF (`pdfimages` lists ≥1 rgb image).

## Test Strategy

| isc | type | check | threshold | tool |
|-----|------|-------|-----------|------|
| 1–2 | integration | discovery + validation return project | exact | `python -c` |
| 4 | static | no `reportlab` substring in geometry.py | 0 hits | `grep` |
| 5 | unit | grid width reconstruction | ±0.01 pt | `pytest` |
| 6–8 | unit | font/stylesheet invariants | all present | `pytest` |
| 9–11 | unit | loader happy-path + error messages | substring | `pytest` |
| 12,15–18,29 | integration | render real edition, assert PDF | 12 pages, fit | `pytest` |
| 13,14,19–24 | visual | raster each page, inspect | reads as newspaper | `pdftoppm` + Read |
| 25–27 | integration | run each script | exit 0 + artifact | `bash` |
| 28,30,31 | gate | pytest / mypy / ruff | green | CLI |

## Features

| name | satisfies | depends_on | parallelizable |
|------|-----------|------------|----------------|
| geometry | ISC-4,5 | — | yes |
| typography | ISC-6,7,8,32 | — | yes |
| content model + loaders | ISC-9,10,11 | — | yes |
| figures | ISC-12,13,14 | — | yes |
| components (flowables) | ISC-19,21,22,33 | typography | no |
| furniture (canvas) | ISC-19,20 | typography,geometry | no |
| layout (frames+flow) | ISC-18,20,22 | components,furniture | no |
| engine | ISC-15,16,17,18 | layout | no |
| content (12 pages) | ISC-19..24 | content model | yes |
| scripts | ISC-25,26,27 | engine | no |
| tests | ISC-28,29 | all | yes |
| docs + boilerplate | sibling parity | — | yes |

## Decisions

- 2026-05-31: Chose **ReportLab** over WeasyPrint — pure-Python, no system
  (pango/cairo) deps, and exact frame/rule control suited to newspaper columns.
- 2026-05-31: Trim = **Tabloid 11×17** as the "large-format newsletter" the user
  asked for — large, single-sheet, renders crisply; broadsheet/berliner/letter
  also supported via config.
- 2026-05-31: **Hybrid layout** (drawn furniture + flowed columns) instead of a
  pure `BaseDocTemplate`, because spanning headlines and standing boxes do not
  compose with whole-document auto-flow.
- 2026-05-31: Fixed Didot bold subfont index (2, not 1 = italic) after the first
  render showed italic headlines — caught by visual verification.
- 2026-05-31: Decoupled the **rail** from the column grid (fixed 1.55″) so main
  columns keep a readable ~1.9″ measure; `page.columns` now counts main columns.
- 2026-05-31: refined: classifieds flow **unboxed and dense** (split across
  columns) with a separate `display` box kind for house ads — boxed categories
  wasted vertical space and left the page 70% empty.
- 2026-05-31: refined: under-set feature pages (weather, opinion) filled with
  **prose** (long history feature, more letters) + data boxes — prose fills a
  15″ column where compact boxes do not.
- 2026-05-31: Kept a renderable `manuscript/` so the pipeline's Stage 03 still
  produces a descriptive PDF; the newspaper PDF itself is produced in Stage 02
  by `scripts/`, independent of the infra manuscript renderer.
- 2026-05-31: Advisor review (Inference.ts) flagged four silent-failure risks
  (over-set, determinism, real-pipeline-path, font embedding). All verified
  concretely and the first two bound as flip-tests (ISC-34/35); pipeline path
  proven by running the real `02_run_analysis.py` dispatcher; fonts confirmed
  embedded via `pdffonts`. Cross-page jump-flow declared out of scope on record.

## Changelog

- 2026-05-31 (iteration 4 — grand masthead + font embedding): redesigned the
  front-page masthead — the nameplate now fits the clear zone strictly BETWEEN
  compact boxed ears (eliminating the letter/ear overlap the user reported),
  with a top double rule and descender clearance for a grander flag.
  **Root-caused a rendering bug:** the sans role used base-14 Helvetica, which
  is not embedded and rasterised BLANK under this poppler (ears, folio, kickers,
  bylines, captions all vanished in raster though present in the PDF per
  `pdftotext`). Fixed by registering/embedding Arial as the sans face — sans
  text now embeds and renders everywhere (more portable, like Didot/Georgia).
  Confirmed 10 RGB color images embedded via `pdfimages`. 48 tests, mypy/ruff
  clean. Lesson: base-14 fonts are not embedded; prefer embedded TTFs.
- conjecture: ear/folio text rendered fine (it was visible pre-overlap-fix).
  refuted-by: after masthead changes, raster showed empty ear boxes and no
  folio, yet `pdftotext` extracted the exact strings — so the text was correct
  but the sans face (Helvetica, base-14) was not rasterising.
  learned: verify "missing text" against `pdftotext` before assuming a layout
  bug; the failure was a non-embedded-font rasterisation issue, not geometry.
  criterion-now: ISC-43 (sans embeds via Arial); masthead overlap-free + grand.
- 2026-05-31 (iteration 3 — color, ads, spot color): added a color-capable
  **display-ad** system (`Ad` type + `ad_flowables`: background tint, accent,
  graphic, border styles box/double/thick/none, "ADVERTISEMENT" label) and
  placed 6+ worked color ad examples (A2/A6/A7/A8/A11). Added 4 procedural
  **color** ad graphics + a creative festival banner (RGB). Wired the
  `spot_color` render flag (colored nameplate + section labels + band rules,
  `spot_hex`-configurable) — verified in teal, shipped default off to preserve
  the classic flag. Ads are non-splitting (over-set-detectable, per C1). Tests:
  47 pass, 95.55%; mypy/ruff clean; `all_pages_fit: true`. Note: editorial type
  stays monochrome; color enters via photos/charts/ads, as in a real paper.
- 2026-05-31 (iteration 2 — review + 4-column + art): converted all editorial
  pages to a **4-column** measure (classifieds kept dense at 6); the wider
  measure under-filled several pages, so added authentic copy to A2/A3/A7/A9/A10
  to refill — re-rendered `all_pages_fit: true`. Generated three new procedural
  scenes (`lily_fields`, `baseball`, `crab_boat`) and a keyline-plate border on
  all halftones; wired them in with cutlines. Fixed the A2 mislabel (redwoods →
  lily fields). Figure set now 9 (6 scenes + 3 charts); `test_figures` updated.
- conjecture: `/art` (Art skill) would generate AI editorial images.
  refuted-by: no image-model API key in this environment — `GOOGLE_API_KEY`,
  `OPENAI_API_KEY`, `BFL/FLUX`, `REPLICATE` all absent; `~/.claude/PAI/.env`
  does not exist; only `ELEVENLABS_API_KEY` is present.
  learned: external image generation is environment-gated; the robust path is the
  local deterministic figure engine (no API, tracked, reproducible).
  criterion-now: images generated locally and inserted/captioned; adding an
  image API key re-enables `/art` AI generation as a drop-in upgrade.

- conjecture: a 6-column tabloid classifieds page would fill with ~16 categories.
  refuted-by: render showed only ~2 of 6 columns filled.
  learned: a tabloid column holds ~100 lines; filling 6 needs directories +
  legal notices + display ads, not just category lists.
  criterion-now: ISC-22 verified against the dense-flow render.
- conjecture: Didot subfont 1 is Bold.
  refuted-by: TTC inspection — 0=Regular, 1=Italic, 2=Bold; headlines rendered slanted.
  learned: never assume .ttc subfont order; verify with `TTFont(...).face`.
  criterion-now: ISC-8/ISC-19 verified upright-bold.
- conjecture: `all_pages_fit` proves no copy is dropped (ISC-18/35).
  refuted-by: Forge cross-vendor audit (C1) — boxes were wrapped in
  `KeepInFrame(mode="shrink")`, which silently scales an over-tall box to fit
  instead of leaving it unplaced, so the over-set counter never saw it; the
  ISC-35 flip-test only exercised splittable prose, not the box shape.
  learned: a verification harness validated against one input shape must be
  re-exercised against every structurally different shape it claims to cover.
  criterion-now: boxes now flow as plain non-splitting flowables (over-tall
  boxes are counted as over-set); `test_over_tall_box_is_detected_as_overset`
  flips red on the box shape. Shipped edition re-rendered `all_pages_fit: true`.
- conjecture: `_esc` (escaping only `" & "`) was sufficient.
  refuted-by: Forge audit (H1) — `AT&T` corrupted, `5 < 10` corrupted, an
  unclosed `<b>` aborted the whole render with a ReportLab parse error.
  learned: author text needs a real escaper with a tag allowlist.
  criterion-now: `_esc` escapes stray `&`/`<`/`>` (preserving entities + an
  allowlist of `<b>/<i>/<br/>/<font>`); five `test_robustness` escaping tests.
- conjecture: `Figure.span_columns` was a supported feature.
  refuted-by: Forge audit (H2) — referenced in zero render paths (a no-op).
  learned: do not advertise unimplemented API.
  criterion-now: field removed; multi-column spanning declared Out of Scope;
  `Figure` now validates `path`/`height` (M3); loader raises named errors (M1/M2).

## Verification

- ISC-1/2: `discover_projects` → `templates/template_newspaper`; `validate_project_structure` → `(True, 'Valid project structure')`.
- ISC-4: `grep -c reportlab src/newspaper/geometry.py` → 0.
- ISC-12/16/17/18: `render_report.json` → `{"page_count":12,"all_pages_fit":true,"oversets":{}}`; `pdfinfo` → `Pages: 12`, `Page size: 792 x 1224 pts`.
- ISC-13/14/19–24: page rasters inspected via `pdftoppm` + image read; front page, opinion, classifieds, weather and the 12-up contact sheet all read as a real newspaper.
- ISC-28/29: `28 passed`; coverage `95.33%` (gate 85%).
- ISC-30/31: `mypy` → `Success: no issues found in 10 source files`; `ruff check` → `All checks passed!`.
- ISC-25/26/27: scripts exit 0; artifacts `output/pdf/the-triplicate.pdf`, `output/data/render_report.json`, `output/reports/render_summary.txt` present.
- ISC-34: rendered the edition twice → `identical bytes: True` (sha256 match).
- ISC-35: 60-paragraph over-long story → `all_pages_fit == False`, `oversets={1: 55}`; test `test_overset_is_detected_not_silent` flips red on overflow.
- Pipeline proof: `python scripts/02_run_analysis.py --project templates/template_newspaper` ran `10_generate_figures.py` + `20_render_newspaper.py`, rendered 12 pages to the project output path, and verified outputs (exit 0).
- Font embedding: `pdffonts` → `Didot-Bold`, `Didot`, `Georgia`/`Bold`/`Italic` all `emb=yes sub=yes uni=yes`; Helvetica is the universal base-14 fallback.
- Cross-vendor audit (Forge / GPT-5.4, read-only): found C1 (box over-set masking), H1 (escaping), H2 (dead `span_columns`), M1–M3, L1–L3. C1/H1/H2/M1/M2/M3/L3 fixed and bound by tests; L1/L2 documented as accepted minor asymmetries. Post-fix: **40 tests pass**, coverage 95.54%, mypy/ruff clean, shipped edition re-rendered `all_pages_fit: true`, contact sheet re-verified (no visual regression).

