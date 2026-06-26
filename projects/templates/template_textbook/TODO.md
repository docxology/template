# template_textbook TODO

Forward-only integrity backlog for the modular fillable textbook scaffold.
Keep this focused on book-scale structure, configurability, and validation.

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_textbook/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_textbook/tests/ --cov=projects/templates/template_textbook/src --cov-fail-under=90`
- Structural integrity is driven by `manuscript/config.yaml`, chapter stubs, figure generation, and manuscript-integrity tests.
- Repo drift gate: `uv run python scripts/check_template_drift.py --strict`
- Stage 04 warning snapshot, 2026-06-20: generated figure registry passes; evidence registry still reports 123 unsupported pedagogical numbers; artifact manifest reports advisory drift after single-stage regeneration.
- 2026-06-25 coverage snapshot: 158 tests, 99.25% coverage. All of `textbook/`, `visualization/`, `mermaid/`, and utility modules covered. Remaining uncovered lines are all `# pragma: no cover` optional-dependency paths (Pillow, mmdc) or unreachable error-cleanup branches.

## Integrity and template-status gaps

- Keep `manuscript/config.yaml` as the only source of truth for parts, chapters, appendices, labs, and question banks.
- Add a generated scaffold audit that reports missing stubs, disabled chapters, orphan files, and stale figure references.
- Keep finished chapters clearly separated from fillable stubs.

## Configurable-surface gaps

- Keep `manuscript/config.yaml.example` small enough to copy while preserving required book, render, units, and appendix schema.
- Add migration tests if `units:` or appendix keys change.

## Documentation and signposting gaps

- Keep README, AGENTS, and manuscript docs clear about worked exemplars versus stubs.
- Link any new structural config keys from the README, AGENTS, and visualization guide.

## Test and validator gaps (current status 2026-06-25)

✅ Edge cases for `_rotate` with empty items (line 34 in content.py)
✅ `validate_chapter` figure-path validation (line 254 in content.py)
✅ `validate_config` for empty/null chapter lists (lines 120-121 in config.py)
✅ `validate_config` duplicate chapter file detection
✅ `discover_template_root` via env var (lines 49-51 in textbook_paths.py)
✅ `discover_template_root` when start is a file (line 55 in textbook_paths.py)
✅ `ensure_project_paths` inserts SRC when absent (line 24 in textbook_paths.py)
✅ `ensure_project_paths` inserts root when absent (line 30 in textbook_paths.py)
✅ `cover_art` without subtitle (branch miss in plots.py line 153)
✅ `_figure_filename` fallback to basename (line 52 in registry.py)
✅ `_figure_filename` output/figures path extraction
✅ Mermaid builder edge cases: empty sequences, no-label transitions, flat mindmap branches, empty gantt/pie/timeline/journey/quadrant
✅ All Mermaid spec names are unique (regression guard)
✅ `load_specs` with custom YAML path
✅ TOC uniqueness across all chapters (regression guard)
✅ `build_toc` skips disabled chapters
✅ `TocEntry` fields populated correctly
✅ Models: logistic growth at N₀=K, scalar t, Hill at x=0, zero decay rate, predict on array, single-value descriptive stats, single-element normalize
✅ Logging: WARNING and ERROR levels
✅ `pad_png_to_square` no-Pillow path (via builtins.__import__ monkeypatch)
✅ `write_text_atomic` no-leftover-tmp guarantee

Remaining known uncovered paths (all intentional):
- `mermaid/renderer.py` lines 43-44, 57: mmdc subprocess path (`# pragma: no cover`)
- `textbook_visuals.py` lines 20-31 (deep Pillow path): `# pragma: no cover`
- `textbook_io.py` line 38: `os.unlink(tmp_name)` when rename raises (rare OS error path)
- `textbook_paths.py` line 51→56: branch when template root is already on sys.path

- Add negative controls for orphan chapter files, missing labs/questions, stale Mermaid diagrams, and unresolved stub markers in finished chapters.
- Add deterministic checks for generated cover art and diagrams when visual styles change.
- Register textbook worked-example numbers, percentages, and appendix-gallery constants as configured facts, or mark them as documentation-only examples, before treating Stage 04 as warning-free.
- Add or document a stable final artifact-manifest refresh path for single-stage analysis/render/copy checks.
- The 2026-06-21 ast-grep audit found the intentional Mermaid `subprocess.run`
  renderer boundary; future hardening should keep a single timeout/cwd/error
  policy for optional external diagram tools and document the fallback path.

## Ordered improvement ladder

1. Keep scaffold, figure, diagram, and manuscript-integrity tests green.
2. Add structured scaffold audit output and stale-file detection.
3. Add copy-and-customize examples for short course notes and full textbook shapes.
4. Promote a filled textbook fork only after unresolved stub markers and placeholder chapters are blocked by validation.
