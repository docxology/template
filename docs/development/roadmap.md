# Development Roadmap

This roadmap documents the evolution of the Research Project Template
infrastructure. Architecture details:
[`architecture.md`](../core/architecture.md) and
[`workflow.md`](../core/workflow.md).

**Last verified:** 2026-07-17. The current root package/release boundary is
documented in [`release-boundary.md`](../maintenance/release-boundary.md);
measured metrics defer to
[`TO-DO.md`](../../TO-DO.md) and
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md)
unless this file is re-measured.

> **Release-boundary note:** the current checkout is unreleased relative to the
> `[Unreleased]` notes. The root package/tag boundary is `3.5.1`/`v3.5.1`; the
> separately published standalone `v1.0.1` entry is not treated as the root
> package's next release. See [`release-boundary.md`](../maintenance/release-boundary.md).

## Completed Releases

### v3.4.0 — Public Template Scope and Release Baseline (2026-06-12)

- published the `v3.4.0` release and resolved the prior pending-tag gap
- rebaselined public exemplar scope to nine tracked templates under
  `projects/templates/`
- closed the v3.3 follow-up backlog sweep and moved live measured facts into
  generated docs and `TO-DO.md`
- see [`CHANGELOG.md`](../../CHANGELOG.md) for the full entry

### v3.3.1 — DOCX Completion and Reproducible Exemplar Outputs (2026-06-07)

- completed Pandoc DOCX rendering so output embeds figures and resolves
  cross-references (`infrastructure/rendering/pipeline.py`)
- ran a deep per-exemplar quality pass across the eight tracked public templates
  and completed + cross-linked sidecar publication metadata for all nine
- reconciled the generated project-scope collection count in
  [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md) to 216
- committed refreshed rendered `output/` artifacts for the public exemplars
  alongside source so the repo ships reproducible, inspectable deliverables
- see [`CHANGELOG.md`](../../CHANGELOG.md) for the full entry

### v3.3.0 — Deterministic Evidence and Anti-Hallucination Infrastructure (2026-06-07)

- added reference-existence verification
  (`infrastructure/reference/verification`) — a deterministic anti-hallucination
  gate resolving each cited reference against Crossref → OpenAlex / arXiv
  (offline-first, opt-in live, SQLite cache)
- added an AI-writing fingerprint detector
  (`infrastructure/validation/content/ai_writing.py`, `validation.cli prose-quality`)
- shipped the evidence graph (EVIDENCE-GRAPH-1), reproduction bundle
  (REPRO-BUNDLE-1), release-readiness dashboard (DASHBOARD-1), pipeline plugin
  stages (PLUGIN-STAGES-1), and incremental pipeline skipping
  (INCREMENTAL-PIPELINE-1) — all opt-in, default plan unchanged
- parallelized CI infrastructure tests (`pytest-xdist -n auto`) and derived the
  `test-project` matrix dynamically from `public_scope` (CI-MATRIX-DYNAMIC-1)
- quieted terminal logging (LOG-CLEAN-1), consolidated the safe markdown reader
  (READFILE-SAFE-1), and ran documentation-accuracy passes across `docs/` and
  infrastructure `{SKILL,README,AGENTS}.md`
- see [`CHANGELOG.md`](../../CHANGELOG.md) for the full entry

### v3.2.0 — Format, Logging, and Exemplar Hardening (2026-06-04)

- added optional Pandoc-backed DOCX/EPUB rendering with per-format toggles
  (default off)
- extended the Active Inference validation spine with producer completeness,
  stale-artifact checks, and dependency graph v2
- hardened the public SIA harness boundary and re-baselined coverage gaps
- closed GitHub supply-chain hygiene (SHA-pinned actions, `actionlint` gate,
  guarded Dependabot automerge) and the XML-parser policy
- see [`CHANGELOG.md`](../../CHANGELOG.md) for the full entry

