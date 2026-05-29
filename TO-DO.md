# 🚀 Repo TO-DO — active backlog

> **DESIGN ETHOS**
> Modular · Intelligent · Functional · Logged · Tested · Documented.
> Real methods only — never mocks or fakes.
> Every release ships with all tests green and all docs accurate (no
> legacy mentions).

This file tracks **only** the live backlog. Historical release notes are
in [`CHANGELOG.md`](CHANGELOG.md). Numbers below come from a live audit
run when this file was last edited.

---

## ✅ Live state snapshot

| Gate | Value | Source |
| --- | --- | --- |
| `pyproject.toml` version | `3.0.0` | `pyproject.toml#[project].version` |
| `mypy --strict infrastructure/` | **3 errors / ~345 files** (see `infrastructure/doctor/cli.py`; file count point-in-time) | `uv run mypy --strict infrastructure/` |
| `ruff check` (infra + canonical project src) | **clean** | `uvx ruff check infrastructure/ projects/template_code_project/src/` |
| `ruff format --check` | run `uvx ruff format --check infrastructure/ projects/template_code_project/src/` for current count | `uvx ruff format --check infrastructure/ projects/template_code_project/src/` |
| Bandit `-ll` (with `bandit.yaml` allow-list) | **HIGH 0 · MEDIUM 0 · LOW 0** | `uv run bandit -r -ll -c bandit.yaml infrastructure/ scripts/ projects/` (`exclude_dirs` in `bandit.yaml`) |
| Bandit strict-LOW pass | **0 unsuppressed** | `uv run bandit -c bandit.yaml -r --severity-level low …` |
| `pip-audit` CI gate | **blocking** (allow-list: `.github/pip-audit-ignore.txt`; retries in CI) | `.github/workflows/ci.yml` → job `security` |
| Zero-Mock Policy (`scripts/verify_no_mocks.py`) | **clean** | `uv run python scripts/verify_no_mocks.py` |
| `__all__` audit (`infrastructure.skills.check_all_exports`) | **0 violations** under live `infrastructure/` | `uv run python -m infrastructure.skills check-all-exports` |
| `docs-lint` (mermaid + cross-links + consistency + doc pairs) | run for current result | `uv run python scripts/lint_docs.py` |
| Stage-table generator | **idempotent** (5/5 docs in sync) | `uv run python scripts/generate_stage_table_doc.py` |
| API-reference generator | idempotent when the generated API doc matches package exports | `uv run python scripts/generate_api_reference_doc.py --check` |
| Architecture overview | regenerable from live package/config/project discovery | `uv run python scripts/generate_architecture_overview.py` |
| Unified `health` command | **11/11 gates PASS** | `uv run python -m infrastructure.core.health` |
| Pre-push hooks | `ruff-ci`, `mypy-ci`, `pre-push-quick`, `bandit-quick`, `skills-check`, `all-exports-check` | `.pre-commit-config.yaml` |
| Bench harness | **7 benches green** (opt-in via `-m bench`) | `tests/infra_tests/bench/` |
| Telemetry retention (`TELEMETRY_KEEP`, default 10) | wired into `TelemetryCollector._persist_report` | `infrastructure/core/telemetry/retention.py` |
| Steganography determinism (`STEGANOGRAPHY_DETERMINISTIC=1`) | byte-identical PDFs across runs | `infrastructure/steganography/config.py` |
| Multi-project parallel exec (`--parallel --max-workers=N`) | ~2.6× speedup on 3 synthetic projects | `scripts/execute_multi_project.py` |
| Coverage trend dashboard | regenerable via `--from-dir` / `--from-gh` | `scripts/generate_coverage_history.py` |
| Project-config schema-extension API | `register_project_schema_extension(name, schema)` | `infrastructure/core/config/schema.py` |
| `tests/infra_tests/` (no LLM, no bench) | **all pass** | `uv run pytest tests/infra_tests/ -q --ignore=tests/infra_tests/llm --timeout=60` |
| `infrastructure/` Python packages | live list and count in [`docs/_generated/canonical_facts.md`](docs/_generated/canonical_facts.md) | `find infrastructure -mindepth 1 -maxdepth 1 -type d -name '[!.]*'` |
| Docs subdirectories with both `AGENTS.md` + `README.md` | **26 / 26** | sweep |
| Infrastructure packages with local docs/skills | verify with docs lint plus `uv run python -m infrastructure.skills check-all-exports` | docs/tooling sweep |

