---
project: humos-template
task: Maximize agentic operability, modularity, and composability of the template package
effort: E5
phase: complete
progress: 24/24
baseline_head: e22c4bb697edc6ae7de204808ecdee590e77f715
iteration: 2-comprehensive-cli-rollout-and-push
mode: algorithm
started: 2026-06-22
updated: 2026-06-22
---

# ISA — HumOS Template Package: Agentic Operability

> Project ISA (system of record). The template is a two-layer research-paper
> pipeline (generic `infrastructure/` Layer 1 + per-project Layer 2) delivered
> across multiple surfaces (CLI, library, scripts, skills, docs). This ISA
> articulates the ideal state where any *agent* — not just a human reading the
> README — can discover, invoke, compose, and verify every capability the
> package exposes, with the same low-friction mental model across all modules.

## Problem

The package is large (569 infrastructure modules, 53 scripts, 10 exemplar
templates) and human-documented well, but its *agent-facing* surface is
uneven. Concretely observed at OBSERVE:

- **No single machine-readable capability catalog.** `infrastructure/skills/discovery.py`
  scans `SKILL.md` descriptors, but there is no one command that emits the full
  set of agent-invocable operations (every `python -m infrastructure.X` CLI, its
  flags, its JSON contract). An agent must read prose to learn what it can call.
- **CLI surface is hand-rolled and non-uniform.** 73 files import `argparse`
  directly; there is no shared CLI scaffold guaranteeing `--json`, `--help`,
  exit-code, and `--dry-run` conventions across modules. Agents cannot assume a
  uniform invocation/parse contract.
- **No MCP server.** MCP appears only as a *client* in `infrastructure/search/deep_research/`.
  The package exposes none of its own capabilities over MCP, the lingua franca
  for agent tool-calling.
- **Composability is implicit.** Public APIs are not uniformly fenced with
  `__all__`/typed contracts; an agent importing a module cannot reliably tell
  the stable surface from internals.
- **Exemplar templates may drift** in structure, making "copy a template and
  go" less deterministic for an agent than it should be.

These are hypotheses to be confirmed/refuted by the OBSERVE reconnaissance
workflow before any are acted on.

## Vision

An agent dropped into this repo runs one discovery command, receives a complete
machine-readable map of every operation (name, module path, CLI invocation,
flags, input/output JSON contract, side effects, idempotency), and can compose
those operations into a pipeline without reading a single paragraph of prose.
Every module feels the same to operate. The euphoric surprise: the package
becomes *self-describing to machines* without losing any of its
human-readability — the same registry that documents it to people is the one
agents query.

## Out of Scope

- Rewriting working business logic for its own sake — improvements must preserve
  behavior and the no-mocks/TDD/coverage gates.
- Changing the two-layer architecture, the thin-orchestrator pattern, or the
  three-tree mirror invariant — these are load-bearing and correct.
- Migrating from `argparse` to Typer/Click wholesale in one pass (high churn,
  high risk) — favor an additive shared scaffold over a rip-and-replace.
- Adding heavy new runtime dependencies to the default install.
- Touching private/local-only projects or anything outside `projects/templates/`.
- Network-dependent or paid features (deep-research, archival deposits) as
  defaults.

## Principles

- **Self-description over documentation.** A capability an agent can enumerate
  and introspect beats one described in prose. (Deutsch: the registry is the
  hard-to-vary explanation of what the system can do.)
- **Uniformity is composability.** When every module obeys the same invocation
  and output contract, composition becomes mechanical rather than bespoke.
- **Additive before destructive.** Prefer new shared scaffolds, registries, and
  adapters over rewrites that risk the existing green gates.
- **Evidence before edit.** Every claimed defect is confirmed with a tool probe
  (file:line) before remediation; every edit is verified after.
- **The gates are the contract.** ruff/mypy/bandit/pytest coverage floors and
  the audit scripts are the regression harness; nothing ships that reddens them.

