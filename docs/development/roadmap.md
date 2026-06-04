# Development Roadmap

This roadmap documents the evolution of the Research Project Template
infrastructure. Architecture details:
[`architecture.md`](../core/architecture.md) and
[`workflow.md`](../core/workflow.md).

**Last verified:** 2026-05-31 (post-`v3.1.0` backlog refresh; measured
metrics defer to [`TO-DO.md`](../../TO-DO.md) and
[`docs/_generated/canonical_facts.md`](../_generated/canonical_facts.md)
unless this file is re-measured)

## Completed Releases

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
> were added (each double-published as a standalone GitHub repo + Zenodo DOI),
> bringing the current public exemplar roster to **nine**. The authoritative,
> always-current count and names live in
> [`docs/_generated/active_projects.md`](../_generated/active_projects.md) and
> [`docs/_generated/canonical_facts.md`](../_generated/canonical_facts.md) —
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
| `v2.4.0` | Monkeypatch elimination — real `tmp_path` + env-isolation fixtures |
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

### v3.1.x — Hygiene and Backlog Accuracy

- keep `TO-DO.md`, generated facts, release metadata, and public-scope docs in
  sync after each release
- close GitHub hygiene items: SHA-pinned actions, `actionlint`, and safe
  Dependabot automerge
- land the Active Inference gate-cache follow-up without changing the immutable
  `v3.1.0` tag

### v3.2.0 — Format, Logging, and Exemplar Hardening

- finish terminal logging cleanup and preserve verbose file logs
- add optional DOCX/EPUB rendering with per-format toggles
- extend the Active Inference validation spine with producer completeness,
  stale-artifact checks, and dependency graph v2
- harden the public SIA harness boundary and re-baseline coverage gaps

### Next Generation (vision)

- **Evidence graph**: unify pipeline DAG, artifact registry, claim ledger,
  provenance, and manuscript tokens into one queryable release-readiness graph
- **Incremental pipeline**: skip unchanged stages via content hashing
- **Plugin architecture**: user-defined pipeline stages with schema validation
- **Hermetic release bundles**: lockfile, artifact manifest, hashes, and
  reproduction commands from a clean checkout
- **Local dashboard**: static, no-network view of pipeline status, coverage
  trends, evidence graph status, and release readiness

---

## Next Up

Use [`TO-DO.md`](../../TO-DO.md) as the authoritative backlog and live snapshot.
The current top items are:

- **Minor:** `GH-PIN-1`, `GH-ACTIONLINT-1`, `GH-AUTOMERGE-1`,
  `AI-GATE-CACHE-1`
- **Medium:** `LOG-CLEAN-1`, `FMT-BUNDLE-1`, `AI-SPINE-V2`,
  `SIA-HARNESS-2`, `COVERAGE-REBASE-1`
- **Major:** `EVIDENCE-GRAPH-1`, `INCREMENTAL-PIPELINE-1`,
  `PLUGIN-STAGES-1`, `REPRO-BUNDLE-1`, `DASHBOARD-1`

Shipped elsewhere and not re-tracked here: pip-audit blocking CI, Bandit LOW
triage, docs-lint CI, the per-project test runner, SIA public-exemplar
promotion, and the first Active Inference validation-spine tracks. See
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