---

## Thermo-nuclear remediation (2026-05-29)

Full report: [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md).

### Blockers (cleared)

| ID | Item | Status |
| --- | --- | --- |
| TN-B1 | Root `AGENTS.md` personal-memory sections fail public-repo contract test | **Fixed** — sections removed |
| TN-B2 | Stale `docs/reference/api-reference.md` fails health gate | **Fixed** — regenerated |
| TN-B3 | `scripts/render_working_projects.py` thin-orchestrator drift (354 LOC) | **Fixed** — `infrastructure/project/working_render.py` + 113-line script |
| TN-B4 | `architecture_viz.py` line-count WARN (822 LOC) | **Fixed** — semantic figure-module split |
| TN-B5 | `canonical_facts.md` infrastructure `.py` count drift | **Fixed** — count **460** |

### High (next waves)

| ID | Item | Status |
| --- | --- | --- |
| TN-H1 | Unify pytest argv: `test_runner` → `build_project_pytest_command` with qualified `project_root` | **Fixed** — `build_union_pytest_command` + `load_project_pyproject` |
| TN-H2 | Add `validation/content/prerender.py` leaf; stop rendering → full `markdown_validator` import | **Fixed** — `prerender.py` + `markdown_strip.py` |
| TN-H3 | Execute P1 splits: `backends.py`, `detectors.py`, `_dashboard_charts.py` (one wave each) | **Fixed** — semantic package/module splits; line-count gate clean |
| TN-H4 | Coverage gate single owner: remove `suite_runner` suppression + `enforce_project_suite_guards` compensation | **Fixed** — fail-loud; zero-collected guard only |

### Medium

| ID | Item | Status |
| --- | --- | --- |
| TN-M1 | `validation/content/markdown_strip.py` — dedupe strip helpers | **Fixed** |
| TN-M2 | Shared cross-ref core (`symbols.py`) for markdown + integrity | **Fixed** |
| TN-M3 | `_latex_log_parse.py` + config-driven suggested citation | **Fixed** (title-page full extraction deferred) |
| TN-M4 | `load_project_pyproject()` — single tomllib read in pytest orchestration | **Fixed** |

### Deferred (waived with reason)

| ID | Item | Reason |
| --- | --- | --- |
| TN-D1 | `template_autoresearch` 500+ LOC domain modules | Under 600 watch threshold; split when a module crosses 600 |
| TN-D2 | Gate `TEST_DISCOVERY_LOG` for collect-only preamble | Ops convenience; low CI impact |
| TN-D3 | Lazy `__init__.py` barrels on wide hubs | P1 row; no import-time regression until split waves land |

---

## 🟢 Minor (1–2 hours each)

* **GH-HYGIENE-1 — GitHub supply-chain & process hardening.**

  **Problem:** workflow/process gaps surfaced by the `.github` audit. Subs
  `c` (`.github/CODEOWNERS`) and `d` (`SECURITY.md` / `CITATION.cff` /
  `CONTRIBUTING.md`) shipped and were cleared from this backlog (see
  [`CHANGELOG.md`](CHANGELOG.md)). Three independent subs remain, ~½–2 h each;
  each row carries its own smallest next step and a verifiable acceptance.

  | Sub | Item | Why it matters | Smallest next step | Acceptance (observable / one command) |
  | --- | --- | --- | --- | --- |
  | a | SHA-pin every `uses:` action in `ci.yml`/`release.yml`/`stale.yml` to a full 40-char commit SHA + trailing `# vX.Y.Z`; let Dependabot bump the pin | Mutable tags are force-pushable — supply-chain compromise vector | enumerate unpinned refs, replace each tag with its commit SHA | `rg -n 'uses: .+@(v[0-9]\|main\|master)$' .github/workflows` returns **no matches** |
  | b | Add an `actionlint` CI job (`needs: []`, `permissions: { contents: read }`) | Would have caught the `hashFiles()`-in-job-`if:` parse outage; prevents regression | add a job running SHA-pinned `rhysd/actionlint` | `actionlint` job exists in `ci.yml` and is green on a PR |
  | e | Dependabot auto-merge workflow gated on green required checks | Safe minor/patch action bumps need zero manual toil | add `.github/workflows/dependabot-automerge.yml` using `gh pr merge --auto`, guarded by `github.actor == 'dependabot[bot]'` | a Dependabot minor/patch PR auto-merges once required checks pass |

  **Out of scope:** rewriting unrelated workflow logic; renaming required-check
  contexts (branch-protection contract — see
  [`.github/AGENTS.md`](.github/AGENTS.md)).

