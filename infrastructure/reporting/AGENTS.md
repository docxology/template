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
| Executive reports | `_executive_models.py`, `_executive_collectors.py`, `_executive_analysis.py`, `_executive_health.py`, `_executive_renderers.py`, `_executive_report_formats.py`, `_dashboard_*`, `_csv_*` | Metrics, summaries, dashboard, CSV, HTML, image, and markdown report generation. |
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
| `native_analysis_boundary_replay.py` | Reconstruct retained analysis boundaries under genuine native custody. |
| `native_analysis_read_replay.py` | Reconstruct every authenticated actual read/write event from held Source bytes. |
| `native_analysis_semantic_compare.py` | Compare complete authenticated analysis graphs across physical executions. |
| `native_analysis_stage_replay.py` | Bind an analysis leaf to the one genuinely authenticated fixed stage chain. |
| `native_analysis_write_replay.py` | Reconstruct completed Source writes and exact returned-read temporal edges. |
| `native_authenticated_original_launch.py` | Compose original native launches only from the genuine hosted collector. |
| `native_authenticated_original_pdfium.py` | Authenticated hosted original PDFium inputs, distinct from live execution. |
| `native_citation_process_custody.py` | Live original CitationRuntime facts, separate from transported process DATA. |
| `native_code_consumed_value_join.py` | Selected finite Code scalar meanings from genuine Original/Current graphs. |
| `native_code_contextual_compare.py` | Equality-only Code projection after both genuine complete per-run joins. |
| `native_code_figure_domains.py` | Independent finite plotted meanings for six selected Code PNG roles. |
| `native_code_figure_lineage.py` | One per-scope join of actual Code plot writes to selected Source assets. |
| `native_code_figure_registry.py` | Independent complete Code exemplar registry reconstruction from held Source. |
| `native_code_metadata_domains.py` | Per-run integrity of the eight Source-selected Code metadata roles. |
| `native_code_native_endpoints.py` | Selected Code endpoints in existing complete own-format native witnesses. |
| `native_code_native_locations.py` | One real own-format ordinal capture per selected Code artifact/phase. |
| `native_code_runtime.py` | Exact CPython executable-code compatibility, separate from host identity. |
| `native_code_scalar_domains.py` | Finite Code token meanings from checked CSV math and authored config DATA. |
| `native_code_stability_domain.py` | Selected Code SDK objective-stability meanings under the existing join. |
| `native_code_value_consumption.py` | Fixed Code numeric DATA reconstruction under genuine held Source custody. |
| `native_code_value_predicate.py` | Independent scalar quadratic facts, never native or Original authority. |
| `native_crossref_archive.py` | Actual Source-pinned official Crossref archive/executable correspondence. |
| `native_crossref_closure.py` | One fixed crossref SDK role; serialized records cannot select another role. |
| `native_crossref_exit.py` | Observe an authenticated live Darwin filter's kernel exit status before replay. |
| `native_crossref_exit_dispatch.py` | Fixed Source-owned original-host roles for Linux and Darwin exit status. |
| `native_crossref_filter.py` | Source-owned live Pandoc/filter handshake; portable records remain DATA. |
| `native_crossref_linux_abi.py` | Fixed Linux 6.15 pidfd_info ABI and original-platform DATA decoding. |
| `native_crossref_linux_exit.py` | Genuine original Source custody of a live Linux filter's held pidfd status. |
| `native_crossref_pair.py` | Exactly two real filter children behind one immutable Source-selected launcher. |
| `native_crossref_pandoc.py` | Actual original/current Pandoc adapters for a Source-selected crossref child. |
| `native_crossref_protocol.py` | Finite kernel-identified filter IPC; messages never nominate a process PID. |
| `native_crossref_replay.py` | Typed portable replay of a genuine externally held Pandoc filter child. |
| `native_crossref_worker.py` | Actual Source-audited Pandoc filter child; stdout contains only filter JSON. |
| `native_current_artifact_join.py` | Observe the actual artifacts of the already executed fresh Current Core. |
| `native_current_epub_engine_data.py` | Retain the one selected EPUBCheck bundle in the separate Current root. |
| `native_current_reader_inputs.py` | Immutable Current execution nominations held by the actual native reader. |
| `native_dependency_preparation.py` | Finite official npm asset preparation, bound to exact source lock integrity. |
| `native_environment_custody.py` | Exact selected, bounded and audited Popen environment commitments. |
| `native_epub_observer.py` | Real EPUBCheck and native reader conversion with exact byte custody. |
| `native_epub_preparation.py` | Prepare the pinned official EPUBCheck bundle in a fresh owned directory. |
| `native_epub_replay.py` | Portable replay of retained EPUB validator and reader execution custody. |
| `native_epub_source_spine.py` | Ordered EPUB reference parity subordinate to independent source survival. |
| `native_failed_transport.py` | Bounded preservation of failed cold-launch evidence, without acceptance. |
| `native_format_acceptance.py` | Supervised fresh native rendering; incomplete visual acceptance stays blocked. |
| `native_format_acceptance_checks.py` | Strict native byte parsers and actual bounded PDF tool observations. |
| `native_format_acceptance_contracts.py` | Source-owned native artifact obligations, separate from existing-file discovery. |
| `native_format_acceptance_control_validation.py` | Existing exact parser, PDF and Source-selected native control replay. |
| `native_format_acceptance_results.py` | Final source identities and preservation of actual native failure outcomes. |
| `native_format_acceptance_validation.py` | Independent native conformance reconstruction and full-acceptance refusal. |
| `native_format_acceptance_worker.py` | Fresh core execution and native observers for one admitted public project. |
| `native_format_browser_assets.py` | Confined source-owned HTML/CSS and declared MathJax dependency closure. |
| `native_format_browser_cdn.py` | Lock-integrity-authenticated offline responses for exact reviewed CDN URLs. |
| `native_format_browser_child.py` | Fixed basic/semantic browser children with genuine Source and native custody. |
| `native_format_browser_driver.py` | Finite loopback-only Chromium DevTools driver using the standard library. |
| `native_format_browser_figures.py` | Independent decoded source image and rendered image-region observations. |
| `native_format_browser_oracles.py` | Real isolated Chromium DOM, reflow and screenshot observations. |
| `native_format_browser_replay.py` | Independent portable browser source, DOM, pixel and supervised control replay. |
| `native_format_browser_runtime.py` | Bounded complete installed browser application byte inventory, standard library only. |
| `native_format_browser_semantic_controls.py` | Real supervised math, citation and source-figure native browser controls. |
| `native_format_browser_semantic_replay.py` | Independent source/producer/DOM/pixel replay of scientific browser controls. |
| `native_format_browser_structure.py` | Independent source-cell and source-note browser layout reconstruction. |
| `native_format_content_contracts.py` | Bounded, explicit text obligations from the exact consumed manuscript bytes. |
| `native_format_control_replay.py` | Independent source-owned control replay retaining original supervised exits. |
| `native_format_current_orchestration.py` | Serial Current-root custody through existing Source/Git/SDK owner factories. |
| `native_format_current_pandoc.py` | Fresh Source-owned Pandoc reader scope; transported receipts select no tools. |
| `native_format_html_admitted_source.py` | HTML source witnesses subordinate to original immutable source admission. |
| `native_format_html_browser_extensions.py` | Exact source-owned observer extensions for finite HTML fidelity evidence. |
| `native_format_html_child_custody.py` | Live parent admission of copied standalone HTML Python source execution. |
| `native_format_html_column_allocation.py` | Independent original-column allocation for a finite CSS fixed-table form. |
| `native_format_html_contextual_request.py` | Source-derived styled text segments for genuine physical font/shaper probes. |
| `native_format_html_darwin_image_custody.py` | Observe actual loaded Darwin framework code without inventing absent files. |
| `native_format_html_fidelity_components.py` | Observer/portable-reader adapters for original HTML fidelity components. |
| `native_format_html_fidelity_observer.py` | Actual HTML fidelity producer and independent portable component hooks. |
| `native_format_html_font_driver_adapter.py` | Exact source-helper byte binding for copied standalone browser drivers. |
| `native_format_html_font_provider.py` | Source-owned finite platform font providers, reconstructed by each reader. |
| `native_format_html_font_witness.py` | Current-reader font bytes and full contours from a genuine local probe. |
| `native_format_html_glyph_contours.py` | Original character occurrences and independent admitted-font glyph contours. |
| `native_format_html_glyph_reference.py` | Source-only glyph scenes and complete independently rendered ink comparison. |
| `native_format_html_image_alt.py` | Occurrence-complete original image alternatives and observed native alt. |
| `native_format_html_integer_resampling.py` | Source-only exact nearest-neighbor kernel at integral pixelated placement. |
| `native_format_html_linux_font_probe.py` | Actual Linux Fontconfig face resolution and FreeType Unicode glyph mapping. |
| `native_format_html_local_paint.py` | Localized native character, math-leaf and complete unit-image paint checks. |
| `native_format_html_metadata.py` | Config byte custody and literal HTML metadata placement witnesses. |
| `native_format_html_platform_font_dom.py` | Actual CDP platform-font usage, without candidate DOM mutation. |
| `native_format_html_platform_font_probe.py` | Actual Darwin/Linux font-file resolution and source-codepoint glyph observations. |
| `native_format_html_reference_runtime.py` | Fresh source-only glyph native launches and portable byte/command custody. |
| `native_format_html_resampling_witness.py` | Conditional source-declared figure kernel without candidate-derived pixels. |
| `native_format_html_shaped_scene.py` | Complete Source contextual runs rendered from exact physical font buffers. |
| `native_format_html_source_adapter.py` | Producer and portable reader adapters for body plus separate config metadata. |
| `native_format_html_source_metadata.py` | Separate, source-owned config custody for genuine HTML metadata observation. |
| `native_format_html_source_shaping.py` | Genuine bounded HarfBuzz shaping of exact independently admitted font bytes. |
| `native_format_html_source_styles.py` | Compile the actual Source web stylesheet and original AST text ancestry. |
| `native_format_html_style_calibration.py` | Actual independent Source writer/UA style expectations, never candidate px. |
| `native_format_html_table_witness.py` | Complete table attribute custody and finite alignment/caption witnesses. |
| `native_format_joint_source.py` | Live external native inputs and original launch custody, separate from JSON. |
| `native_format_math_anchors.py` | Exact source prose anchors for independently observed mathematical occurrences. |
| `native_format_observer_dispatch.py` | Actual native observer dispatch; unsupported source projections stay blocked. |
| `native_format_observer_outcome.py` | Preserve all native source findings and unsupported obligations at admission. |
| `native_format_observer_projection_replay.py` | Independent source-bound projected pages and EPUB native layout replay. |
| `native_format_observer_source_replay.py` | Independent current-reader semantic source and Office conversion replay. |
| `native_format_observer_validation.py` | Portable native observer replay entry points; producer paths remain labels. |
| `native_format_pdf_alpha_paint.py` | Independently decode original raster alpha and literal PDF soft-mask pixels. |
| `native_format_pdf_control_replay.py` | Existing literal PDF controls, with freshly checked complete return DATA. |
| `native_format_pdf_figure_positions.py` | Bind original caption identities and figure positions to source-only output. |
| `native_format_pdf_frontmatter.py` | Independent declared frontmatter text obligations from original YAML bytes. |
| `native_format_pdf_math.py` | Independent source algebra and anchored native PDF equation observations. |
| `native_format_pdf_mermaid_source.py` | Bounded independent current Mermaid source semantics, never writer parity. |
| `native_format_pdf_note_paint.py` | Original literal Note bodies, source-only counters and actual anchor paint. |
| `native_format_pdf_oracles.py` | Actual PDF text, glyph geometry and localized raster observations. |
| `native_format_pdf_positioned_math.py` | Independent equation interpretation at complete-source XeTeX paint positions. |
| `native_format_pdf_positions.py` | Zero-glyph source math positions from the actual XeTeX shipout engine. |
| `native_format_pdf_projection.py` | Fresh source-only canonical PDF TeX projection, before native compilation. |
| `native_format_pdf_raw_natbib.py` | Bind fully understood standalone source natbib commands to genuine labels. |
| `native_format_pdf_raw_source.py` | Real original-Pandoc interpretation of bounded source TeX occurrences. |
| `native_format_pdf_reference_parity.py` | Every-page glyph, vector and pixel parity for an admitted source reference. |
| `native_format_pdf_semantic_plan.py` | Independent source occurrence and literal-text plans for scientific PDFs. |
| `native_format_pdf_source.py` | Source-only PDF manuscript reconstruction and real pre-citeproc AST custody. |
| `native_format_pdf_source_decode_bounds.py` | Reserve finite source image decoding before any RGBA/RGB allocation. |
| `native_format_pdf_source_labels.py` | Interpret literal labels in original source TeX and its source-only AUX. |
| `native_format_pdf_source_layout.py` | Independent source page-break commands against actual literal glyph anchors. |
| `native_format_pdf_source_replay.py` | Portable independent replay of actual PDF source witness predicates. |
| `native_format_pdf_source_witness.py` | Independent actual-PDF literal, table-cell and decoded-source figure witnesses. |
| `native_format_pdf_tex_policy.py` | Explicit original-LaTeX lexical policy; unknown forms remain obligations. |
| `native_format_pdf_whole_reference.py` | Callable bounded complete-source PDF reference and zero-glyph math custody. |
| `native_format_portable_custody.py` | Portable original observations; receipt hashes do not authenticate origin. |
| `native_format_portable_source.py` | Reconstruct original source labels while admitting current source bytes. |
| `native_format_process_custody.py` | Bind a native worker to its supervisor's actual original PID and host. |
| `native_format_scientific_math.py` | Source-engine mathematical references and native glyph/shape comparisons. |
| `native_format_scientific_pdf_observer.py` | Admitted scientific PDF occurrences and real portable source witness replay. |
| `native_format_scope_replay.py` | Bind one complete configured suite and one fresh Current scope per original. |
| `native_format_semantic_ast.py` | Bounded source-only Pandoc occurrence and scientific structure compilation. |
| `native_format_semantic_original.py` | Retained pre-transform source semantics and independent survival obligations. |
| `native_format_semantic_source.py` | Actual bounded source parsing for independent HTML semantic obligations. |
| `native_format_tex_reference.py` | Bounded actual XeTeX references with explicit backend and dependency custody. |
| `native_format_worker_controls.py` | Existing worker parser/PDF controls under the original exact worker CLI role. |
| `native_full_worker_pdfium.py` | Source-owned PDFium preimport selection and held original/reader Code inputs. |
| `native_full_worker_pdfium_replay.py` | Authenticate the actual full-worker PDFium namespace/Code/image event. |
| `native_hosted_original_custody.py` | Live exact-run authenticated collection of Source-owned native artifact bytes. |
| `native_hosted_original_producer.py` | Deterministic bounded transport of genuinely supervised native originals. |
| `native_hosted_reader.py` | Cold installed Source reader with actual authenticated original custody. |
| `native_hosted_transport_archive.py` | Closed Source-native archive bounds and confined member decoding. |
| `native_html_hydration_ordinals.py` | Own HTML hydration ordinals in genuine body and original-source parsers. |
| `native_hydration_reconstruction.py` | Actual Source/SDK-bound hydration and combined-byte reconstruction. |
| `native_installed_custody_capture.py` | Observe the real cold installed SDK against its separately admitted wheel. |
| `native_installed_invocation.py` | Cold installed SDK capture/controller invocation under the original clock. |
| `native_installed_launcher.py` | Prepare a fresh Source4.0.1 wheel and supervise its cold native role. |
| `native_installed_preparation.py` | Source-locked fresh wheel/runtime preparation for the genuine native launcher. |
| `native_linux_calibre_runtime.py` | Actual Source-selected Linux Calibre package/embedded-Qt observations. |
| `native_loader_build.py` | Compile the one Source-owned Linux auditor through the actual native ToolAPI. |
| `native_loader_compilation_replay.py` | Exact compiler/header/body DATA reconstruction under enclosing Tool custody. |
| `native_loader_helper_memory.py` | Observe only the Source auditor's actual RX bytes in the consuming child. |
| `native_loader_maps.py` | Shared bounded kernel-map reconstruction; it supplies no native authority. |
| `native_loader_negative_control.py` | Actual positive/refusal control under existing genuine Source outer owners. |
| `native_loader_observation.py` | Actual consuming-process loader callbacks under the genuine Source ToolAPI. |
| `native_loader_protocol.py` | Fixed Linux callback wire format and actual consuming-process map/body reads. |
| `native_loader_qualification.py` | Actual paired native execution and separately authenticated current replay. |
| `native_loader_replay.py` | Independent loader DATA reconstruction under separately held original custody. |
| `native_mermaid_all_source_worker.py` | Thin installed-SDK entry point for the original complete28 Source component. |
| `native_mermaid_all_sources.py` | Actual complete Source fence observation and explicitly nominated fresh reader. |
| `native_mermaid_batch_all_sources.py` | Actual complete Source fence observation and explicitly nominated fresh reader. |
| `native_mermaid_batch_source_reference.py` | Genuine ordered Source11 artifacts and independently owned batch readers. |
| `native_mermaid_font_bodies.py` | Live independently nominated Source font bodies, separate from OS shaping. |
| `native_mermaid_production_tool.py` | Retain actual Mermaid production launches inside the existing fixed stage. |
| `native_mermaid_runtime_custody.py` | Original Mermaid/Node runtime bytes and exact observed platform-font faces. |
| `native_mermaid_runtime_selection.py` | Source-pinned npm Mermaid selection under a genuine live Source owner. |
| `native_mermaid_source_census.py` | Exact current manuscript Mermaid fences, source positions and document order. |
| `native_mermaid_source_effect_ink.py` | Finite original rectangular clip, opaque mask and identity filter profiles. |
| `native_mermaid_source_glyph_layout.py` | Actual Source-only label layout, separate from physical font authority. |
| `native_mermaid_source_marker_ink.py` | Source-defined marker placement, viewport and conservative unclipped ink. |
| `native_mermaid_source_path_ink.py` | Finite Source path extrema and real segment directions for SVG markers. |
| `native_mermaid_source_reference.py` | Actual source-only Mermaid producer, independent SVG paint, portable replay. |
| `native_mermaid_svg_batch_paint.py` | One genuinely supervised original SVG-only browser, fresh ordered targets. |
| `native_mermaid_svg_control_plan.py` | Plan genuine source/SVG controls without inventing their process receipts. |
| `native_mermaid_svg_controls.py` | Source-owned controls mutating actual original Mermaid SVG output bytes. |
| `native_mermaid_svg_geometry.py` | Bounded independent SVG geometry for original Mermaid graph witnesses. |
| `native_mermaid_svg_ink_enclosures.py` | Independent finite original SVG primitive/stroke/marker enclosures. |
| `native_mermaid_svg_paint.py` | Fresh SVG-only Chromium paint and actual glyph/font/process observations. |
| `native_mermaid_svg_topology.py` | Independent original-source graph witnesses for all five Mermaid families. |
| `native_newspaper_source.py` | Configured newspaper print checks against source and actual native rasters. |
| `native_office_cache_structure.py` | Compare retained cache Code as bounded DATA, never construct cached Code. |
| `native_office_content_witness.py` | Independent source-to-native-package witnesses for complete Office bodies. |
| `native_office_control_custody.py` | Distinct original Office control custody; full native-worker 0/75 is unchanged. |
| `native_office_control_supervisor.py` | Actual installed-SDK original four Office cells and Textbook seven controls. |
| `native_office_diagram_binding.py` | Actual original Office Mermaid source admission for native visibility. |
| `native_office_diagram_census.py` | Complete Source-composed Office Mermaid applicability and native targets. |
| `native_office_diagram_cohort.py` | Complete Source-scoped Office diagram original/Current execution and replay. |
| `native_office_diagram_control_worker.py` | One actual Source-owned Office child, invoked only by its original supervisor. |
| `native_office_diagram_controls.py` | Real native PDF mutations for independent Office diagram visibility controls. |
| `native_office_diagram_geometry.py` | Independent source PNG/actual PDF occurrence, clip and paint geometry. |
| `native_office_diagram_pdfium.py` | Separate actual PDFium source/native crop paint and installed DLL custody. |
| `native_office_diagram_positive.py` | Genuine complete-Source native diagram positive, before any PDF mutation. |
| `native_office_diagram_runtime.py` | Live Source-admitted PDFium provider and original inline-process observations. |
| `native_office_diagram_source.py` | Actual complete Office Mermaid Source under its live original process owner. |
| `native_office_diagram_visibility.py` | Actual source-only PDF image stencils and independent native visible ink. |
| `native_office_full_observer.py` | Actual complete-source native Office observation with explicit source witnesses. |
| `native_office_full_replay.py` | Independent portable complete-source Office replay without producer tool paths. |
| `native_office_full_worker_context.py` | Explicit Office nominees and genuine original/current worker contexts. |
| `native_office_hydration_ordinals.py` | Exact generated-field anchors through the actual Office Source filter chain. |
| `native_office_image_ink.py` | Independent decoded source assets and actual native PDF image witnesses. |
| `native_office_math_semantics.py` | Finite independent TeX expression trees for actual native package readback. |
| `native_office_mermaid_binding.py` | Bind original Office diagram occurrences to genuine source-only graphics. |
| `native_office_mermaid_font_binding.py` | Bind genuinely observed Office font usage to held Source body/face bytes. |
| `native_office_mermaid_ink.py` | Genuine independent SVG decode and native diagram-image ink projection. |
| `native_office_mermaid_semantics.py` | Finite independent Mermaid source grammar and bounded SVG interpretation. |
| `native_office_mermaid_source.py` | Actual source-bound Mermaid producer adapter; diagram ink admission is separate. |
| `native_office_nested_custody.py` | Office child DATA admitted only through the externally held full Original. |
| `native_office_observer.py` | Bounded native Office conversion; package parsing never grants layout acceptance. |
| `native_office_ordered_blocks.py` | Complete ordered Office block correspondence, subordinate to native controls. |
| `native_office_pdfium_event_replay.py` | Portable inline PDFium DATA admission through actual external custody. |
| `native_office_pdfium_images.py` | Actual selected PDFium process image mapping observations; no memory grant. |
| `native_office_pdfium_provider.py` | Source-locked PDFium wheel and exact actual installed provider admission. |
| `native_office_raw_roles.py` | Independent finite source roles for native Office raw occurrences. |
| `native_office_reference.py` | Source-only Office references with unresolved scientific coverage retained. |
| `native_office_reference_visual.py` | Full native Office page comparison, subordinate to independent source coverage. |
| `native_office_scientific_controls.py` | Genuine bounded scientific native Office controls, including preserved-content ink mutants. |
| `native_office_scientific_replay.py` | Independent portable replay of genuine scientific Office control processes. |
| `native_office_scientific_suite.py` | Select and replay scientific Office controls beside basic native controls. |
| `native_office_scope_cohorts.py` | One Original and one Current Office roster, followed by genuine paired replay. |
| `native_office_semantic_source.py` | Source-owned combined manuscript reconstruction for native DOCX and EPUB. |
| `native_office_source_coverage.py` | Independent scientific occurrence accounting; inventory alone never admits layout. |
| `native_office_table_coverage.py` | Independent table-cell accounting without granting native layout admission. |
| `native_oracle_axis_facts.py` | Conjunctions of actual completed specialized native predicates. |
| `native_oracle_control_requirements.py` | Complete literal control declarations from their existing Source owners. |
| `native_oracle_dispatch.py` | Finite projection of fresh checked native DATA onto held Source requirements. |
| `native_oracle_dispatch_requirements.py` | Compile one held Source requirement graph and its literal target plans. |
| `native_oracle_obligation_compiler.py` | Compile complete Source requirements without observing or granting a pass. |
| `native_oracle_obligation_spec.py` | Source-owned native proof requirements; these types cannot grant admission. |
| `native_oracle_original_control_facts.py` | Retain completed Original controller returns without reader or owner fabrication. |
| `native_oracle_phase.py` | Purpose-specific Original/reader native DATA collection after real checks. |
| `native_oracle_phase_original.py` | Read completed Original stage/control facts under its genuine existing owner. |
| `native_oracle_phase_reader.py` | Purpose collection of actual independent reader/Current native results. |
| `native_oracle_phase_residuals.py` | Typed phase residual DATA after genuine Original/Current native checks. |
| `native_oracle_selected_lineage.py` | Classify actual selected lineage; universal coverage limits remain advisory. |
| `native_original_supervisor.py` | Actual Source-owned original native worker supervision and terminal custody. |
| `native_pdf_candidate_raster.py` | Reuse the actual complete candidate raster from the enclosing native run. |
| `native_pdf_citation_replay.py` | Current-reader citation regeneration and exact native glyph/ink observations. |
| `native_pdf_citation_runtime.py` | Finite real citation tools and observed TeX dependency custody. |
| `native_pdf_citations.py` | Independent source-only natbib/plainnat citation references for scientific PDFs. |
| `native_pdf_cmap_bounds.py` | Bound actual CMap range expansion before native font-map construction. |
| `native_pdf_hydration_ordinals.py` | One annotated Source parser under the existing live Original/Current owner. |
| `native_pdf_index_bounds.py` | Admit exact classic or compressed PDF indexes before native decoding. |
| `native_pdf_literal_roles.py` | Exact Source Code/Link roles in existing complete PDF native observations. |
| `native_pdf_stream_bounds.py` | Bounded indexed-PDF admission before unbounded native stream parsing. |
| `native_pdf_stream_decode.py` | Finite supported PDF stream decoders used before native page parsing. |
| `native_pdf_whole_cohort.py` | Complete native PDF cohort observation and genuine current reproduction. |
| `native_pdf_whole_control_effect.py` | Actual native effects of complete Source-selected whole-PDF controls. |
| `native_pdf_whole_control_replay.py` | Independent whole-PDF control replay under genuine original Source custody. |
| `native_pdf_whole_control_run.py` | Real Source-bound whole-PDF control preparation and native predicates. |
| `native_pdf_whole_control_supervisor.py` | Genuine Source-owned complete PDF contract/control child supervision. |
| `native_pdf_whole_control_worker.py` | Fixed selected-SDK original whole-PDF page/occurrence control child. |
| `native_pdf_whole_controls.py` | Complete Source/page control requirements and actual native PDF mutations. |
| `native_pdf_whole_diagnostics.py` | Preserve complete whole-PDF diagnostic DATA without granting native authority. |
| `native_pdf_whole_reference_replay.py` | Original whole-PDF native custody and fresh current full-reference replay. |
| `native_pdf_whole_semantic_references.py` | Reuse genuine whole-reference custody for Source citation/math predicates. |
| `native_pdf_whole_source_witness.py` | Complete PDF Source occurrence predicates with actual whole-reference bytes. |
| `native_pdf_whole_worker.py` | Fixed original whole-PDF producer sequence under the existing live Source owner. |
| `native_pdfium_source_wheel.py` | Source-lock-authenticate nominated wheel bytes without importing its code. |
| `native_pitch_control_custody.py` | One fixed Pitch child role in the existing Source control custodian. |
| `native_pitch_control_mutations.py` | Single-target valid native mutations of actual configured Pitch bytes. |
| `native_pitch_control_plan.py` | Complete Source-selected Pitch pair/page control targets, without admission. |
| `native_pitch_control_replay.py` | Authenticate full Original Pitch axes, then rerun each once in genuine Current. |
| `native_pitch_control_run.py` | Real configured Pitch controls under an existing Source/SDK native owner. |
| `native_pitch_control_supervisor.py` | Fixed complete Pitch axis children, using the existing genuine Source route. |
| `native_pitch_control_worker.py` | One fixed selected-SDK child for a complete configured Pitch control axis. |
| `native_pitch_source.py` | SDK-owned Pitch compiler consuming admitted source DATA without executing it. |
| `native_pitch_source_admission.py` | Explicit immutable source admission for a separate mutable native mirror. |
| `native_pitch_source_layout.py` | Complete current-source native Pitch package layout, theme and replay. |
| `native_pitch_source_native.py` | Actual complete source-only Pitch PDF layout/theme/ink and portable replay. |
| `native_pitch_source_parity.py` | Source-driven Pitch OOXML package and all-three native PDF/PPTX pair closure. |
| `native_preparation_resources.py` | Bounded owner-controlled installed preparation capacity; no cleanup authority. |
| `native_prepared_code_readback.py` | Read exact retained original Code from actual prepared installed invocations. |
| `native_prepared_pdfium.py` | Prepare exact Source-listed wheel DATA for the cold native provider factory. |
| `native_print_artifact_controls.py` | Actual subprocess controls over configured print outputs and source witnesses. |
| `native_print_artifact_observer.py` | Source print witnesses bound to configured pipeline outputs, never surrogates. |
| `native_print_artifact_replay.py` | Portable configured-print admission; producer font and tool paths are labels. |
| `native_print_child_custody.py` | Fixed Source-owned control child roles under a genuine enclosing native owner. |
| `native_print_control_replay.py` | Independent configured-print mutant reconstruction with original process exits. |
| `native_print_font_custody.py` | Observe actual print font resources without redistributing installed fonts. |
| `native_print_mutations.py` | Deterministic mutations of actual native print bytes for source-owned controls. |
| `native_print_source_loader.py` | Load only held current print-source Python; existing pyc cannot substitute. |
| `native_print_witness.py` | Original Darwin print witnesses with complete source, font and decoder custody. |
| `native_print_witness_validation.py` | Independent portable print witness admission without producer font access. |
| `native_project_domain.py` | Actual declared project suites inside the genuine native Source owner. |
| `native_projection_checks.py` | Actual per-page projected glyph checks, retaining unsupported visual gates. |
| `native_projection_contracts.py` | Ordered deck obligations compiled from a source-reconstructed deck model. |
| `native_projection_source_dispatch.py` | Admitted manuscript projection and complete Pitch source companions. |
| `native_projection_source_replay.py` | Independent admitted manuscript and complete Pitch companion readback. |
| `native_qr_runtime.py` | Observe the actual linked QR core; portable receipts retain hashes, never binaries. |
| `native_readiness_input_copy.py` | Copy declared Source/common DATA into the owner-controlled full-Git mirror. |
| `native_renderer_section_roster.py` | Read complete Source-selected section rosters under actual paired Stage roles. |
| `native_renderer_source_call.py` | Retain the actual combined PDF/HTML Pandoc command under the fixed stage owner. |
| `native_renderer_stage_replay.py` | Read actual Original/Current combined renderers from one Core run each. |
| `native_scientific_reference_replay.py` | Independent portable reconstruction of retained source-only TeX references. |
| `native_scientific_reference_reproduction.py` | Fresh reader-local source compilation; original XDV never substitutes for ink. |
| `native_selected_manuscript_transforms.py` | Fixed Source manuscript transformations, never execution or native authority. |
| `native_slide_assets.py` | Exact source-owned Beamer figure resolution and private reference inputs. |
| `native_slide_checks.py` | Actual every-occurrence slide ink and every-page native layout observations. |
| `native_slide_control_adapter.py` | Actual Source-owned slide children and independently authenticated readback. |
| `native_slide_controls.py` | Actual baseline/later-page generic slide source/font/clipping/pixel controls. |
| `native_slide_observer.py` | Source-aware complete manuscript projection adapter for native dispatch. |
| `native_slide_raw_source.py` | Finite exact lexical witnesses for the configured raw slide source forms. |
| `native_slide_reference.py` | Bounded actual source-only Beamer references with complete source custody. |
| `native_slide_replay.py` | Independent portable current-source manuscript slide reference readback. |
| `native_slide_source.py` | Complete manuscript slide occurrence contracts, independent of native output. |
| `native_slide_tex_runtime.py` | Actual source-only TeX discovery and fresh admitted slide compilation. |
| `native_slide_tex_source.py` | Closed source-only cross-deck numbers and portable Beamer writer reconstruction. |
| `native_source_control_targets.py` | Source target requirement bindings and finite checked-result DATA projection. |
| `native_source_external_admission.py` | External native source bindings and a real full-Git mirror correspondence. |
| `native_source_provider_bootstrap.py` | Explicit admitted SDK package loading without a SourceDATA import root. |
| `native_stage_child.py` | Prepare one fixed Source stage child only inside its actual native owner. |
| `native_stage_child_code_closure.py` | Fixed complete Source stage-child Code/cache closure, granting no authority. |
| `native_stage_child_contracts.py` | Fixed Source stage-child DATA shape; validation never constructs an owner. |
| `native_stage_child_custody.py` | Fixed nested stage role authenticated through its genuine parent ToolAPI. |
| `native_stage_child_scope.py` | Actual fixed child scope for Source renderer records; no directory authority. |
| `native_stage_child_worker.py` | One fixed child that independently admits Source before an existing stage. |
| `native_stage_crossref_archive_replay.py` | Official archive readback through the genuine renderer→Crossref role. |
| `native_stage_loader_replay.py` | Loader readback through the actual fixed renderer/Stage role. |
| `native_storybook_source.py` | Source-bound raster storybook checks; producer summaries are never evidence. |
| `native_tex_section_reference.py` | Source-only standalone TeX compilation with genuine every-page references. |
| `native_tex_section_render.py` | Actual section compiler ToolAPI under the existing genuine native stage child. |
| `native_tex_section_replay.py` | Authenticate an Original TeX section and independently repeat its full writer. |
| `native_tex_section_source.py` | Exact Source-selected standalone TeX inputs in an owned reference tree. |
| `native_tex_stage_inputs.py` | Reconstruct the Source-selected section compiler packet as DATA. |
| `native_tool_process.py` | Original native tool process observations; no Python audit label for tools. |
| `native_tool_process_inputs.py` | Bounded native tool input/output observations shared by the real supervisor. |
| `native_tool_producer.py` | Process-local Source-admitted producer custody, separate from portable readback. |
| `native_tool_replay.py` | Portable native tool readback authenticated by live original launch custody. |
| `native_workflow_transport.py` | Validate bounded transport DATA for the Source-declared upload steps. |
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
| `required_candidate_collection.py` | Actually authenticate the exact completed candidate and every bounded shard. |
| `required_candidate_transport.py` | Source-owned bounded shards for the complete independently passed candidate. |


## Native reference custody

TeX references bind canonical distribution leaves to the selected Kpathsea
installation. `TEXMFROOT` is a locator, never a broad input root. Producer and
portable replay share the same explicit leaf policy, including Debian's split
system distribution; ambient TeX routing, local/auxiliary trees and private
execution overlaps are refused. Browser children freeze bytecode writes only
after their executed Source audit closes; parents still verify the exact final
cache inventory and bytes. Unit replay DATA cannot grant original native launch
custody; post-admission tamper coverage remains a hosted native acceptance gate.
