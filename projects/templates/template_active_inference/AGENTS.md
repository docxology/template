# AGENTS.md - template_active_inference

Public Active Inference exemplar with coupled analytical, simulation, GNN,
ontology, Lean, and sheaf-manuscript tracks. Keep this file as the project
routing layer; put directory-specific contracts in the nearest child
`AGENTS.md`.

## Ground Truth

| Surface | Source of truth |
| --- | --- |
| Pipeline track gates | [`tracks.yaml`](tracks.yaml) |
| Manuscript sheaf registry | [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) |
| IMRAD section matrix | [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml) |
| Coverage styling/report inputs | [`manuscript/sheaf/coverage.yaml`](manuscript/sheaf/coverage.yaml) |
| Figure registry, captions, alt text | [`figures.yaml`](figures.yaml) |
| pymdp/SI run config | [`pymdp.yaml`](pymdp.yaml) |
| Open follow-up scope | [`TODO.md`](TODO.md) |

Generated counts and claim numbers belong in
`output/data/manuscript_variables.json` and hydrated manuscript output, not in
hand-authored prose.

## Where To Look

| Task | Start here | Notes |
| --- | --- | --- |
| Manuscript section edits | [`manuscript/AGENTS.md`](manuscript/AGENTS.md) | Edit fragments under `manuscript/sections/imrad/`; numbered main files are mostly composed. |
| Sheaf registry/composition | [`src/manuscript/sheaf/AGENTS.md`](src/manuscript/sheaf/AGENTS.md) | Registry, manifest, coverage, generated renderers, and semantic checks. |
| Analytical formulas | [`src/analytical/AGENTS.md`](src/analytical/AGENTS.md) | Bernoulli K=2, MI/FE/EFE decomposition, invariants, sweep I/O. |
| Simulation/SI harness | [`src/simulation/AGENTS.md`](src/simulation/AGENTS.md) | pymdp config/runtime, SI T-maze, graph-world traces, deterministic run logs. |
| GNN parsing/concordance | [`src/gnn/AGENTS.md`](src/gnn/AGENTS.md) | Parser/model/concordance for `gnn/*.gnn.md`. |
| Ontology bindings | [`src/ontology/AGENTS.md`](src/ontology/AGENTS.md) | Nested `terms:` flattening and cross-track naming contract. |
| Output gates | [`src/gates/AGENTS.md`](src/gates/AGENTS.md) | Validation facade, output/manuscript checks, claim ledger, Lean gate. |
| Artifact paths (SSOT) | [`src/contracts/AGENTS.md`](src/contracts/AGENTS.md) | Promoted/variable/gate artifact path registry. |
| Promoted roadmap artifacts | [`src/roadmap_tracks/AGENTS.md`](src/roadmap_tracks/AGENTS.md) | Toy sweep, formal interop, integration audit, canonical sheaf tracks. |
| Visual outputs | [`src/visualizations/AGENTS.md`](src/visualizations/AGENTS.md) | Figure registry/style/generator contracts. |
| Thin orchestration scripts | [`scripts/AGENTS.md`](scripts/AGENTS.md) | Scripts delegate business logic to `src/`. |
| Tests and fixtures | [`tests/AGENTS.md`](tests/AGENTS.md) | Project suite; gate-specific tests have their own child file. |

## Regeneration Order

Use this order when changing generated evidence or manuscript claims:

```bash
uv run python scripts/generate_toy_sweep_tracks.py
uv run python scripts/generate_formal_interop_tracks.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/generate_sheaf_tracks.py
uv run python scripts/z_generate_manuscript_variables.py
```

Then compose/render or validate as needed. `scripts/05_copy_outputs.py --project
templates/template_active_inference` is the root-copy step from the parent
template checkout when copied-root output parity matters.

## Commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/check_documentation_contract.py --check
uv run python scripts/generate_method_inventory.py --check
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/validate_outputs.py
```

Simulation smoke:

```bash
uv run python scripts/simulate_si_tmaze.py --seed 0 --mode state_inference
uv run python scripts/compute_statistics.py
```

## Contracts

- Scripts stay thin; put analytical, simulation, visualization, sheaf, and gate
  logic under `src/`.
- Keep current publication claims confined to deterministic toy artifacts unless
  new measured outputs are generated and validated.
- Do not hand-edit copied/generated output under `output/`; regenerate from the
  source registries and scripts.
- When a GNN model, ontology term, analytical symbol, or simulation artifact
  changes, update the matching track and run the relevant concordance/gate tests
  instead of fixing one lane in isolation.
- Edit decision memory and verifier notes according to
  [`../../../docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md):
  nearby `WHY:` comments only for surprising local choices, generated counts for
  volatile facts, and negative controls for verifier-like gates.


## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-active-inference/SKILL.md`](.agents/skills/template-active-inference/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

## Parent Docs

- Template root: [`../../../AGENTS.md`](../../../AGENTS.md)
- Publishing guide: [`../../../docs/guides/publishing-guide.md`](../../../docs/guides/publishing-guide.md) · Publishing module reference: [`../../../infrastructure/publishing/README.md`](../../../infrastructure/publishing/README.md) · Archival targets: [`../../../docs/maintenance/archival-targets.md`](../../../docs/maintenance/archival-targets.md)
- Zenodo DOI strategy: [`../../../docs/guides/zenodo-doi-strategy.md`](../../../docs/guides/zenodo-doi-strategy.md)