---

## 🟡 Medium (½ – 2 days each)

_None active._ (Prior MED items shipped and were cleared to
[`CHANGELOG.md`](CHANGELOG.md); this section tracks only open medium work.)

---

## 🟠 In-flight — 2026-05-20 logging & output-format hardening

> **Trigger.** Clean 4/4 multi-project pipeline run on 2026-05-20
> (`actinf_policy_entanglement_lean` + `deep_temporal_affect` +
> `template_code_project` + `template_prose_project`, wall time 67 m 21 s).
> Inspection of the terminal output and the rendering code surfaced four
> classes of defect — chrome-heavy console output, spinner/pytest collision,
> per-file render noise, and no DOCX/EPUB output path nor any per-format
> on/off toggle. ISA + live status:
> `~/.claude/PAI/MEMORY/WORK/template-logging-formats-2026-05-20/ISA.md`.
>
> **Single discipline:** an item is closed (`[x]`) only when the on-disk
> artifact named in the **Acceptance** column has been produced and the
> command output is pasted back into the closure note. No item is ticked
> from intention or self-report.

### A. Docs (distill the run, document the contract)

| ID | Item | Effort | Why it matters | Smallest next step | Acceptance (observable / one command) |
| --- | --- | --- | --- | --- | --- |
| **LOG-DOC-OUTPUT-DESIGN-1** | New `docs/operational/logging/output-design.md` capturing the visual contract of pipeline output | Small (1–2 h) | The existing `docs/operational/logging/` set documents the API, not the *visual contract*. A new doc captures the canonical clean-run image and the failure-mode image so regressions become obvious. | Author the doc with six sections (why, clean-run reference, failure-mode reference, summary-block schema, LOG_LEVEL dial, see-also). Cross-link from `docs/operational/logging/README.md` and `docs/documentation-index.md`. | `test -f docs/operational/logging/output-design.md && rg -q '## Summary block schema' docs/operational/logging/output-design.md && rg -q 'output-design.md' docs/operational/logging/README.md` |
| **LOG-DOC-LAST-RUN-1** | Auto-generate `docs/_generated/last-run-summary.md` from every multi-project run | Small (1–2 h) | The end-of-run multi-project summary table is the best output the system produces and currently lives only in stdout. Persisting it under `docs/_generated/` (next to `coverage_history.md`) makes regressions diff-able. | Extend `infrastructure/core/pipeline/multi_project.py::format_multi_project_summary` to also write the rendered block to `docs/_generated/last-run-summary.md` with a `> Auto-generated by … Do not edit manually.` banner + ISO-8601 timestamp. Add a unit test in `tests/infra_tests/core/pipeline/` that confirms the write. List the new artifact in `docs/_generated/README.md`. | After `./run.sh --pipeline --project template_prose_project`: `test -s docs/_generated/last-run-summary.md && head -3 docs/_generated/last-run-summary.md \| grep -q 'Auto-generated'` |
| **LOG-DOC-SUMMARY-1** | Document `format_multi_project_summary()` + `_pipeline_summary.py` as the canonical reporting surface | Small (½ h) | Without a doctrinal docstring, future contributors can't tell a stable contract from a debug print. Tests already assert on substring presence — make that the spec. | Add a top-level docstring to `format_multi_project_summary` declaring "STABILITY: canonical pipeline-completion reporting surface; tests assert on substring presence, not layout" and schema description of each section. Mirror on `_pipeline_summary.py`. Add a "Pipeline Summary Format" section to `docs/operational/reporting-guide.md`. | `rg -q 'STABILITY: canonical' infrastructure/core/pipeline/multi_project.py infrastructure/rendering/_pipeline_summary.py && rg -q 'Pipeline Summary Format' docs/operational/reporting-guide.md` |

### B. Terminal logging (density, gating, collision-fix, consistency)