### v3.1.0 — Public Exemplar / Validation-Spine Release (2026-05-30)

- added the sixth public exemplar, `projects/templates/template_sia/`, plus the
  reusable `infrastructure.sia` harness and validation docs
- promoted the first Active Inference validation-spine tracks:
  `provenance`, `reproducibility`, and `counterexample`
- refreshed public project signposting to `projects/templates/...` and checked
  folder-level `AGENTS.md` / `README.md` coverage across public exemplars
- hardened public project coverage orchestration by pinning subprocess coverage
  behavior across project virtual environments
- shipped curated release notes and a `3.1.0` metadata bump

> **Roster note (post-`v3.1.0`):** the git-tracked public exemplar set under
> `projects/templates/` has since grown beyond the six referenced above —
> `template_autoscientists`, `template_newspaper`, and `template_textbook`
> were added (each double-published as a standalone GitHub repo + Zenodo DOI).
> The authoritative, always-current count and names live in
> [`docs/_generated/active_projects.md`](../_generated/active_projects.md) and
> [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md) —
> consult those rather than this historical release log.

### v3.0.0 — Production / Stable (2026-02-22)

- mypy strict adopted as the baseline gate for `infrastructure/` (live
  counts in [`TO-DO.md`](../../TO-DO.md))
- Ruff format enforcement
- Security hardening: Bandit MEDIUM+ gate in CI; pip-audit blocking since **v0.7.2**
  (ignore list + retries — see [`CHANGELOG.md`](../../CHANGELOG.md))
- Dockerfile modernised to `python:3.12` + `uv`

### v2.x — Foundation Series (2025–2026)

