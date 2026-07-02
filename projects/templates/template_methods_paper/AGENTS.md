# A Domain Language for Specifying Controlled Methods — agent guide

**This is an active project** in the `projects/` directory, discovered and
executed by infrastructure discovery functions. Public exemplar roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars).
Publication DOI layout:
[`docs/guides/zenodo-doi-strategy.md`](../../../docs/guides/zenodo-doi-strategy.md).
Manuscript semantics:
[`docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md).

Decision memory and verifier hardening follow
[`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md):
use nearby `WHY:` comments only for surprising local choices, keep volatile
counts generated, and add negative controls for verifier-like gates.

This exemplar demonstrates the **methods paper** archetype: the manuscript's
subject is a controlled-method specification domain language
(`src/methods_dsl/`) itself, not results produced by running one. The
vocabulary generalizes BPL (Biology Programming Language,
https://gitlab.com/bota-biosciences-public/bpl-code) — an upstream reference
for encoding controlled-system protocols as programs with staged validation
and deterministic compilation — from wet-lab protocols to any controlled
procedure.

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/methods_dsl/` (domain) | Pure dataclasses and functions — **no** plotting, no file I/O, **no** `infrastructure` imports except the one sanctioned exception (`_logging.py`) |
| `scripts/` | Thin orchestrators; may import `infrastructure/` and `src/`; the only place matplotlib + file writes live |
| Live counts | Link [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md); **do not** hardcode measured test totals or coverage % |

The boundary is enforced by `check_project_src_infrastructure_boundary` via
`scripts/check_template_drift.py --strict` and
[`manuscript/layer_contract.yaml`](manuscript/layer_contract.yaml).

## Configuration as the source of truth

`manuscript/config.yaml` is the configuration single source of truth for
paper title, authors, keywords, version, and publication metadata; it is
mirrored by a sanitized
[`manuscript/config.yaml.example`](manuscript/config.yaml.example) with the
same top-level sections. The controlled vocabulary (units, step kinds,
targets, gate order) is declared in code
(`src/methods_dsl/units.py`, `vocabulary.py`, `validation.py`), not
configuration — `config.yaml`'s `dsl` block documents that surface for
readers without driving it.

## Key capabilities

- **Controlled-method model** (`src/methods_dsl/model.py`): `Method`,
  `Step`, `Resource`, `Parameter`, constructed directly as frozen
  dataclasses rather than parsed from text.
- **Dimensional safety** (`units.py`): `Quantity` arithmetic across
  incompatible dimensions raises `DimensionError`.
- **Four staged validation gates** (`validation.py`): structural, semantic,
  plan, target — `run_all_gates` runs them in a fixed, short-circuiting
  order.
- **Deterministic compiler** (`compiler.py`): `compile_method` always
  produces the same `Plan.plan_hash` for the same `Method`.
- **Thin analysis script**: [`scripts/methods_analysis.py`](scripts/methods_analysis.py)
  compiles both worked examples (`PBSPreparation`, `SensorCalibrationSweep`),
  runs every gate, writes export/report artifacts and one figure to
  `output/`, and prints output paths for manifest collection.

## Run via the template monorepo

```bash
# From the repository root — run the methods analysis pipeline (thin orchestrator)
uv run python template_methods_paper/scripts/methods_analysis.py
# Writes output/data/*, output/reports/*, and output/figures/step_counts.png
```

## Testing

```bash
# Run project tests with the 90% coverage gate (configuration source of truth: pyproject.toml)
uv run pytest template_methods_paper/tests \
    --cov=template_methods_paper/src --cov-fail-under=90
```

Live test count and achieved coverage:
[`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md) — do not
copy the numbers here.

## Advisory research overlays (validation inputs, not autonomous agents)

- [`domain_profile.yaml`](domain_profile.yaml) — declares the `methods_dsl`
  domain, preferred outputs, review gates, source policy, and artifact
  expectations.
- [`experiment_plan.yaml`](experiment_plan.yaml) — declares the worked-example
  conditions, the primary metric, and expected figures/tables.
- [`data/claim_ledger.yaml`](data/claim_ledger.yaml) — registers sourced
  numeric claims for evidence-registry validation.

## Protocol for AI agents

**Critical Directive**: Before modifying this project, reference the rules in
`docs/`:

- [`docs/agent_instructions.md`](docs/agent_instructions.md) — operational constraints.
- [`docs/testing_philosophy.md`](docs/testing_philosophy.md) — zero-mock policy, before touching any test.
- [`docs/architecture.md`](docs/architecture.md) — the thin-orchestrator boundary and BPL pipeline correspondence, before altering `scripts/`/`src/`.


## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-methods-paper/SKILL.md`](.agents/skills/template-methods-paper/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

## See Also

- [Root projects AGENTS.md](../../AGENTS.md#permanent-canonical-exemplars) — public exemplar roster.
- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md).
- [`manuscript/SYNTAX.md`](manuscript/SYNTAX.md) — Pandoc citation/cross-reference syntax.
- [`src/AGENTS.md`](src/AGENTS.md) / [`src/methods_dsl/AGENTS.md`](src/methods_dsl/AGENTS.md) — DSL library API reference.
- [`TODO.md`](TODO.md) — template-status gaps and improvement ladder.