## Constraints

- Python 3.10–3.12 (CI matrix), Pydantic v2, async-first, strong typing; all
  commands via `uv`.
- No mocks in tests (`pytest-httpserver`, real temp files, real subprocess).
- Coverage floors: infrastructure ≥60%, per-project ≥90%, public-union ≥75%.
- Thin-orchestrator pattern: business logic only in `infrastructure/` or
  `projects/{name}/src/`; scripts coordinate.
- Three-tree mirror + per-folder `AGENTS.md`/`README.md` (audit-enforced).
- Confidentiality invariant: only `projects/templates/*` is git-tracked.
- Forge/Cato unavailable this session (codex ChatGPT-account 401) → inline
  RedTeam substitution per Algorithm Rule 2a.

## Goal

Raise the package's agentic-operability surface so that (a) one command emits a
complete machine-readable capability catalog of all module CLIs and their
contracts, (b) a shared CLI scaffold/convention makes invocation and JSON output
uniform and verifiable, (c) module public APIs are explicitly fenced for safe
composition, and (d) the exemplar templates are structurally consistent — all
delivered as additive, gate-green, behavior-preserving changes verified by tool
probe and recorded in this ISA.

## Criteria

> Seed criteria — the OBSERVE reconnaissance workflow expands this to the E5
> floor with specific, file-anchored, leverage-ranked ISCs before BUILD. IDs
> are stable; recon findings append as ISC-N.

