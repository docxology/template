# template_autopoiesis

> **Public exemplar** — DOI forthcoming

A combinatoric **grammar** that deterministically generates whole runnable projects — `src/`, `tests/`, `scripts/`, and `manuscript/` — one level past a manuscript generator.

## Use This Template

This template is for anyone who needs to **generate runnable project trees deterministically**:
- A combinatoric grammar that emits whole projects (src/, tests/, scripts/, manuscript/)
- Children that pass their own `pytest --cov 90` gate with real audited kernels
- Recompute verification (never trust recorded hashes)
- A falsifiable honesty manifest against green-by-construction theater

It extends `template_madlib` one level up: from generating *a manuscript* to generating *a project that generates a manuscript*.

## Configuring from this template

Edit `manuscript/config.yaml`:
- The `autopoiesis:` block controls the grammar (slots, options, seed, deps)
- The `paper:` block controls publication metadata
- The `analysis:` block controls which scripts run on render

See [`SYNTAX.md`](SYNTAX.md) for grammar syntax, [`config.yaml.example`](manuscript/config.yaml.example) for a fork-safe starting point.

## Template integrity

This project is a **canonical template exemplar**. To use it:
1. Fork or copy the `projects/templates/template_autopoiesis/` directory
2. Edit `manuscript/config.yaml` with your own grammar and metadata
3. Run `uv sync && uv run pytest` to verify

Standalone usage is documented in [`STANDALONE.md`](STANDALONE.md).

---

> **Status:** 410 tests · 90.17% coverage · Public exemplar · DOI forthcoming

---

## What it does

```mermaid
flowchart LR
    G[Grammar] --> S[Seeded spec.json]
    S --> M[Byte-stable materialize]
    M --> V[Recompute-verify from disk]
    V --> Q[QR seal]
```

The spine:

1. **Grammar** — defined in `manuscript/config.yaml` under `autopoiesis:`. Slots × options = archetypes.
2. **Expand** — deterministic SHA-256-based selection, no entropy source.
3. **Materialize** — writes a complete child project to `output/children/child_{domain}_{spec_hash}/`.
4. **Verify** — recomputes tree hash from disk and checks against `provenance.json`.
5. **Seal** — embeds spec hash + tree hash as a QR code in `seal.json`.

The dominant failure mode of project generators — **green-by-construction test theater** — is defeated by:

- Analytic ground-truth primitive kernels (5 domains, 8 kernels)
- Mutation meta-gate (`test_meta_teeth.py`): stub `run_analysis` must *fail*
- Recompute verifier: hash derived from disk, never cached

---

## Drive it

```bash
# Expand the grammar to a spec
uv run python scripts/autopoiesis.py expand

# Materialize a child project
uv run python scripts/autopoiesis.py materialize --out-root output/children

# Verify a child
uv run python scripts/autopoiesis.py verify output/children/child_optimization_XXXX

# Realize one child per domain (smoke test)
uv run python scripts/realize_archetypes.py

# Full realize + verify pipeline
uv run python scripts/realize_child_full.py
```

---

## Render the manuscript

```bash
# Generate figures
uv run python scripts/01_generate_manuscript_assets.py

# Generate cover art
uv run python scripts/generate_cover_art.py

# Generate manuscript variables
uv run python scripts/z_generate_manuscript_variables.py

# Full pipeline (from repo root)
uv run python scripts/execute_pipeline.py --project templates/template_autopoiesis --core-only
```

> **Chrome / Puppeteer note:** PDF rendering uses the shared `infrastructure/rendering` pipeline and requires Chrome/Chromium. Child projects render their own tests only — PDF rendering of child manuscripts is not supported.

---

## Determinism

Given the same `grammar_hash` and `seed`, every output is bit-for-bit identical on the same platform:

- All slot selections use `_digest_index` (SHA-256, no `random.random()`)
- Tree hash computed over sorted `(path, content_hash)` pairs
- Provenance JSON serialized with `sort_keys=True`

Verified by `test_materialize.py::test_materialize_tree_hash_stable` and `test_property_invariants.py`.

---

## Build

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
    --cov=projects/templates/template_autopoiesis/src \
    --cov-fail-under=90 -q
```