| Release | Theme |
| ------- | ----- |
| `v2.0.0` | Two-layer architecture, thin orchestrator pattern, declared DAG pipeline, multi-project support |
| `v2.1.0` | Unified intelligent logging — `ProjectLogger`, structured format, `log_operation()`, `format_duration()` |
| `v2.1.1` | CI Zero-Mock gate (`verify_no_mocks.py`); mock/fake patterns eliminated from suite |
| `v2.2.0` | Orchestration hermeticity — script discovery, `get_subprocess_env()`, hermetic subprocess env |
| `v2.3.0` | Type safety — TypedDicts for config, `ResolvedTestingConfig`, `ProjectInfo` dataclass |
| `v2.4.0` | Test isolation — real `tmp_path` + env-isolation fixtures (pytest's `monkeypatch` fixture remains permitted by the no-mocks policy and is still used for boundary substitution and env isolation; it was not eliminated) |
| `v2.5.0` | Structured log assertions — `caplog`-based, `log_parser.py` |
| `v2.6.0` | Ruff lint remediation: 710 → 0 errors across `infrastructure/`, `scripts/`, `tests/` |
| `v2.7.0` | Type narrowing & mypy baseline: 100 → 0 errors across `core/` |
| `v2.8.0` | Error reporting & resilience — typed `InfraError` constants, standardized error format |
| `v2.9.0` | Documentation parity — `python3` → `uv run python`, auto-generated API reference |

### v0.6.0 — Desloppify Code-Health Campaign (2026-03-10)

161-commit systematic blind-review campaign across all infrastructure
packages:

- Import hygiene (unused imports, `sys.path` mutations, `TYPE_CHECKING` guards)
- Exception narrowing (specific types, context restoration, no silent swallowing)
- Dead-code removal (`coverage_reporter.py`, stub wrappers, passthrough methods)
- Type annotations modernised (legacy `typing` → built-in generics)
- API surface consolidation (`OllamaClientConfig`, `PerformanceMetrics`, `ProjectLogger`)
- Bug fixes (inverted bool, stall detection, path bugs, broken imports)
- Structural: eliminated `core.py` hub, extracted `_build_stage_list`, broke circular dep
- Logging noise reduction; docstring bloat; test name collisions resolved

---

## Planned

The active planning surface is [`TO-DO.md`](../../TO-DO.md). It is intentionally
more specific than this roadmap and now groups work as **Minor**, **Medium**,
and **Major**.

### Ongoing — Hygiene and Backlog Accuracy

- keep `TO-DO.md`, generated facts, release metadata, and public-scope docs
  synchronized after each release or major verifier pass
- keep forkability checks and regression pins green, finish the active-inference
  fixed-point cluster, and only then add new scientific surface

> The GitHub supply-chain hygiene items (SHA-pinned actions, `actionlint`, safe
> Dependabot automerge) shipped in `v3.2.0`; terminal logging cleanup
> (LOG-CLEAN-1), the safe markdown-read helper (READFILE-SAFE-1), and the dynamic
> CI project matrix (CI-MATRIX-DYNAMIC-1) shipped in `v3.3.0`. See Completed
> Releases above.

### Next (open backlog)

The authoritative open backlog lives in [`TO-DO.md`](../../TO-DO.md). Current
themes are verifier-first maintenance items: generated-source reconciliation,
combined public coverage isolation, publication safety, hostile-input handling,
runtime support, and faster
deterministic feedback.

### Next Generation (vision)

> The prior vision list — evidence graph (EVIDENCE-GRAPH-1), incremental pipeline
> (INCREMENTAL-PIPELINE-1), plugin architecture (PLUGIN-STAGES-1), hermetic
> release bundles (REPRO-BUNDLE-1), and local dashboard (DASHBOARD-1) — **all
> shipped in `v3.3.0`** (opt-in/default-off). See Completed Releases above. The
> live follow-up work for these capabilities is tracked in the open backlog
> above and in [`TO-DO.md`](../../TO-DO.md); new long-horizon vision items should
> replace this note as they are defined.

---

## Next Up

Use [`TO-DO.md`](../../TO-DO.md) as the authoritative backlog and live snapshot.
The current open top items are:

- `SECURITY-OWNERSHIP-1`
- `SECURITY-PRIVATE-PROMOTION-1`
- `COVERAGE-BASELINE-1`
- `RUNTIME-SUPPORT-1`
- `CI-ERGONOMICS-1`

Shipped and not re-tracked here: the GitHub supply-chain hygiene set
(`GH-PIN-1`, `GH-ACTIONLINT-1`, `GH-AUTOMERGE-1`), `LOG-CLEAN-1`,
`READFILE-SAFE-1`, `CI-MATRIX-DYNAMIC-1`, `FMT-BUNDLE-1`, `AI-SPINE-V2`,
`COVERAGE-REBASE-1`, and the five `v3.3.0` Major capabilities
(`EVIDENCE-GRAPH-1`, `INCREMENTAL-PIPELINE-1`, `PLUGIN-STAGES-1`,
`REPRO-BUNDLE-1`, `DASHBOARD-1`), plus pip-audit blocking CI, Bandit LOW triage,
docs-lint CI, the per-project test runner, and SIA public-exemplar promotion. See
[`CHANGELOG.md`](../../CHANGELOG.md) for the release history.

---

## Quality Metrics

Authoritative counts and gate outputs live in the **Live state snapshot**
table in [`TO-DO.md`](../../TO-DO.md) (re-baseline there after substantive
changes). This roadmap avoids duplicating numbers that drift between audits.

| Topic | Where to verify |
| ----- | ---------------- |
| mypy / ruff / Bandit / pip-audit / health | [`TO-DO.md`](../../TO-DO.md) |
| CI wiring | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [`.github/AGENTS.md`](../../.github/AGENTS.md) |
| Coverage gaps | [`coverage-gaps.md`](coverage-gaps.md) |

---

## See Also

- **[Contributing](contributing.md)** — how to contribute to the template
- **[`../../TO-DO.md`](../../TO-DO.md)** — active backlog with acceptance
  criteria
- **[`../../CHANGELOG.md`](../../CHANGELOG.md)** — historical release notes
