# Rendering Pipeline: Manuscript → PDF

The `manuscript/` directory contains the narrative components of the
editorial-review project. It is compiled into a publication-ready PDF
automatically by the template's rendering infrastructure. This document
describes every step, what it produces, which scripts run it, and how to
troubleshoot failures.

## Prerequisite: Mermaid diagrams need `chrome-headless-shell`

This manuscript embeds **Mermaid** diagrams (see
`manuscript/05_pipeline_internals.md`). When the rendering infrastructure
builds the **combined PDF**, every inline ```mermaid``` block is rasterised
by `mmdc` (mermaid-cli), which drives a **pinned** `chrome-headless-shell`
via Puppeteer. If that exact Chrome build is absent from the Puppeteer cache
(`~/.cache/puppeteer/`), the combined-PDF step — and the whole **PDF
Rendering** pipeline stage — fails with:

```
mmdc failed for inline_mermaid_0001_...: Could not find Chrome (ver. X)
```

Install it once (reversible, one-time per machine):

```bash
npx --yes puppeteer browsers install chrome-headless-shell
# or pin to the exact version mmdc reports as missing:
npx --yes puppeteer browsers install chrome-headless-shell@131.0.6778.204
```

CI provisions this automatically; a fresh local clone does not. The
per-section slide PDFs do **not** need Chrome (no `mmdc`), so a partial
success with slides-but-no-combined-PDF is the signature of this missing
dependency. See
[troubleshooting.md](troubleshooting.md#pdf-rendering-stage-fails-mmdc-could-not-find-chrome).

## The Self-Referential Flow

The pipeline has four phases. Each phase must complete before the next
begins.

### Phase 1 — Run the Prose Pipeline

**Script**: `projects/templates/template_prose_project/scripts/run_prose_pipeline.py`

**Command**:
```bash
uv run python projects/templates/template_prose_project/scripts/run_prose_pipeline.py
```

**Inputs**: `manuscript/*.md`, `manuscript/references.bib`,
`manuscript/config.yaml`.

**What it does**: Loads `ProjectConfig` from `manuscript/config.yaml`, calls
`src.pipeline.run_prose_pipeline`, which delegates to
`infrastructure.prose.analyze_manuscript` and
`infrastructure.reference.citation.parse_bibfile`, evaluates the configured
checks, and writes JSON + Markdown artefacts.

**Outputs**:

| File | Location | Content |
|---|---|---|
| `manuscript_report.json` | `output/` | Raw `ManuscriptReport` (per-file metrics + aggregate) |
| `checks.json` | `output/` | List of `CheckResult` (one per configured check) |
| `review_report.md` | `output/` | Human-readable narrative review |
| `run_summary.json` | `output/` | One-line metadata (pass/fail, counts) |

The `--strict` flag causes the script to exit non-zero if any check fails.

### Phase 2 — Generate Figures and Manuscript Variables

**Scripts**:
`projects/templates/template_prose_project/scripts/y_generate_prose_figures.py` and
`projects/templates/template_prose_project/scripts/z_generate_manuscript_variables.py`

**Commands**:
```bash
uv run python projects/templates/template_prose_project/scripts/y_generate_prose_figures.py
uv run python projects/templates/template_prose_project/scripts/z_generate_manuscript_variables.py
```

**Inputs**: `output/manuscript_report.json` (produced by Phase 1) +
`manuscript/config.yaml` for the variables script.

**What `y_generate_prose_figures.py` does**: Loads the typed
`ManuscriptReport` JSON via
`infrastructure.prose.report.load_report_json`, then calls
`src/figures.py::generate_all_figures` to write three diagnostic PNGs.

**What `z_generate_manuscript_variables.py` does**: Loads the raw report
JSON via `src/manuscript_variables.py::load_report_payload`, calls
`compute_variables` to derive the eleven substitution values, writes them
to `output/data/manuscript_variables.json`, and produces token-substituted
copies of every `manuscript/*.md` under `output/manuscript/`.

**Outputs**:

| File | Location | Content |
|---|---|---|
| `section_word_counts.png` | `output/figures/` | Per-section word-count bar chart |
| `readability_metrics.png` | `output/figures/` | FKGL / FRE / Gunning Fog comparison |
| `citation_density.png` | `output/figures/` | Citations per 1000 words by section |
| `manuscript_variables.json` | `output/data/` | `{ "TOKEN": "value" }` mapping for all eleven tokens |
| `*.md` (substituted) | `output/manuscript/` | Manuscript section files with `{{TOKEN}}` resolved |

**Critical**: every `{{TOKEN}}` referenced in `manuscript/*.md` must resolve
to a non-empty string before Phase 3. Unresolved tokens render literally.

### Phase 3 — Render PDF

**Script**: `scripts/pipeline/stage_03_render.py` (at repository root, **not** inside
`projects/`).

**Command**:
```bash
uv run python scripts/pipeline/stage_03_render.py --project template_prose_project
```

**Inputs**: `output/manuscript/*.md` (substituted) + `manuscript/config.yaml`
+ `manuscript/preamble.md` + `manuscript/references.bib`.

**Infrastructure modules involved**:

| Module | Role |
|---|---|
| `infrastructure/rendering/pdf_renderer.py` | Orchestrates Pandoc → XeLaTeX pipeline |
| `infrastructure/rendering/_pdf_latex_helpers.py` | LaTeX package validation and preamble injection |
| `infrastructure/rendering/manuscript_discovery.py` | Discovers and orders manuscript section files |
| `infrastructure/core/config/loader.py` | Reads `manuscript/config.yaml` for title, authors, metadata |

**Outputs**:
- `projects/templates/template_prose_project/output/pdf/template_prose_project_combined.pdf`
  — final publication PDF (working copy).
- `projects/templates/template_prose_project/output/pdf/_combined_manuscript.*` — LaTeX intermediates
  (`.tex`, `.aux`, `.log`).
- `projects/templates/template_prose_project/output/slides/` — per-section Beamer slide
  PDFs.
- `projects/templates/template_prose_project/output/web/` — HTML versions of each section.

### Phase 4 — Copy Final Deliverables

**Script**: `scripts/pipeline/stage_05_copy.py` (at repository root).

**Command**:
```bash
uv run python scripts/pipeline/stage_05_copy.py --project template_prose_project
```

**Output**: Final PDF and figures copied to
`output/template_prose_project/` at the repository root (used by CI artifact
upload and by the multi-project executive report).

## `config.yaml` Controls

Every knob lives in `projects/templates/template_prose_project/manuscript/config.yaml`:

| YAML Key | Controls | Consumed by |
|---|---|---|
| `paper.title` | PDF title page, page headers, `{{CONFIG_TITLE}}` token | `pdf_renderer.py`, `manuscript_variables.py` |
| `authors[*]` | Author list on title page | `pdf_renderer.py` |
| `publication.doi` | DOI on title page | `pdf_renderer.py` |
| `prose.target_grade_level_min` / `_max` | FKGL band for `grade_level_in_band` check | `_check_grade_level` in `src/pipeline/checks.py` |
| `prose.long_sentence_threshold` | Word count above which sentences are flagged | `infrastructure.prose.analyze_quality` (via `analyze_manuscript`) |
| `prose.citation_density_min_per_1000` | Floor for `citation_density_above_floor` check | `_check_citation_density` in `src/pipeline/checks.py` |
| `prose.require_h1_per_section` | Toggle `every_file_has_h1` check | `_check_h1_per_file` in `src/pipeline/checks.py` |
| `prose.forbid_skipped_levels` | Toggle `no_skipped_heading_levels` check | `_check_no_skipped_levels` in `src/pipeline/checks.py` |
| `bibliography.references_path` | Path to BibTeX file | `parse_bibfile` in `src/pipeline/checks.py` |
| `bibliography.fail_on_missing` | Fail if a `[@key]` is not in the bib | `_check_bibliography` in `src/pipeline/checks.py` |
| `bibliography.fail_on_unused` | Fail if a bib entry is never cited | `_check_bibliography` in `src/pipeline/checks.py` |

## Troubleshooting

### Unresolved `{{TOKEN}}` appears in PDF

**Symptom**: The rendered PDF contains a literal `{{TOKEN_NAME}}` string.

**Cause**: Phase 2 did not run, failed silently, or the token is not defined
in `src/manuscript_variables.py::ManuscriptVariables`.

**Fix**:
```bash
# Confirm the JSON exists
ls projects/templates/template_prose_project/output/data/manuscript_variables.json

# Re-run Phase 2
uv run python projects/templates/template_prose_project/scripts/z_generate_manuscript_variables.py

# Detect remaining unresolved tokens
grep -r "{{" projects/templates/template_prose_project/output/manuscript/ | grep -v ".json"
```

### BibTeX citation error / PDF fails to compile

**Symptom**: XeLaTeX exits with a BibTeX error or undefined citation key.

**Cause**: Either a malformed entry in `manuscript/references.bib`
(unclosed braces, duplicate keys, missing required fields) or a `[@key]`
reference in the prose with no matching entry.

**Fix**: Run the bibliography validator first:
```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_prose_project/manuscript/references.bib --strict
```

If `bibliography_consistency` failed in Phase 1, `output/checks.json`
will list missing keys under `details.missing` — add them to
`manuscript/references.bib` (this project never auto-populates the bib;
manual curation is intentional).

### FKGL out of band

**Symptom**: `grade_level_in_band` failed in `output/checks.json`.

**Cause**: The weighted Flesch-Kincaid Grade Level falls outside
`[prose.target_grade_level_min, prose.target_grade_level_max]`.

**Fix**:
1. **Too high (dense prose)**: shorten sentences, replace polysyllabic
   words with simpler synonyms, split paragraphs.
2. **Too low (over-simple)**: verify `manuscript/` contains the actual
   prose, not placeholder text.
3. Or widen the band in `manuscript/config.yaml`.

See [`troubleshooting.md`](troubleshooting.md) for the diagnostic flowchart.

### Matplotlib backend error during Phase 2

**Symptom**: `y_generate_prose_figures.py` fails with a Tk/Qt backend error.

**Cause**: The shell environment is overriding the `MPLBACKEND` variable
that `src/figures.py` sets at import time.

**Fix**:
```bash
unset MPLBACKEND
uv run python projects/templates/template_prose_project/scripts/y_generate_prose_figures.py
```

`tests/conftest.py` pins `MPLBACKEND=Agg` for the test suite; the figure
script does the same at import time of `src/figures.py`.

### Phase 2 runs before Phase 1

**Symptom**: `y_generate_prose_figures.py` exits with code 2 and a message
that `manuscript_report.json` is missing.

**Cause**: Phase 2 has no input until Phase 1 has produced
`output/manuscript_report.json`.

**Fix**: Run `scripts/run_prose_pipeline.py` first. The full ordered run is
documented in [`quickstart.md`](quickstart.md).