| ID | Item | Effort | Why it matters | Smallest next step | Acceptance (observable / one command) |
| --- | --- | --- | --- | --- | --- |
| **LOG-CONSOLE-FORMATTER-1** | Strip `ℹ️ [YYYY-MM-DD HH:MM:SS] [INFO]` chrome from the console handler; keep it on the file handler | Small (1 h) | ~38 chars of redundant prefix on every line; the terminal does not need timestamps, the log file does. New env `LOG_TERMINAL_VERBOSE=1` restores old behavior. | In `infrastructure/core/logging/formatters.py`, split `TemplateFormatter` into a `ConsoleFormatter` (clean prefix-less output, optionally a single emoji for warn/error) and the file-side `FileFormatter` (current behavior). Wire `ConsoleFormatter` to the stdout handler in `setup.py`; file handler keeps the full prefix. Add `get_terminal_verbose_enabled()` to `constants.py`. Update affected tests under `tests/infra_tests/core/logging/`. | `python -c "from infrastructure.core.logging.utils import get_logger; get_logger('t').info('hi')"` prints `hi` (or `ℹ️  hi`) — **no `[INFO]`, no `[ts]`**; and after a pipeline run `rg -q '\[20.*\] \[INFO\]' projects/template_prose_project/output/logs/pipeline.log` still finds the prefixed file form |
| **LOG-RENDER-VERBOSITY-1** | Demote per-file render chatter to DEBUG; keep one INFO line per file | Small (1–2 h) | Stage 5 currently emits ~10 INFO lines per markdown file. With 8 files × 4 projects = ~320 lines just for per-file rendering. Plus a 7-line preamble per analysis script (~112 lines). All of this is DEBUG-grade. | In `infrastructure/rendering/pipeline.py` (`_render_individual_files`, `_render_combined_outputs`), `slides_renderer.py`, `web_renderer.py`, `_pdf_combined_renderer.py`: keep one INFO line per file (`[N/M] file.md → slides.pdf (22 KB) + .html (6 KB) in 2.7s`); move per-step "Generating beamer slides…", "Compiling …", etc. to `logger.debug`. Same treatment for the 7-line per-script preamble in the analysis stage. | At `LOG_LEVEL=1`, `grep -c "Rendering Markdown file" projects/template_prose_project/output/logs/pipeline.log` is **0**; at `LOG_LEVEL=0` the count returns to its prior value (regression check) |
| **LOG-SPINNER-COLLISION-1** | Skip the spinner when the wrapped command streams subprocess stdout to terminal | Small (1 h) | During the pytest stage, `log_with_spinner(...)` in `infrastructure/reporting/suite_runner.py:198` runs while pytest streams `PASSED` lines to the same TTY. The spinner's `\r` collides with pytest output: visible garble like `⠋ Running project tests…projects/.../test_X PASSED`. | Add `streaming_subprocess: bool = False` to the suite-runner config; set it `True` for the test invocation; gate `log_with_spinner(...)` on `not config.streaming_subprocess`. Spinner stays for `ollama_setup.py` (non-streaming). | After a project test run: `grep -P '[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏].*PASSED' projects/template_prose_project/output/logs/pipeline.log` returns **no matches** |
| **LOG-SEPARATOR-CONSTS-1** | Centralize separator widths into `infrastructure/core/logging/constants.py` | Small (½ h) | Four hand-rolled widths in flight (`=*60`, `=*50`, `━*46`, `-*64`, `=*64`). The existing `_HEADER_SEPARATOR_WIDTH` / `_STAGE_SEPARATOR_WIDTH` cover two of them; the others are scattered. | Promote four constants — `BANNER_WIDTH=60`, `STAGE_WIDTH=46`, `SUBSECTION_WIDTH=50`, `TABLE_WIDTH=80` — to `constants.py`. Re-export the existing two from `pipeline_logging.py` (kept for backwards compat) but make them aliases. Replace hardcoded uses in `infrastructure/reporting/pipeline_test_runner.py` (`=*64`/`-*64`) and `infrastructure/core/pipeline/multi_project.py` (default `width=BANNER_WIDTH`). | `rg -n '"=" \* 6[04]\|"-" \* 6[04]' infrastructure/` returns **no hits** outside `constants.py`; `python -c "from infrastructure.core.logging.constants import BANNER_WIDTH, STAGE_WIDTH, SUBSECTION_WIDTH, TABLE_WIDTH; print((BANNER_WIDTH, STAGE_WIDTH, SUBSECTION_WIDTH, TABLE_WIDTH))"` prints `(60, 46, 50, 80)` |

