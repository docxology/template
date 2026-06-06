# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks live work after the `v3.2.0` template release. Historical
release detail belongs in [`CHANGELOG.md`](CHANGELOG.md); generated counts and
project rosters belong in
[`docs/_generated/canonical_facts.md`](docs/_generated/canonical_facts.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Live state snapshot

Refreshed on **2026-06-06** from the post-`v3.2.0` release state and local
inspection. Re-run the commands in the **Source** column before copying any
number into prose.

| Gate or surface | Current value | Source |
| --- | --- | --- |
| Package version | `3.2.0` | `pyproject.toml#[project].version` |
| Latest template release | `v3.2.0` (published 2026-06-04) | [`CHANGELOG.md`](CHANGELOG.md), GitHub release tag |
| Public source scope | `infrastructure` plus nine public exemplar `src/` trees | `uv run python -m infrastructure.project.public_scope source-paths` |
| Public exemplars | `template_active_inference`, `template_autoresearch_project`, `template_autoscientists`, `template_code_project`, `template_newspaper`, `template_prose_project`, `template_sia`, `template_template`, `template_textbook` | [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) |
| Canonical generated facts | 20 importable infrastructure packages; 526 infrastructure Python modules; nine exemplar coverage gates at or above 90 % | [`docs/_generated/canonical_facts.md`](docs/_generated/canonical_facts.md) |
| Open GitHub PRs | 5 open: 3 Dependabot (`codecov-action` #5, `actions/stale` #4, `astral-sh/setup-uv` #3) + 2 maintainer (#23 sheaf integrity gates, #14 infrastructure composability audit) | `/opt/homebrew/bin/gh-axi pr list` |
| Docs lint status | links-only, consistency-only, and doc-pairs checks were clean in the `v3.2.0` release verification | `uv run python scripts/lint_docs.py --links-only --quiet --json`, `--consistency-only`, `--doc-pairs-only` |
| Mermaid lint status | clean with chunked batch rendering under the default total budget | `uv run python scripts/lint_docs.py --mermaid-only --quiet --json` |
| Release verification baseline | public project tests, Active Inference focused gate, docs invariant suite, Ruff, format, mypy, drift, skills, exports, SIA validation, tracked-project/generated-artifact guards, and pre-push hooks passed | `v3.2.0` release notes and local command history |

---

## Recently shipped

Keep this section short. Details live in release notes or archived audits.

- **Reference-existence + AI-writing infrastructure (2026-06-06):** new
  `infrastructure/reference/verification/` deterministic anti-hallucination gate
  (Crossref→OpenAlex/arXiv resolver, SQLite cache, offline-first) and
  `infrastructure/validation/content/ai_writing.py` AI-writing fingerprint
  detector (`validation.cli prose-quality`); wired into the `docs/prompts`
  workflows. Clean-room distillation of academic-research-skills ideas
  (CC-BY-NC-4.0); no code vendored.
- **Infra test parallelization (2026-06-06):** `pytest-xdist` + `-n auto` on the
  CI `test-infra` job cut each leg from ~892s to ~585s; suite verified
  parallel-safe; default `-v` dropped from `addopts`.
- **Docs accuracy sweep (2026-06-06):** audited `docs/` + every
  `infrastructure/*/{SKILL,README,AGENTS}.md`; corrected examples that cited
  methods/params/CLI flags/test paths that did not exist (every fixed command
  re-verified to resolve).
- **Docs/infrastructure/.github review pass (2026-06-05, PR #24 + follow-up):**
  `CODEOWNERS` aligned to the 9-exemplar CI matrix; `concurrency:` guards on
  `release.yml`/`stale.yml`; `find_repo_root` centralized in
  `infrastructure.core.project_paths` (fixing a latent `parents[4]` bug in
  `multi_project_cli`); infra quick wins (dead-code removal, portable cache
  default, redundant-`normpath` drop, facade-test + regex-doc hygiene); docs
  fixes (core/README index row, Pitfall-6 anchor); and `integration_audit.py`
  split into a facade + two builder modules to clear the line-count WARN.
- **DOCX/EPUB renderers + format toggles (FMT-BUNDLE-1):** real Pandoc-backed
  `docx_renderer.py`/`epub_renderer.py` with `enable_docx`/`enable_epub` config
  toggles (default off) and `test_docx_renderer.py`/`test_epub_renderer.py`.
- **Active Inference validation spine v2 (AI-SPINE-V2):** producer-completeness,
  integration dependency graph, and seed/commit artifact provenance shipped with
  stale / missing-producer / missing-consumer negative controls in
  `test_roadmap_promotion.py`.
- **Infrastructure coverage gaps rebaselined (COVERAGE-REBASE-1):**
  [`docs/development/coverage-gaps.md`](docs/development/coverage-gaps.md)
  re-measured against the current tree.
- **GitHub workflow supply-chain hardening (GH-PIN-1, GH-ACTIONLINT-1,
  GH-AUTOMERGE-1):** all workflow `uses:` refs SHA-pinned (version comments
  retained); a read-only `actionlint` CI gate added; a guarded Dependabot
  automerge workflow (actor + minor/patch + green-checks) added.
- **XML parser policy (DEP-DEFUSEDXML-1):** `defusedxml` confirmed as the single
  mandated parser, enforced by an AST import guard + live-tree test and
  documented in [`docs/rules/security.md`](docs/rules/security.md).
- **`template_autoresearch_project` flat→package refactor completed:** 40
  orphaned flat modules removed, the 6 packages are the single source of truth,
  the dpi/palette figure-override regression fixed; coverage restored to
  92.81%.
- **Mermaid lint fail-closed:** `mmdc` exiting 0 without writing output is now
  treated as a failure (was silently swallowed on the batch path).
- **`v3.1.0` release train:** SIA joined the public exemplar scope; Active
  Inference gained the first validation-spine tracks; docs signposting moved to
  `projects/templates/...`; public coverage orchestration was hardened. See
  [`CHANGELOG.md`](CHANGELOG.md).
- **Thermo-nuclear remediation waves:** 2026-05-29 and 2026-05-30 blockers and
  branch deltas are closed. See
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md)
  and
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-30.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-30.md).
- **Tracked setup-hook/conftest docs:** Windows setup-hook behavior and the
  one-pytest-process-per-project `conftest.py` rule are documented. Keep
  [`tests/AGENTS.md`](tests/AGENTS.md) and
  [`docs/guides/new-project-setup.md`](docs/guides/new-project-setup.md) aligned
  when touching those surfaces.
- **Mermaid lint bounded diagnostics:** all-repo Mermaid lint now has an
  internal total budget, chunked batch rendering, and file/line/`mmdc` command
  details for timeout diagnostics.

---

## Minor

### TODO-REBASE-1 - Keep the live backlog synchronized with `v3.2.0`

- **Problem:** `TO-DO.md` can drift behind release metadata, generated facts,
  and public exemplar scope.
- **Why it matters:** agents use this file to pick work; stale version numbers
  create false priorities.
- **Smallest next step:** after each release, refresh the live snapshot and move
  shipped rows to [`CHANGELOG.md`](CHANGELOG.md) or archived audit docs.
- **Acceptance:** `rg -n '3\.2\.0|v3\.2\.0' TO-DO.md CHANGELOG.md pyproject.toml`
  finds the current release, and
  `uv run python -m infrastructure.project.public_scope source-paths` prints
  `infrastructure` plus the nine public exemplar source paths.
- **Out of scope:** re-running generated docs unless generated facts changed.

### AI-GATE-CACHE-1 - Formalize Active Inference gate bootstrap caching

- **Problem:** focused Active Inference gate tests rebuild expensive deterministic
  artifacts repeatedly; a post-release local helper change now sketches a cache.
- **Why it matters:** faster focused gates reduce review latency, but cached
  artifacts must never hide stale or missing outputs.
- **Smallest next step:** land a test-supported gate cache that reuses a project
  root only when required gate artifacts are present, and keep the stale saved
  hash negative control.
- **Acceptance:** focused validation-spine and gate tests pass from a clean
  checkout, including a negative control where a stale saved hash fails.
- **Out of scope:** changing `v3.1.0` or force-moving the release tag.

### ARCH-CONFTEST-1 - Keep cross-project pytest rules explicit

- **Problem:** a single pytest process collecting multiple project test trees can
  collide on repeated `tests/conftest.py` plugin names.
- **Why it matters:** the failure mode is confusing and easy to reintroduce when
  adding new exemplars.
- **Smallest next step:** keep [`tests/AGENTS.md`](tests/AGENTS.md) and pipeline
  docs aligned with the one-subprocess-per-project rule.
- **Acceptance:** docs name the collision and the sanctioned runner
  `infrastructure.core.test_runner.run_per_project_pytest`.
- **Out of scope:** converting CI to one global pytest collection over all
  project tests.

---

## Medium

### LOG-CLEAN-1 - Finish terminal logging cleanup

- **Problem:** the pipeline still has noisy terminal chrome, spinner/subprocess
  collision risk, scattered separator constants, and verbose render chatter.
- **Why it matters:** the terminal output is a user interface; unreadable runs
  slow debugging and make failures harder to triage.
- **Smallest next step:** split console/file formatters, disable spinners around
  streaming subprocess output, centralize separator widths, and demote per-file
  render internals to DEBUG.
- **Acceptance:** a focused run shows no DEBUG/spinner chrome on stdout —
  `uv run python scripts/execute_pipeline.py --project templates/template_code_project --core-only 2>&1 | rg -c 'DEBUG|SPINNER'`
  returns `0` — while the project's `output/logs/pipeline.log` still carries
  timestamped file logs; a rendering test asserts the console formatter strips
  DEBUG that the file formatter retains.
- **Out of scope:** changing JSON report schemas.

### READFILE-SAFE-1 - Consolidate the defensive markdown-read pattern

- **Problem:** the `path.read_text(encoding="utf-8")` + `except (OSError,
  UnicodeDecodeError)` guard is duplicated across many validation/publishing
  modules; `validation/docs/consistency/_shared.py` already exposes a safe
  `read_markdown` helper that most call sites do not use.
- **Why it matters:** divergent error handling means a corrupt file is skipped
  in one linter and crashes another.
- **Smallest next step:** route the byte-identical call sites (start with
  `validation/docs/`) through the shared safe-read helper; do it incrementally
  with tests, not as one sweeping change.
- **Acceptance:** the targeted modules import the shared helper, their tests
  still pass, and a deliberately corrupt fixture is handled identically across
  them.
- **Out of scope:** changing the helper's error-handling contract.

### SIA-HARNESS-2 - Harden the SIA exemplar boundary

- **Problem:** `template_sia` is now public, but fixture replay, validation
  profiles, and optional live-mode guardrails need a second hardening pass.
- **Why it matters:** the public exemplar must demonstrate self-improvement
  harness mechanics without implying autonomous live-code execution in CI.
- **Smallest next step:** tighten SIA docs, add validation profile examples, and
  expand tests around fixture/live-mode separation.
- **Acceptance:** `uv run python -m infrastructure.sia.cli validate projects/templates/template_sia/tasks/mini_classify`
  and focused SIA tests pass.
- **Out of scope:** enabling live LLM calls by default.

### CI-MATRIX-DYNAMIC-1 - Derive the CI project matrix from the generated roster

- **Problem:** the `test-project` matrix in
  [`.github/workflows/ci.yml`](.github/workflows/ci.yml) hard-codes the nine
  `templates/template_*` exemplars; adding or retiring an exemplar requires a
  manual edit kept in sync with `CODEOWNERS` and
  [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).
- **Why it matters:** a hand-maintained matrix drifts from the canonical roster
  (the `CODEOWNERS` gap fixed on 2026-06-05 was exactly this failure mode).
- **Smallest next step:** add a `detect`-style job that emits the exemplar list
  from `infrastructure.project.public_scope` as a matrix output, and have
  `test-project` consume it via `fromJSON`.
- **Acceptance:** adding an exemplar under `projects/templates/` extends the CI
  matrix without editing `ci.yml`'s matrix literal; `CODEOWNERS` drift is caught
  by an existing guard.
- **Out of scope:** restructuring the other CI jobs.

---

## Major

### EVIDENCE-GRAPH-1 - Build a queryable evidence graph

- **Problem:** stage DAGs, artifact registries, claim ledgers, provenance rows,
  and manuscript tokens are adjacent but not unified.
- **Why it matters:** release readiness should answer "which producer, consumer,
  validator, and claim justify this artifact?" without manual cross-reading.
- **Smallest next step:** define a graph schema and generate it for public
  exemplars from existing DAG, registry, provenance, and manuscript-variable
  sources.
- **Acceptance:** every public exemplar artifact has producer, consumer,
  validator, and claim-or-scope metadata in the graph.
- **Out of scope:** live dashboards; this item is the data layer.

### INCREMENTAL-PIPELINE-1 - Add content-hash pipeline skipping

- **Problem:** unchanged projects still rerun expensive stages.
- **Why it matters:** fast no-op runs make the template usable for repeated
  manuscript and validation work.
- **Smallest next step:** hash stage inputs/declared dependencies and skip only
  when the current hash matches a validated previous output manifest.
- **Acceptance:** a repeated pipeline run skips unchanged stages, and mutating a
  stage input invalidates the correct downstream stages.
- **Out of scope:** distributed execution.

### PLUGIN-STAGES-1 - Support user-defined pipeline stages

- **Problem:** projects with specialized methods currently need bespoke scripts
  or core changes to add pipeline behavior.
- **Why it matters:** a template should be extensible without weakening the core
  DAG contract.
- **Smallest next step:** add a schema-validated plugin-stage declaration with a
  fixture plugin stage in tests.
- **Acceptance:** the fixture plugin stage runs in CI without modifying core
  stage definitions.
- **Out of scope:** arbitrary unvalidated shell hooks.

### REPRO-BUNDLE-1 - Produce hermetic release bundles

- **Problem:** release artifacts are validated, but the reproduction envelope is
  spread across lockfiles, manifests, logs, and docs.
- **Why it matters:** readers should be able to verify a release from a clean
  checkout with one bundle and one command.
- **Smallest next step:** bundle lockfile, artifact manifest, hashes, generated
  facts, and reproduction commands for one public exemplar.
- **Acceptance:** bundle verification passes from a clean checkout.
- **Out of scope:** guaranteeing third-party service availability.

### DASHBOARD-1 - Add a local release-readiness dashboard

- **Problem:** CI status, coverage trends, evidence graph status, docs lint, and
  release metadata are scattered across logs and generated files.
- **Why it matters:** maintainers need a quick local view before tagging.
- **Smallest next step:** generate a static dashboard from existing JSON/Markdown
  artifacts with no network calls.
- **Acceptance:** the dashboard builds locally and renders pipeline state,
  coverage trends, evidence graph status, and release readiness.
- **Out of scope:** hosted services or authenticated web apps.

---

## Known divergences from `CHANGELOG.md`

None open. If a new drift appears between [`CHANGELOG.md`](CHANGELOG.md),
`TO-DO.md`, generated facts, or `.github/workflows/ci.yml`, fix forward and
record the current source of truth here instead of rewriting shipped changelog
entries.

---

## Conventions

- Backlog IDs are stable. Use them in commit messages when closing related
  work; do not silently reuse retired IDs for new work.
- **ID scheme:** `<AREA>-<SLUG>-<N>`, where `AREA` names the surface — `GH`
  (GitHub workflows/CI), `ARCH` (architecture/test rules), `LOG` (logging), `AI`
  (Active Inference exemplar), `SIA` (SIA exemplar), `DEP` (dependencies), `FMT`
  (rendering formats), `COVERAGE`/`READFILE`/`CI-MATRIX` (named gates/patterns),
  `EVIDENCE`/`INCREMENTAL`/`PLUGIN`/`REPRO`/`DASHBOARD` (major capabilities), and
  `TODO` (backlog hygiene itself). `N` is a monotonic counter within that area.
- Every active item must include a problem, why it matters, smallest next step,
  acceptance check, and out-of-scope boundary.
- Completion requires evidence from a command, file diff, or generated artifact;
  do not check off items from intention.
- Re-baseline measured facts instead of copying old numbers from this file.
- Keep private or rotating project names out of public docs; link to
  [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
  for public scope.
- Preserve the no-mocks testing policy, project coverage floors, and generated
  artifact guard when closing backlog items.

## See also

- [`CHANGELOG.md`](CHANGELOG.md) - historical release notes
- [`docs/development/roadmap.md`](docs/development/roadmap.md) - release
  direction and long-horizon themes
- [`docs/development/coverage-gaps.md`](docs/development/coverage-gaps.md) -
  measured infrastructure coverage gaps
- [`.github/AGENTS.md`](.github/AGENTS.md) - CI gates and local parity commands
