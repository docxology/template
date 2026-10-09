# Reporting Package

## Purpose

Reporting converts pipeline, test, validation, evidence, and release-readiness
facts into human and machine-readable artifacts. Reports should summarize real
local evidence; they must not present missing, stale, or optional network state
as verified success.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Pipeline reports | `pipeline_report_model.py`, `pipeline_io.py`, `pipeline_markdown.py`, `pipeline_html.py` | Structured per-run stage reports; validation JSON and Markdown share one `SOURCE_DATE_EPOCH`-aware timestamp. |
| Multi-project summaries | `multi_project_reporter.py`, `multi_project_report.py` | Original expected selections and matching typed outcomes drive terminal and runtime summaries; aggregate artifacts stay in ignored `output/multi_project_summary/`. |
| Executive reports | `executive_reporter.py`, `_executive_*`, `_dashboard_*`, `_csv_*` | Dashboard, CSV, HTML, image, and markdown report generation. |
| Evidence/release | `evidence_graph.py`, `release_readiness.py` | Local evidence graph and no-network release-readiness dashboard. `evidence_graph.py` graphs this repo's own `pipeline.yaml` stage DAG (producer/consumer/validator/artifact/claim) — a structurally-similar-but-different-domain analog to `projects/templates/template_literature_meta_analysis/src/reproducibility/`'s paper-content workflow graphs; cross-reference only, the two are not merged. |
| Error/test helpers | `error_aggregator.py`, `suite_runner.py`, `pipeline_test_runner.py`, `project_verifier.py`, `pytest_output_parser.py` | Test orchestration and failure aggregation. `project_verifier.py` owns the nonce-bound receipt, confined argv, timeout, real-count, and independent coverage contract for explicitly declared single-project verifiers. |
| Coverage parsing | `coverage_json_parser.py` | `parse_coverage_json` reads pytest-cov `coverage.json` into per-file and overall coverage stats. |
| Coverage analysis | `coverage_analysis.py` | `format_coverage_status`, `analyze_coverage_gaps`, and `format_failure_suggestions` render coverage against thresholds and derive gap and failure hints. |
| Test summary builder | `report_builder.py` | `discover_active_projects` returns `ProjectInfo.qualified_name` (so `templates/<name>` does not collide with a flat sibling) and `generate_summary_report` aggregates infrastructure and project suite results into one weighted summary structure. |
| Test result loaders | `result_loaders.py` | `load_test_results` and `load_infrastructure_results` read runner JSON into the `InfraResults` shape. |
| Stage 01 reporting | `pipeline_test_reporting.py` | `report_results` and `report_infra_only_results` log the Stage 01 test-execution summary in human-readable form. |
| Executive output layout | `executive_outputs.py` | `organize_executive_summary` and `ExecutiveOutputOptions` sort `output/executive_summary` files by type via `OutputOrganizer`. |
| HTML templates | `html_templates.py` | `shared_css`, `get_base_html_template`, `render_summary_cards`, and `render_table` supply the shared design-token/dark-mode CSS and reusable report HTML. |
| Log summaries | `log_analysis.py` | `generate_log_summary` tallies log-level counts and error/warning samples into a human-readable log report. |
| Run lessons | `run_lessons.py` | `collect_run_lessons` and `write_run_lessons` capture per-run pipeline lessons (`RunLesson`) to JSONL, Markdown, and next-run context files. |
| Interactive dashboards | `interactive_dashboard.py`, `_interactive_models.py`, `_interactive_html.py` | `InteractiveDashboard` builder API, the `Panel`/`Control`/`Invariant` data types, and page assembly for self-contained Plotly dashboards. See [Interactive simulation dashboard](#interactive-simulation-dashboard-interactive_dashboardpy). |
| Output organization | `output_organizer.py`, `output_statistics.py`, `page_grid.py`, `page_rendering.py` | Final report file layout and page grids. `output_statistics.py` consumes the artifact layer's complete stable inventory rather than raw disk state. Public exemplars use `stable-shippable-output-v1`; explicitly resolved non-template projects may use `stable-local-output-v1`. Dynamic categories and root bundles are retained; Stage 5 declares `stage5-delivery-mirror` scope and writes byte-identical source/copy receipts. |

## Interactive simulation dashboard (`interactive_dashboard.py`)

Project-agnostic builder for a single self-contained HTML page with Plotly
panels, live controls, invariants, and reproducibility metadata. The package is
split three ways: `_interactive_models.py` holds the `Panel`, `Control`, and
`Invariant` dataclasses; `_interactive_html.py` assembles the page
(`render_interactive_dashboard_html`, `PLOTLY_CDN`); `interactive_dashboard.py`
exposes the `InteractiveDashboard` builder API.

- Construct with `InteractiveDashboard(title, subtitle, project_name, repo_root)`.
- Feed data with `set_payload`, `set_hyperparameters`, `set_meta`, `add_table`,
  `add_note`; the chained setters return `self`.
- Add views with `add_panel(Panel(...))` and controls with `add_slider`,
  `add_dropdown`, `add_toggle`, or the generic `add_control`.
- Declare checks with `add_invariant(Invariant(name, actual, expected, tol))`;
  `evaluate_invariants()` scores them and `render_invariants_text()` /
  `render_summary_text()` render the plaintext companions.
- `write(html_path, json_path=None, txt_path=None, invariants_path=None)`
  writes the artefacts and returns a dict of artefact name → resolved `Path`.

Boundaries: the builder does not run a simulation — callers pass in already
computed payloads. Invariant results are recorded as evaluated, never forced to
pass. The page embeds its own payload plus git revision and dirty state, so the
HTML stays self-contained and the run is traceable.

## Boundaries

- Reports consume existing artifacts; they do not run project analysis.
- Local readiness is not publication readiness. Network deposits, DOI state, and
  public endpoints need explicit publishing checks.
- Avoid hard-coded project rosters; use public scope helpers or generated docs.
- Keep charts deterministic and compact. Put metric definitions in source data
  or report prose, not hidden code comments.
- When a report quotes counts or coverage, cite generated facts or fresh command
  output.

## Public Commands

```bash
uv run python -m infrastructure.reporting.evidence_graph build templates/template_code_project --json /tmp/evidence_graph.json
uv run python -m infrastructure.reporting.release_readiness --repo-root . --out output/release_readiness.md
uv run python scripts/runner/execute_multi_project.py --mode core --run-timeout 14400
```

The multi-project CLI uses local discovery, including deliberately configured
private active projects. Its reports are local runtime artifacts. Use the public
acceptance matrix commands in `RELEASE_READINESS.md` for the canonical public roster.

## Tests

```bash
uv run pytest tests/infra_tests/reporting -q
```

The streaming test runner includes source admission, guardian READY/ARM, child execution and mandatory cleanup in one original finite deadline. The shared startup phase allowance defaults to 60 seconds and cannot extend that deadline. Source-admission/READY timeouts return 124 before launch; ARM failures clean already launched children and preserve observed interruption. Successful child exit cannot authorize success after cleanup exhausts the deadline.

For changes that touch project test execution, also run the relevant
`scripts/pipeline/stage_01_test.py` mode because `pipeline_test_runner.py` controls the
project output lock used by pipeline stages.

The ordinary project path remains the generic pytest runner. A project may
opt into a stateful/chunked command with
`[tool.template].project_test_command`; the single-project lane accepts it only
when `project_verifier.py` validates a fresh run-bound receipt and independently
regenerates the project's CI-uploadable `coverage_project.json` from a new
coverage database at or above the unchanged project floor. The verifier uses the existing selected interpreter after an actual bounded
probe validates the workspace's exact runner dependency versions, and the receipt carries
real JUnit outcomes plus pytest-produced discovery and warning counts; absent
project-local coverage never falls back to a repository-level file from another
run. The all-project union runner uses the same independent admission for
source-declared verifiers and preserves their exact validated database bytes
through coverage combination and receipt finalization. Declared verifier lanes
run serially after the ordinary matrix under the existing 6,900-second verifier
budget. Their receipt records the source-owned command and actual concurrency;
generic pytest markers and xdist selections apply to ordinary lanes.

## Change Checklist

- Add tests for JSON/Markdown/HTML shape when public report schema changes.
- Keep release-readiness aggregation offline unless a command explicitly says it
  performs network validation.
- Regenerate downstream report fixtures only through their producer commands.
- Run `git diff --check`; report markdown tables are easy to break with trailing
  whitespace.

## See Also

- [`README.md`](README.md)
- [`../core/pipeline/AGENTS.md`](../core/pipeline/AGENTS.md)
- [`../validation/AGENTS.md`](../validation/AGENTS.md)

Candidate and published acceptance use the full source-owned public roster; see
[`RELEASE_READINESS.md`](RELEASE_READINESS.md) for required evidence and custody.

### Optional plotting imports

Package imports for pipeline reports, statistics, errors and the interactive
dashboard do not initialize Matplotlib. Requesting `DASHBOARD_AVAILABLE`, an
optional plotting export, or explicit package enumeration loads the original
plotting providers once. Their function identities and import-failure behavior
remain unchanged; the package retains its declared public exports. Import
observations alone do not establish complete execution or a universal speedup.

## Release acceptance modules

| Module | Role |
| --- | --- |
| `native_dependency_preparation.py` | Finite official npm asset preparation, bound to exact source lock integrity. |
| `native_epub_observer.py` | Real EPUBCheck and native reader conversion with exact byte custody. |
| `native_epub_preparation.py` | Prepare the pinned official EPUBCheck bundle in a fresh owned directory. |
| `native_epub_replay.py` | Portable replay of retained EPUB validator and reader execution custody. |
| `native_format_acceptance.py` | Supervised fresh native rendering; incomplete visual acceptance stays blocked. |
| `native_format_acceptance_checks.py` | Strict native byte parsers and actual bounded PDF tool observations. |
| `native_format_acceptance_contracts.py` | Source-owned native artifact obligations, separate from existing-file discovery. |
| `native_format_acceptance_validation.py` | Independent native conformance reconstruction and full-acceptance refusal. |
| `native_format_acceptance_worker.py` | Fresh core execution and native observers for one admitted public project. |
| `native_format_browser_assets.py` | Confined source-owned HTML/CSS and declared MathJax dependency closure. |
| `native_format_browser_cdn.py` | Lock-integrity-authenticated offline responses for exact reviewed CDN URLs. |
| `native_format_browser_driver.py` | Finite loopback-only Chromium DevTools driver using the standard library. |
| `native_format_browser_figures.py` | Independent decoded source image and rendered image-region observations. |
| `native_format_browser_oracles.py` | Real isolated Chromium DOM, reflow and screenshot observations. |
| `native_format_browser_replay.py` | Independent portable browser source, DOM, pixel and supervised control replay. |
| `native_format_browser_runtime.py` | Bounded complete installed browser application byte inventory, standard library only. |
| `native_format_browser_semantic_controls.py` | Real supervised math, citation and source-figure native browser controls. |
| `native_format_browser_semantic_replay.py` | Independent source/producer/DOM/pixel replay of scientific browser controls. |
| `native_format_content_contracts.py` | Bounded, explicit text obligations from the exact consumed manuscript bytes. |
| `native_format_control_replay.py` | Independent source-owned control replay retaining original supervised exits. |
| `native_format_math_anchors.py` | Exact source prose anchors for independently observed mathematical occurrences. |
| `native_format_observer_dispatch.py` | Actual native observer dispatch; unsupported source projections stay blocked. |
| `native_format_observer_outcome.py` | Preserve all native source findings and unsupported obligations at admission. |
| `native_format_observer_projection_replay.py` | Independent source-bound projected pages and EPUB native layout replay. |
| `native_format_observer_source_replay.py` | Independent current-reader semantic source and Office conversion replay. |
| `native_format_observer_validation.py` | Portable native observer replay entry points; producer paths remain labels. |
| `native_format_pdf_math.py` | Independent source algebra and anchored native PDF equation observations. |
| `native_format_pdf_oracles.py` | Actual PDF text, glyph geometry and localized raster observations. |
| `native_format_pdf_positions.py` | Zero-glyph source math positions from the actual XeTeX shipout engine. |
| `native_format_pdf_projection.py` | Fresh source-only canonical PDF TeX projection, before native compilation. |
| `native_format_pdf_reference_parity.py` | Every-page glyph, vector and pixel parity for an admitted source reference. |
| `native_format_pdf_source.py` | Source-only PDF manuscript reconstruction and real pre-citeproc AST custody. |
| `native_format_pdf_whole_reference.py` | Callable bounded complete-source PDF reference and zero-glyph math custody. |
| `native_format_portable_custody.py` | Portable original observations; receipt hashes do not authenticate origin. |
| `native_format_portable_source.py` | Reconstruct original source labels while admitting current source bytes. |
| `native_format_scientific_math.py` | Source-engine mathematical references and native glyph/shape comparisons. |
| `native_format_semantic_source.py` | Actual bounded source parsing for independent HTML semantic obligations. |
| `native_format_tex_reference.py` | Bounded actual XeTeX references with explicit backend and dependency custody. |
| `native_newspaper_source.py` | Configured newspaper print checks against source and actual native rasters. |
| `native_office_observer.py` | Bounded native Office conversion; package parsing never grants layout acceptance. |
| `native_office_reference.py` | Source-only Office references with unresolved scientific coverage retained. |
| `native_office_reference_visual.py` | Full native Office page comparison, subordinate to independent source coverage. |
| `native_office_semantic_source.py` | Source-owned combined manuscript reconstruction for native DOCX and EPUB. |
| `native_office_source_coverage.py` | Independent scientific occurrence accounting; inventory alone never admits layout. |
| `native_office_table_coverage.py` | Independent table-cell accounting without granting native layout admission. |
| `native_pdf_citation_replay.py` | Current-reader citation regeneration and exact native glyph/ink observations. |
| `native_pdf_citation_runtime.py` | Finite real citation tools and observed TeX dependency custody. |
| `native_pdf_citations.py` | Independent source-only natbib/plainnat citation references for scientific PDFs. |
| `native_pdf_cmap_bounds.py` | Bound actual CMap range expansion before native font-map construction. |
| `native_pdf_index_bounds.py` | Admit exact classic or compressed PDF indexes before native decoding. |
| `native_pdf_stream_bounds.py` | Bounded indexed-PDF admission before unbounded native stream parsing. |
| `native_pdf_stream_decode.py` | Finite supported PDF stream decoders used before native page parsing. |
| `native_print_font_custody.py` | Observe actual print font resources without redistributing installed fonts. |
| `native_print_witness.py` | Original Darwin print witnesses with complete source, font and decoder custody. |
| `native_print_witness_validation.py` | Independent portable print witness admission without producer font access. |
| `native_projection_checks.py` | Actual per-page projected glyph checks, retaining unsupported visual gates. |
| `native_projection_contracts.py` | Ordered deck obligations compiled from a source-reconstructed deck model. |
| `native_qr_runtime.py` | Observe the actual linked QR core; portable receipts retain hashes, never binaries. |
| `native_scientific_reference_replay.py` | Independent portable reconstruction of retained source-only TeX references. |
| `native_scientific_reference_reproduction.py` | Fresh reader-local source compilation; original XDV never substitutes for ink. |
| `native_storybook_source.py` | Source-bound raster storybook checks; producer summaries are never evidence. |
| `readiness_receipts.py` | Source-bound acceptance profiles; receipts do not establish execution provenance. |
| `release_readiness_artifacts.py` | Native archive structure and exact public source/export parity. |
| `release_readiness_collectors.py` | Informational local snapshots; acceptance authority comes from the required profile. |
| `release_readiness_dependencies.py` | Bind runtime acceptance to current declared installed public providers. |
| `release_readiness_pipeline.py` | Validate fresh completion against the actual source-owned execution plan. |
| `release_readiness_profile.py` | Source-owned platform candidate and release acceptance requirements. |
| `release_readiness_root_cases.py` | Source-owned Root v2 case cells and original selected-interpreter acceptance. |
| `release_readiness_runtime.py` | Independently validate complete source/spec/process-bound public pytest cells. |
| `release_readiness_snapshot.py` | Confined one-read snapshots shared by facts and their receipt hashes. |
| `release_readiness_types.py` | Typed fail-closed sections for local release readiness. |
| `release_readiness_validators.py` | Kind-specific acceptance oracles; structural receipts alone cannot pass. |
| `required_acceptance_aggregate.py` | Combine original required evidence; publish only independently passed candidates. |
