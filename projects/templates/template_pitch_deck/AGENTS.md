# AGENTS: Template Pitch Deck

Technical specification for the pitch-deck generation exemplar.

**Location:** [`projects/templates/template_pitch_deck/`](.) — public canonical exemplar (`infrastructure.project.public_scope`).

## Purpose

Reproducible, validated pitch-deck generation: one token-resolved content
source renders to six real artifacts (short/medium/long × PDF/PPTX), with
every fact traced live to the repository, every slide checked for pitch-deck
cliché, and every claim optionally deep-linked to its source file.

## Architecture

```text
template_pitch_deck/
├── manuscript/
│   ├── deck_content_{short,medium,long}.yaml   # the pitch content itself
│   ├── config.yaml                              # project_config.deck: theme, source URL, subject
│   └── 00_abstract.md … 99_references.md        # standard "about this template" manuscript
├── src/
│   ├── content_loader.py       # YAML → DeckContent (token-resolved)
│   ├── token_resolution.py     # {{TOKEN}} substitution + raise-on-missing
│   ├── cliche_lint.py          # word-boundary denylist
│   ├── deck_audit.py           # shared token+cliche audit (used by 2 scripts)
│   ├── diligence_audit.py      # fact-token → source-citation coverage check
│   ├── deck_tokens.py          # live repo introspection → token values
│   ├── standalone_slides.py    # per-slide standalone .md pages + QR URL computation
│   ├── coverage_chart_data.py  # live COUNTS.md → per-exemplar coverage rows (chart data)
│   ├── infra_facts.py          # live infrastructure/ subpackage/file counts, reusing counts_doc.py
│   ├── chart_rendering.py      # matplotlib plotting logic for scripts/16_generate_charts.py
│   ├── render_orchestration.py # ties audit → diligence-gate → standalone-pages → QR-attach → render together
│   └── paths.py                # repo-root discovery
├── scripts/
│   ├── 10_audit_deck_content.py   # token + cliche audit (fails closed)
│   ├── 15_generate_diagrams.py    # Mermaid → PNG ×3 (required; fails closed without mmdc/Chrome)
│   ├── 16_generate_charts.py      # matplotlib charts ×3 (bar/scatter/donut) — thin dispatcher over chart_rendering.py
│   ├── 20_render_decks.py         # the six-artifact render (thin wrapper around render_orchestration.py)
│   └── 30_audit_diligence.py      # citation-coverage audit (standalone; also runs inside render_orchestration.py itself)
├── tests/                      # 90%+ coverage on src/, no mocks
└── output/                     # pdf/, pptx/, figures/, slides_standalone/
```

The actual rendering logic — `Slide`/`DeckContent`/`DeckTheme` dataclasses,
the ReportLab PDF renderer, the python-pptx renderer, and the standalone
Mermaid-to-PNG renderer — lives in `infrastructure/rendering/{slide_deck,pptx_deck,mermaid_figure}.py`,
not in this project's `src/`. This is a deliberate departure from the
`template_newspaper`/`template_storybook` precedent (which keep their
bespoke ReportLab layout engines in project-local `src/`): a slide deck is a
generic, reusable output shape — like DOCX or EPUB — not a domain-specific
layout, so it belongs alongside `infrastructure/rendering/docx_renderer.py`
and `epub_renderer.py`. Both renderers consume the same exact Helvetica
glyph-width fitter and precomputed body-line layout from `slide_deck.py`, so
PDF and PPTX stay in fitted-size and line-break parity, not just
text/slide-count parity. The shared preflight fails before output replacement
if a title cannot fit at the legibility floor or body text would enter the
full-width protected band above the QR/source footer.
The PPTX renderer also normalizes OOXML ZIP-member timestamps after save;
two identical renders must have the same SHA-256 digest.

Medium and long keep the public roster presentation-readable without
weakening its evidence: one cited slide contains the exact live public roster,
and the next carries the two original contract claims with the same citation.
Executable content tests bind both authored decks to their declared budgets.
The subpackage donut independently chooses black or white percentage text
from each real wedge artist's alpha-composited color and fails below 4.5:1.

