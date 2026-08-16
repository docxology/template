# infrastructure/validation/output/ - Output Validation Documentation

## Purpose

The `infrastructure/validation/output/` package contains pipeline output validation and no-mock enforcement helpers.

## Files

- `validator.py` - output structure validation (`validate_copied_outputs`, `validate_output_structure`, ...); all provenance-bound counts, sizes, and largest-file fields derive from `collect_stable_output_inventory()`. Public exemplars declare `stable-shippable-output-v1`; explicitly resolved non-template projects may declare `stable-local-output-v1`. Both exclude runtime/build/control and hidden-path residue. Dynamic categories and root bundles are retained, and Stage 5 reuses an inventory mapped to the canonical source-output context rather than scanning the ignored mirror directly.
- `pipeline.py` - Stage 4 orchestration facade (`validate_pdfs`, `validate_manuscript_output_markdown`, `execute_validation_pipeline`)
- `render_formats.py` - shared Stage 4/5 effective-format loading, exact canonical deliverable validation, disabled-output rejection, and copied-tree filtering
- `pdf_checks.py` - PDF structure and transmission bookend checks
- `markdown_checks.py` - manuscript markdown wrapper and diagnostic report handling
- `design.py` - domain profile, experiment plan, and AutoResearch overlay validation
- `artifacts.py` - strict shared artifact-manifest JSON parsing and lifecycle-mode-aware current-manifest selection; legacy missing mode means strict shippable, but loose/coerced entry fields are invalid
- `prose_quality.py` - opt-in, report-only AI-writing prose quality gate
- `claim_verification.py` - optional web-grounded claim verification report for manuscript prose
- `no_mock_enforcer.py` - AST/token lexical mock-framework scan plus classified monkeypatch stand-in inventory
- `no_mock_audit.py` - shared repository CLI/report/exit semantics used by both script wrappers
- `layout.py` - shared output directory layout constants (`OUTPUT_SUBDIR_NAMES`, `OPTIONAL_OUTPUT_SUBDIRS`)

## Key APIs

### `pipeline.py`

- `validate_manuscript_output_markdown(project_name)` — pipeline wrapper; resolves `projects/{name}/manuscript/` and calls content `validate_markdown()`. **Not** the same symbol as content `validate_markdown(dir, repo_root)`.
- `validate_pdfs(project_name)` — PDF validation for project output dir
- `execute_validation_pipeline(project_name)` — runs PDF + markdown checks for Stage 4
- `validate_claim_verification(project_root)` — optional report-only web claim verification over manuscript Markdown

### `render_formats.py`

- `load_effective_rendering_config(project_root)` — loads the same
  environment-over-YAML format configuration used by rendering
- `validate_enabled_render_outputs(...)` — validates every enabled canonical
  PDF, HTML, slide, DOCX, or EPUB artifact and rejects renderer-owned artifacts
  for disabled formats; an enabled file must also belong to the stable,
  shippable inventory, so a valid but Git-ignored artifact cannot pass
- `remove_disabled_render_outputs(...)` — removes disabled renderer-owned
  artifacts only from Stage 5's freshly copied tree; it does not mutate project
  source outputs or unrelated authored web pages

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../content/discovery.py`](../content/discovery.py) — manuscript markdown enumeration (`scope="tree"`)