### C. Output formats (DOCX, EPUB, per-format on/off)

| ID | Item | Effort | Why it matters | Smallest next step | Acceptance (observable / one command) |
| --- | --- | --- | --- | --- | --- |
| **FMT-DOCX-1** | New `infrastructure/rendering/docx_renderer.py` invoking pandoc | Small (1–2 h) | DOCX is one of the most-requested deliverable formats for research output (journal submissions, collaborator markup). Pandoc is already wired for HTML + combined PDF; DOCX is one pandoc invocation away. | Add `docx_renderer.py` with `render_docx(combined_md, output_path, *, reference_doc=None, bibliography=None) -> Path`. Use `pandoc -f markdown+yaml_metadata_block --citeproc --bibliography=… -o output.docx` and optional `--reference-doc=`. Add `tests/infra_tests/rendering/test_docx_renderer.py` running real pandoc against tmp_path. | After running the test: `file -b --mime-type tmp/output.docx` returns `application/vnd.openxmlformats-officedocument.wordprocessingml.document` AND the file is > 1 KB |
| **FMT-EPUB-1** | New `infrastructure/rendering/epub_renderer.py` invoking pandoc | Small (1 h) | EPUB is the right format for long-form prose to read on e-readers. Bundled with DOCX so the format-toggle plumbing only needs to be wired once. | Add `epub_renderer.py` with `render_epub(combined_md, output_path, *, cover_image=None, bibliography=None) -> Path` using `pandoc -o output.epub --citeproc`. Add `tests/infra_tests/rendering/test_epub_renderer.py`. | After running the test: `unzip -p tmp/output.epub OEBPS/content.opf \| grep -q '<dc:title>'` succeeds |
| **FMT-TOGGLES-1** | Per-format on/off toggle in `RenderingConfig` + `config.yaml` | Small (2 h) | The pipeline currently renders all formats unconditionally. A user who only wants HTML pays the LaTeX/xelatex cost on every run. A user who wants DOCX but not slides has no knob. | Extend `RenderingConfig` (`infrastructure/rendering/config.py`) with five booleans: `enable_pdf=True`, `enable_html=True`, `enable_slides=True`, `enable_docx=False`, `enable_epub=False`. Extend `from_env()` to read `ENABLE_PDF=0/1` etc. Add `render: { formats: { pdf: true, … } }` block to `projects/{name}/manuscript/config.yaml` and the project-config schema in `infrastructure/core/config/schema.py`. `infrastructure/rendering/pipeline.py` reads the formats block and skips each renderer when False, logging `[skip] <format> rendering disabled in config`. Add `tests/infra_tests/rendering/test_format_toggles.py`. | Setting `enable_pdf: false` in `config.yaml` and running the pipeline: `find projects/template_prose_project/output/pdf -name '*.pdf' \| wc -l` returns **0** and `rg -q '\[skip\] PDF rendering disabled' projects/template_prose_project/output/logs/pipeline.log` succeeds |
| **FMT-VERIFY-1** | End-to-end format verification on `template_prose_project` | Small (½ h) | Adding new formats and toggles is only verified when the whole pipeline runs and produces the expected artifact set. | Three end-to-end runs with different toggle combinations: all-on, DOCX-on-EPUB-on-PDF-off, slides-off-DOCX-on. Document the artifact tree from each under `docs/operational/logging/output-design.md` "Reference Images" section. | After the all-on run: every entry in `find projects/template_prose_project/output -type f -name '*combined*' -newer pyproject.toml` includes one each of `.pdf`, `.html`/`index.html`, `.docx`, `.epub`; slides PDF count equals manuscript section count |

### D. Cross-cutting (no-regression discipline)

| ID | Item | Effort | Why it matters | Smallest next step | Acceptance (observable / one command) |
| --- | --- | --- | --- | --- | --- |
| **LOG-NO-REGRESSION-1** | All existing tests stay green | Small (½ h continuous) | The non-negotiable backstop. Logging and rendering changes are easy to land but easy to break a downstream test. | After each change: run `uv run python scripts/01_run_tests.py --project template_prose_project` and `uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60`. New tests for the new code paths included. | Both commands exit 0; project coverage ≥ 90 %; infra coverage ≥ 60 % |
| **LOG-ROLLBACK-1** | Provide exact-rollback path for the console-formatter change | Trivial | Aesthetics are taste; a user who depends on the old format must be able to opt back in. | `LOG_TERMINAL_VERBOSE=1` honored by `ConsoleFormatter` to restore the `ℹ️ [ts] [INFO] …` prefix. Documented in `docs/operational/logging/README.md`. | `LOG_TERMINAL_VERBOSE=1 python -c "from infrastructure.core.logging.utils import get_logger; get_logger('t').info('hi')"` prints a line containing both `[INFO]` and an ISO-8601-shaped timestamp |