### Per-slide QR deep-links (`src/standalone_slides.py`)

Every slide gets a scannable, click-through QR code (bottom-right, both
renderers) pointing at that exact slide's own standalone Markdown page under
`output/slides_standalone/{pitch_subject}_{length}/slide_NN.md` — real
content (title, body, citation, back-links to the full deck and its content
source), not a redirect stub. `render_orchestration.py::render_one_length`
writes these pages and attaches each slide's URL (`Slide.qr_url`) before
rendering. This extends the diligence system one step further: `source`
citations point *out* to evidence; a slide's QR points *at* the slide itself,
so a photo of a projected/printed slide can always be traced back to
"was this actually said, and can I verify it" — starting from nothing but
the photo.

## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-pitch-deck/SKILL.md`](.agents/skills/template-pitch-deck/SKILL.md).

## Key Subsystems

### Content (`src/content_loader.py`)

| Function | Description |
|----------|-------------|
| `load_deck_yaml` | Parse a `deck_content_*.yaml` file |
| `raw_deck_texts` | Flatten every prose field for token/cliche auditing |
| `build_deck_content` | Resolve tokens across all fields, return a `DeckContent` |

### Facts (`src/deck_tokens.py`)

`build_deck_tokens(repo_root, pitch_subject="template_template")` reads:
test count + coverage % from `docs/_generated/COUNTS.md`, DOI/version/license/
github from the pitch subject's own `manuscript/config.yaml`, and the live
exemplar count from `infrastructure.project.public_scope.public_project_names`.
Raises `ValueError`/`FileNotFoundError` rather than fabricating a value when
a fact isn't yet available (e.g. before this project's own COUNTS.md row
exists).

### Validation (`src/token_resolution.py`, `src/cliche_lint.py`, `src/diligence_audit.py`)

Three independent gates: unresolved-token detection (raises, never silently
ships a `{{TOKEN}}` literal), cliché denylist (word-boundary regex,
case-insensitive), and citation coverage (every slide referencing a
`PITCH_SUBJECT_*`/`EXEMPLAR_*` fact token must carry a `source` field —
`title`-kind slides are exempt). Token/cliché checks run via
`deck_audit.audit_deck`, called from both `scripts/10_audit_deck_content.py`
and `render_orchestration.py::render_one_length` (fails closed, before any
render). Citation coverage runs via `diligence_audit.uncited_fact_slides`,
called from both the standalone `scripts/30_audit_diligence.py` AND (added
2026-07-09, after Advisor caught the gap) `render_orchestration.py::render_one_length`
itself — a `DiligenceAuditFailure` blocks that deck length's PDF/PPTX write,
not just the separate script.

## Verification

From the template repo root:

```bash
export PATH="$PWD/node_modules/.bin:$PATH"
uv run pytest projects/templates/template_pitch_deck/tests/ \
  --cov=projects/templates/template_pitch_deck/src --cov-fail-under=90 -v
uv run python projects/templates/template_pitch_deck/scripts/10_audit_deck_content.py
uv run python projects/templates/template_pitch_deck/scripts/20_render_decks.py
uv run python projects/templates/template_pitch_deck/scripts/30_audit_diligence.py
```

## Patterns

- **Thin orchestrator:** scripts delegate to `src/` for content/validation and to `infrastructure/rendering/` for layout — never both in the same place.
- **Zero-mock testing:** real YAML, real rendered PDF/PPTX read back with `pypdf`/`python-pptx`, real repo introspection.
- **Deep-linked diligence:** `source` citations are real clickable hyperlinks (`canvas.linkURL` in the PDF, run hyperlinks in the PPTX), not plain footer text.

## See also

- [`README.md`](README.md)
- [`manuscript/README.md`](manuscript/README.md)
- [`src/README.md`](src/README.md)
- Memory and decision records: [`../../../docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md)
