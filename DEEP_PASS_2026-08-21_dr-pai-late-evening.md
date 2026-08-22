# Deep-pass session report — Dr. PAI (ox-alpha), 2026-08-21 late evening

Independent re-run of the deep-assessment mission from HEAD `380959b9c` (main).
Nothing taken on trust from prior sessions; every result below was measured
live in this session.

## Context

Arrived to a tree with concurrent-session work in flight (rendering slides
fixes, `_python_env.py`/`env_deps.py` refactor introducing
`infrastructure/core/runtime/_tools.py`, template_active_inference output
regeneration). All such files were left untouched per mission hard rules.

## Root-cause finding this session confirmed

**git_hook_smoke timeout failures were caused by the global pytest-timeout,
not the subprocess caps.** Measured component timings on this checkout:

| Component | Measured |
| --- | --- |
| `tracked_public_output_leaks()` | 37.6 s |
| full `check_tracked_generated_artifacts.py` | 41-45 s |
| `tracked_secret_findings()` | 23.2 s |
| global `pyproject.toml` `timeout = 10` (thread) | fires first |

Consequence: raising only the subprocess cap (30->120 s) could not fix the
failure; per-test `@pytest.mark.timeout` overrides are required. That fix is
now committed as `1b6074262` ("re-apply pytest timeouts ... prior edit lost to
concurrent-session file race") — this session independently verified the
committed state is effective:

- `pytest tests/infra_tests/git_hook_smoke/ -q --no-cov`: **14 passed** across
  ~40 consecutive runs spanning system-load swings (5-57 s wall). Two residual
  failures observed mid-session were diagnosed:
  1. A transient guard failure naming rotating
     `template_active_inference/output/manuscript/*.md` offenders while the
     concurrent session's regeneration was rewriting tracked output files.
     Direct probe of the named paths showed all four matcher predicates false;
     the standalone guard passed immediately after. Race, not a code defect.
  2. One run failing `test_validation_cli_help_returns_zero` with an
     `IndentationError` inside `infrastructure/core/runtime/_python_env.py`
     line 200 — a broken intermediate state of the concurrent session's
     in-flight edit (`import shutil` removed, replacement indented wrongly).
     Self-resolved when that session completed its edit; CLI help now exits 0.

## Gate battery re-measured this session

| Gate | Result |
| --- | --- |
| Ruff lint (full public lint surface) | PASS |
| Ruff format check (public surface) | 2 pre-existing dirty rendering files would reformat (concurrent session's); clean otherwise |
| Mypy (1559 source files) | PASS |
| No-mocks lexical + inventory ceiling 0 | PASS (clear; debt 0) |
| Tracked secrets scan | PASS |
| Confidentiality guards (projects/fonds/rules/tools) | PASS |
| Generated-artifact guard standalone | PASS (~41 s runtime) |
| Template drift `--strict` | PASS |
| Skills check / check-all-exports / api_reference / roster | PASS |
| Backlog contract | PASS (0 errors/warnings) |
| Docs lint cross-links / consistency / doc-pairs | 0 / 0 / 0 |
| Docs lint mermaid | 7 local mmdc per-block 30 s timeouts (environment slowness; matches prior passes) |
| pipeline-smoke infra lane | PASS (exit 0) after timeout fix |
| counts.py --check | FAIL (STALE coverage provenance for template_active_inference) — concurrent session owns the uncommitted source changes; disposition unchanged |

## Dispositions

- Timeout fix (Medium): FIXED and committed (`e4dfce5a9`, `1b6074262`);
  independently verified here end-to-end including root cause.
- Stale COUNTS provenance / mirror-shape strays / branch-behind-origin: remain
  owner/concurrent-session items exactly as recorded in the canonical backlog.
- Majors (M1-M3 in canonical backlog): unchanged scoping; nothing this session
  contradicts them.

## Files changed by this pass

- `DEEP_PASS_2026-08-21_dr-pai-late-evening.md` — this report (only file).

No push performed, per mission rules.