### Implementation order (recommended)

1. **`LOG-SEPARATOR-CONSTS-1`** — pure refactor, zero-risk, unblocks visual sanity
2. **`LOG-CONSOLE-FORMATTER-1`** — biggest aesthetic win, contained change
3. **`LOG-SPINNER-COLLISION-1`** — fixes the most visible defect
4. **`LOG-RENDER-VERBOSITY-1`** — touches multiple renderers
5. **`FMT-DOCX-1` + `FMT-EPUB-1`** — new files, additive
6. **`FMT-TOGGLES-1`** — wires the new renderers into the pipeline
7. **`LOG-DOC-LAST-RUN-1` + `LOG-DOC-SUMMARY-1`** — easy doc work
8. **`FMT-VERIFY-1`** — runs after everything lands
9. **`LOG-DOC-OUTPUT-DESIGN-1`** — captures the final state as the canonical reference image
10. **`LOG-NO-REGRESSION-1` + `LOG-ROLLBACK-1`** — continuous backstop

### Anti-criteria (must NOT happen)

- ❌ No item gets ticked from intention. Every `[ ]→[x]` transition cites a verbatim artifact (file content, command output, MIME line).
- ❌ No subagent uses the Edit/Write tool in this repo — it is denied. All subagent writes go through a Bash `python3` heredoc.
- ❌ No coverage regression. ≥ 60 % infra / ≥ 90 % project / ≥ 75 % combined union remain.
- ❌ No silent change to existing default output. `enable_docx/epub=False` initially so today's pipelines are untouched.
- ❌ No reliance on `should work` / `appears to` / `looks correct` — only on probe output.

---

## 🔍 Tracked — scoped backlog (not scheduled)

Items here have a **default deferral** until someone picks them up; each row
states effort, why it matters, and the smallest next step.

| ID | Topic | Effort (rough) | Why | In scope (this item) | Out of scope | Next step |
| --- | --- | --- | --- | --- | --- | --- |
| **ARCH-CONFTEST-1** | Cross-project `tests/conftest.py` | Medium (½–2 days if pursued) | Multiple `conftest.py` trees in one pytest proc collide on `tests.conftest`. | Doc-only first: state the **one subprocess per project** contract in [`tests/AGENTS.md`](tests/AGENTS.md) and one allowed pattern (uniquely named `pytest_plugins` / shared import, no duplicate `tests.conftest`). Code later: optional thin helper if it does not change CI’s per-project pytest shape. | Switching CI to a single global pytest over all `projects/*/tests/` without `run_per_project_pytest`; silent `tests.conftest` collisions. | Read [`tests/AGENTS.md`](tests/AGENTS.md); add a short “Shared fixtures” subsection that names the collision failure mode and the allowed extension. |
| **DEP-DEFUSEDXML-1** | Replace `defusedxml` with hardened stdlib | Medium (1–3 days) | Drop third-party XML dep once stdlib usage is provably safe on supported Pythons. | Refactor [`infrastructure/reporting/coverage_history.py`](infrastructure/reporting/coverage_history.py), [`infrastructure/search/literature/fulltext.py`](infrastructure/search/literature/fulltext.py), [`infrastructure/search/literature/arxiv_backend.py`](infrastructure/search/literature/arxiv_backend.py); add regression tests on real sample XML. | Drive-by changes to unrelated parsers; blanket `# nosec B314`. | `rg defusedxml` for call sites; read CPython 3.10–3.12 notes on `xml.etree` (DTD/expansion/external entities) for the parse modes this repo uses. |
| **WIN-SETUPHOOK-1** | `setup_hook` Windows path | Small (mostly docs) | POSIX `setup_hook.sh` does not run on Windows; Python entry is required there. | Onboarding and CI stay aligned: [`docs/guides/new-project-setup.md`](docs/guides/new-project-setup.md) states Windows uses `setup_hook.py`; [`.github/workflows/ci.yml`](.github/workflows/ci.yml) `setup-hook-windows-smoke` still runs only when a matching `projects/**/scripts/setup_hook.py` exists. | Porting the shell hook to PowerShell; guaranteeing every Windows environment. | `rg setup_hook` after template changes; confirm the workflow `paths` / `if:` gates still match the doc. |