- [x] ISC-1: A single command emits a machine-readable catalog of every invocable `python -m infrastructure.*` operation (probe: `operations-list-json` → 12 ops, valid JSON).
- [x] ISC-2: The catalog includes, per operation, module + invocation + subcommands + exports (probe: jq over manifest).
- [x] ISC-3: Anti: No existing green gate reddens as a result of changes (probe: ruff ✓, mypy ✓, __all__ audit ✓, no-mocks ✓, drift ✓, full infra suite — only pre-existing + load-flaky failures, proven on baseline worktree).
- [x] ISC-4: Anti: No business logic moves into scripts; orchestrators stay thin (probe: diff review — scripts only add docstrings/launcher/enum import).
- [x] ISC-5: Anti: No file outside `projects/templates/` becomes git-tracked (probe: check_tracked_projects.py — guard green).
- [x] ISC-6: Changed/added modules carry mirror partners; all new infra modules have test partners (probe: audit_documentation EXIT=0, no new-file findings).
- [x] ISC-7: Reconnaissance produced a leverage-ranked, file-anchored, adversarially-verified findings set (probe: workflow 68→32 confirmed).
- [x] ISC-8: `scripts/exit_codes.py` names the in-force 0/1/2 contract as an IntEnum without changing any return value (probe: import + value asserts).
- [x] ISC-9: `copy_exemplar/plan_copy/CopyResult` importable from `infrastructure.project` (probe: import).
- [x] ISC-10: `describe-pipeline --format json` derives 12 stages (10 core-only) from pipeline.yaml with clean stdout (probe: jq).
- [x] ISC-11: `main(argv) -> int` standardized on rendering + core CLIs (probe: inspect.signature + main([]) == 1).
- [x] ISC-12: `cli_scaffold.parser_schema` + `--schema` flag emit a JSON parameter contract (probe: pipeline `describe-pipeline --schema`).
- [x] ISC-13: stdio MCP server speaks valid JSON-RPC (initialize/tools/list/tools/call) over real subprocess (probe: subprocess round-trip test).
- [x] ISC-14: Anti: MCP `invoke_cli` refuses non-`infrastructure.*` and unregistered modules; list-form subprocess, no shell (probe: Anvil attack tests + unit tests).
- [x] ISC-15: Anti: No MCP tool corrupts the JSON-RPC stdout stream with log output (probe: Anvil repro, stderr-discarded — 0 parse failures; subprocess test calls describe_pipeline).
- [x] ISC-16: `template_manifest.json` is a derived, in-sync machine-readable template catalog (probe: generator `--check` green).
- [x] ISC-17: `tests/_suite_registry.py` + `_test_selector.py` let agents compose pytest invocations programmatically (probe: select_tests asserts).
- [x] ISC-18: The operations manifest has an ENFORCED drift gate, not just a documented one (probe: `operations-check` wired into `.pre-commit-config.yaml`).
- [x] ISC-19: `docs/architecture/capability-surfaces.md` documents all eight delivery surfaces accurately (no overclaim after Anvil #5 fix) (probe: read + gate-wiring check).
- [x] ISC-20: Every new infra module has no-mocks tests holding the 60% floor (probe: 81 new/touched tests pass; verify_no_mocks green).
- [x] ISC-21: Anti: Cross-vendor audit ran (Anvil, Cato substitute) and every BLOCKER it raised is fixed+verified (probe: Anvil verdict + blocker re-probe).
- [x] ISC-22: Every infrastructure CLI exposes a uniform `schema` introspection emitting clean JSON (probe: 16/16 live `python -m … schema` probes pass).
- [x] ISC-23: Six previously-non-invocable CLIs are now `python -m`-invocable (`__main__.py` added); the operation catalog lists 18 CLIs (probe: operations-list-json count).
- [x] ISC-24: Anti: No test-induced or out-of-scope artifact is committed; changeset confined to infrastructure/scripts/tests/docs/.cursor/.pre-commit/ISA (probe: scope grep — reverted a test-clobbered manuscript table).

## Test Strategy

| isc | type | check | threshold | tool |
|-----|------|-------|-----------|------|
| ISC-1 | functional | catalog command returns valid JSON listing ops | ≥1 op per CLI module | Bash + jq |
| ISC-2 | functional | each entry has module + invocation fields | 100% | jq |
| ISC-3 | regression | gate suite stays green | no new failures | uv run ruff/mypy/pytest, gates |
| ISC-4 | regression | diff introduces no logic into scripts | 0 violations | git diff review |
| ISC-5 | regression | tracked-projects check passes | exit 0 | check_tracked_projects.py |
| ISC-6 | regression | three-tree mirror intact | exit 0 | audit_docs.py Rule 5 |
| ISC-7 | process | findings file exists with evidence + verdicts | present | Read |

## Features

| name | satisfies | depends_on | parallelizable |
|------|-----------|------------|----------------|
| operation_registry (keystone) | ISC-1,2 | — | yes |
| exit_codes enum | ISC-8 | — | yes |
| project copy_exemplar exports | ISC-9 | — | yes |
| describe-pipeline CLI | ISC-10 | — | yes |
| main(argv)->int standardization | ISC-11 | — | yes |
| cli_scaffold + --schema | ISC-12 | main standardization | no |
| MCP server (capstone) | ISC-13,14,15 | operation_registry, describe-pipeline | no |
| template_manifest | ISC-16 | — | yes |
| test suite/selector registries | ISC-17 | — | yes |
| operations drift gate wiring | ISC-18 | operation_registry | no |
| capability-surfaces doc | ISC-19 | all above | no |

## Decisions

- 2026-06-22: Tier = E5 (classifier). ISA home = project ISA at template/ISA.md (persistent identity, E3+ structure mandatory).
- 2026-06-22: Forge/Cato unavailable (codex ChatGPT-account 401 per SessionStart Gate H probe). `forge_unavailable: true`, `cato_unavailable: true`. Substituting inline RedTeam scaled to change per Rule 2a; Anvil (Kimi) remains available as non-Anthropic producer.
- 2026-06-22: User opted into `/workflows` → using a read-only reconnaissance + adversarial-verification Workflow to map all six surfaces and apply FirstPrinciples/RedTeam/Science lenses, rather than blind parallel Agent calls. Edits made by the main loop (verifiable) after findings return.
- 2026-06-22: Criteria seeded, not fully enumerated, at OBSERVE — deliberate: specific ISCs depend on recon findings (ISA is a living articulation; Criteria written OBSERVE→EXECUTE).
- 2026-06-22: User chose full scope (ranks 1–10 incl. MCP capstone) at the E5 pre-BUILD interview gate (AskUserQuestion).
- 2026-06-22: MCP server built dependency-free (stdlib JSON-RPC over stdio) rather than via the `mcp` SDK — keeps the default install untouched and makes it unit-testable without a transport; recorded as a deliberate constraint-honoring choice.
- 2026-06-22 (VERIFY): advisor unavailable (CLAUDECODE blocks nested `claude`) AND Cato unavailable (codex ChatGPT-401). Per Rule 2a v6.5.1, substituted **Anvil (Kimi K2.6, non-Anthropic)** for cross-vendor audit. `advisor_unavailable: true`, `cato_unavailable: true`, `forge_unavailable: true`, `substituted: Anvil cross-vendor audit`.
- 2026-06-22 (VERIFY): Anvil raised 1 BLOCKER (MCP `describe_pipeline` leaked dag-loader log to stdout, corrupting JSON-RPC) + 2 minor (unenforced operations drift gate, doc-link casing). All fixed and re-probed.
- 2026-06-22 (iteration 2): Rolled the uniform `schema` introspection across all 16 remaining CLIs via a 16-agent `/workflows` run; added `__main__.py` to 6 modules (operation catalog 12 → 18). Central verification (not agent self-reports) gated the push: 16/16 live schema probes, CI-scope ruff+mypy clean, bandit MEDIUM+ clean, 253 affected tests pass, all drift/export/no-mocks/confidentiality gates green.
- 2026-06-22 (iteration 2): Scope guard caught a test-induced regression — the full infra suite refreshed a *generated* status table inside `template_active_inference/manuscript/08_methods_sheaf.md` to a degenerate state; reverted it (git-anchored: tree was clean at session start) rather than committing content loss.

## Changelog

- conjectured: a per-call `_quiet_dag_logging()` wrap in the pipeline CLI's `describe_pipeline` was sufficient to keep stdout JSON-clean.
  refuted_by: Anvil cross-vendor audit — the MCP server's `_tool_describe_pipeline` calls `stage_rows()` directly, bypassing that wrap, so the dag-loader's stdout log corrupted the JSON-RPC stream for that one tool (masked by an in-process-only test).
  learned: the stdout-purity guard belongs at the data boundary (`stage_rows`), not at each call site; and any "speaks valid protocol" claim needs a transport-level test that exercises the log-emitting path.
  criterion_now: ISC-15 — no MCP tool may corrupt the JSON-RPC stdout stream, verified by a subprocess test that calls the DAG-loading tool.

## Verification

- ISC-1/2: `uv run python -m infrastructure.skills operations-list-json` → `{"version":1,"operations":[...12...]}`, each with module/invocation/subcommands/exports.
- ISC-3: ruff `All checks passed`; mypy `no issues in 10 files`; `__all__` audit `0 violations`; no-mocks `All tests comply`; full infra suite 7467 passed — the 9 failures = 6 `-n 6` load-flaky (pass serially) + 3 pre-existing (identical failure on baseline worktree e22c4bb).
- ISC-10/12: `describe-pipeline --format json` 12 stages / `--core-only` 10; `--schema` emits parameter JSON.
- ISC-13/14/15: subprocess MCP round-trip (initialize+tools/list+describe_pipeline) all valid JSON; `invoke_cli` refuses `os` and injection attempts (Anvil); stderr-discarded stdout probe = 0 parse failures.
- ISC-16: `generate_exemplar_roster_doc.py --check` → "10 exemplars, doc + manifest in sync".
- ISC-18: `operations-check` hook present in `.pre-commit-config.yaml`; runs green.
- ISC-21: Anvil verdict CONCERNS → all blockers fixed → re-probed clean.