**Canonical test runner reminder (ARCH-CONFTEST-1):** one pytest subprocess
per `projects/<name>/tests/` via
`infrastructure.core.test_runner.run_per_project_pytest` and CI `test-project`.
A single pytest collecting multiple project trees with distinct `conftest.py`
files remains **unsupported**.

**Per-ID closure notes**

- **GH-HYGIENE-1f:** `release.yml` passes event/tag expression values through
  step `env:` variables before shell use; `actionlint` is clean and direct tag
  interpolation inside `run:` blocks is gone.

- **GH-HYGIENE-1g:** the `performance` job now grants `actions: read`, so
  `scripts/generate_coverage_history.py --from-gh` can download workflow
  artifacts with the built-in `GITHUB_TOKEN` instead of silently no-oping.

- **ARCH-CONFTEST-1 (doc track):** [`tests/AGENTS.md`](tests/AGENTS.md) states
  the per-project pytest rule, names the `tests.conftest` collision, and
  documents one sanctioned way to share fixtures without a second pytest
  collection root.

- **DEP-DEFUSEDXML-1:** Same inputs produce the same parsed structures as
  before; Bandit B314 clean without `# nosec` carpet-bombing; `defusedxml`
  removed from `pyproject.toml`; XML-related tests pass on real samples.

- **WIN-SETUPHOOK-1:** Doc and workflow both describe the Windows smoke job
  condition; no contradictory “POSIX-only” wording for people on Windows.

---

## ⚠️ Known divergences from `CHANGELOG.md`

_None open._ If you find a **new** drift between `CHANGELOG.md`, `TO-DO.md`,
and `.github/workflows/ci.yml`, log it here and fix forward rather than
rewriting shipped changelog entries. (The prior v0.7.x divergences were closed
and verified; their detail now lives in [`CHANGELOG.md`](CHANGELOG.md), not in
this live backlog.)


---

## Conventions

- Every release row in `CHANGELOG.md` corresponds to a `vX.Y.Z` git tag.
- **Backlog IDs** (`GH-HYGIENE-1`, `ARCH-CONFTEST-1`, …) are stable; use
  them in commit messages or doc comments when touching related work so grep
  stays useful. A cleared item's ID is retired with it (its history moves to
  `CHANGELOG.md`); never silently reuse a retired ID for new work.
- Every TO-DO item has explicit acceptance criteria and a verifiable
  command in the **Acceptance** line (tracked-table items use **Per-ID closure
  notes** below the table).
- **Elevation:** when an item in **Tracked** gets an owner and schedule, move
  it to **Minor** or **Medium** with a target window; shrink **Tracked** to
  defer-only work.
- Numbers in the "Live state snapshot" table come from a live audit;
  re-baseline them — never copy stale values.
- **Bandit policy.** Repo-wide LOW-severity allow-list lives in
  [`bandit.yaml`](bandit.yaml) with per-test-ID justifications. CI runs
  both a MEDIUM+ pass and a strict LOW pass — both invoked with `-c
  bandit.yaml`. Any new LOW outside the allow-list must be either fixed
  or annotated inline with `# nosec <ID> reason: …`. See
  [`docs/rules/security.md`](docs/rules/security.md) and
  [`.github/AGENTS.md`](.github/AGENTS.md).
- **`__all__` policy.** Every re-exporting Python module under
  `infrastructure/` must define an explicit `__all__`; the
  `check-all-exports` CI gate enforces this. See
  [`docs/rules/api_design.md`](docs/rules/api_design.md).

## See also

- [`CHANGELOG.md`](CHANGELOG.md) — historical release notes
- [`docs/development/roadmap.md`](docs/development/roadmap.md) — longer-term direction
- [`.github/AGENTS.md`](.github/AGENTS.md) — CI gates and quality thresholds
- [`docs/audit/archived/triple-check-report-2026-04-27.md`](docs/audit/archived/triple-check-report-2026-04-27.md) — 2026-04-27 integrity audit (archived; live linter at `scripts/lint_docs.py`)
