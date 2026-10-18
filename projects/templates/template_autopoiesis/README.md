# template_autopoiesis

> **Public exemplar** — [DOI: 10.5281/zenodo.21227869](https://doi.org/10.5281/zenodo.21227869)

A combinatoric **grammar** that generates standalone child analysis, primitives,
domain tests, manuscript sources, and provenance from an explicit selected spec.

## When to use this template

Use this template when you need to **generate runnable project trees
deterministically**: a child project with `analysis.py`, `primitives/`,
`tests/`, and `manuscript/`, selected by a seed and explicit grammar filters.
Actual child tests and analysis accompany recomputed provenance and a
structural honesty manifest. It
extends `template_madlib` one level up: from generating *a manuscript* to
generating *a project that generates a manuscript*. If you only need
token-driven manuscript generation without the project-generation layer, use
`template_madlib` directly instead; if you need a manuscript template with no
generative grammar at all, see `template_code_project` or
`template_prose_project`.

Concretely, this template provides:
- A combinatoric grammar that emits standalone numerical child projects
- Children that pass their own `pytest --cov 90` gate with real audited kernels
- Recompute verification (never trust recorded hashes)
- A source-bound structural manifest, plus independently verified child results

## Configuring from this template

Edit `manuscript/config.yaml`:
- The `project_config.autopoiesis:` block controls slots, options, seed, dependencies, and archetype filters
- The `paper:` block controls publication metadata
- The `analysis:` block controls which scripts run on render

See [`SYNTAX.md`](SYNTAX.md) for grammar syntax, [`config.yaml.example`](manuscript/config.yaml.example) for a fork-safe starting point.

## Template integrity

This project is a **canonical template exemplar**. To use it:
1. Fork or copy the `projects/templates/template_autopoiesis/` directory
2. Edit `manuscript/config.yaml` with your own grammar and metadata
3. From the copied project directory inside a template checkout, run `uv sync --locked --extra dev && uv run --locked pytest` to verify the full own suite with its declared platform dependency.

Standalone usage is documented in [`STANDALONE.md`](STANDALONE.md).

---

> **Status:** Public exemplar · [DOI: 10.5281/zenodo.21227869](https://doi.org/10.5281/zenodo.21227869) · test count and coverage move with the code — see the "Publication and rendering" section below (generated from a live measurement) rather than a hand-typed number here.

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

The generator's acceptance controls use:

- Analytic ground-truth primitive kernels (5 domains, 8 kernels)
- Mutation meta-gate (`test_meta_teeth.py`): stub `run_analysis` must *fail*
- Recompute verifier: hash derived from disk, never cached
- Real selected-child domain tests, numerical analysis, and parent-side reference comparisons

`realize_archetypes.py` executes one selected cell per permitted domain;
`realize_child_full.py` executes one manifest-selected child. The current
unfiltered grammar declares 360 nominal cells and 45 effective cells. A five-child
default run provides evidence for its five selected specs. Child PDF rendering
is unsupported. New execution receipts and exports live only under ignored
`output/.pipeline/child_realization/`, preserving historical `output/children/`.
See [the child execution contract](docs/child-execution.md) for custody and limits.

---

## Drive it

```bash
# Expand the grammar to a spec
uv run python scripts/autopoiesis.py expand

# Materialize a child project
uv run python scripts/autopoiesis.py materialize --out-root output/children

# Verify a child
uv run python scripts/autopoiesis.py verify output/children/child_optimization_XXXX

# Check the falsifiable honesty manifest (this template's headline feature)
uv run python scripts/autopoiesis.py honesty

# Execute and independently verify one selected child per permitted domain
uv run python scripts/realize_archetypes.py

# Execute and independently verify one manifest-selected child
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
uv run python scripts/runner/execute_pipeline.py --project templates/template_autopoiesis --mode core
```

> **Chrome / Puppeteer note:** The parent manuscript uses the shared rendering pipeline. Child acceptance executes domain tests and numerical analysis. Child manuscript PDF rendering is unsupported.

---

## Determinism

Given the same grammar, seed, and generator source bytes, generated child source
is deterministic. Runtime timing and coverage receipts reflect actual execution:

- All slot selections use `_digest_index` (SHA-256, no `random.random()`)
- Tree hash computed over sorted `(path, content_hash)` pairs
- Provenance JSON serialized with `sort_keys=True`

Verified by `test_materialize.py::test_materialize_tree_hash_stable` and `test_property_invariants.py`.

---

## Publication and rendering

<!-- PUBLISHING-STATUS:START (generated by infrastructure.publishing.status_report) -->
**Autopoietic Project Generation** · intended v2.0.0 (unreleased) · MIT · Daniel Ari Friedman

Intended release: v2.0.0 — unreleased.
Last published release: v1.0.1. Recorded publication links refer to that release.

Concept DOI: [10.5281/zenodo.21227869](https://doi.org/10.5281/zenodo.21227869) | Last published version DOI: [10.5281/zenodo.21229620](https://zenodo.org/records/21229620) | Repository: [docxology/template_autopoiesis](https://github.com/docxology/template_autopoiesis)

Publishing surface — 20 platforms, 0 published for the intended release:

| Platform | Tier | Status | Reference | Credentials |
| --- | --- | --- | --- | --- |
| zenodo | first-class | 📚 historical reference | [10.5281/zenodo.21227869](https://doi.org/10.5281/zenodo.21227869) | `ZENODO_API_TOKEN` |
| github | first-class | 📚 historical reference | [docxology/template_autopoiesis](https://github.com/docxology/template_autopoiesis) | `GITHUB_TOKEN` |
| arxiv | first-class | ⚪ available | — | — |
| pypi | first-class | ⚪ available | — | `PYPI_TOKEN`, `TESTPYPI_TOKEN` |
| ipfs_pinata | first-class | 📚 historical reference | [https://gateway.pinata.cloud/ipfs/QmanoQUGKKFeYFtd5HRpB4ysE9jVxbzvaWpqgpWu5rRi8V](https://gateway.pinata.cloud/ipfs/QmanoQUGKKFeYFtd5HRpB4ysE9jVxbzvaWpqgpWu5rRi8V) | `PINATA_JWT` |
| ipfs_web3storage | first-class | ⚪ available | — | `WEB3_STORAGE_TOKEN` |
| software_heritage | first-class | ⚪ available | — | — |
| github_pages | first-class | ⚪ available | [docxology/template_autopoiesis](https://github.com/docxology/template_autopoiesis) | `GITHUB_TOKEN` |
| cloudflare_pages | first-class | ⚪ available | — | `CLOUDFLARE_API_TOKEN` |
| netlify | first-class | ⚪ available | — | `NETLIFY_AUTH_TOKEN` |
| huggingface_hub | first-class | ⚪ available | — | `HUGGINGFACE_TOKEN`, `HF_TOKEN` |
| osf | first-class | 📚 historical reference | [https://osf.io/ksmzp/](https://osf.io/ksmzp/) | `OSF_TOKEN` |
| amazon_kdp | documented | 🟡 planned | — | `AMAZON_KDP_EMAIL`, `AMAZON_KDP_PASSWORD` |
| google_play_books | documented | 🟡 planned | — | `GOOGLE_PLAY_BOOKS_SERVICE_ACCOUNT_JSON` |
| gumroad | documented | 🟡 planned | — | `GUMROAD_ACCESS_TOKEN` |
| leanpub | documented | 🟡 planned | — | `LEANPUB_API_KEY` |
| lulu | documented | 🟡 planned | — | `LULU_CLIENT_KEY`, `LULU_CLIENT_SECRET` |
| draft2digital | documented | 🟡 planned | — | `DRAFT2DIGITAL_API_TOKEN` |
| stripe | documented | 🟡 planned | — | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` |
| ingramspark | documented | 🟡 planned | — | `INGRAMSPARK_CLIENT_ID`, `INGRAMSPARK_CLIENT_SECRET` |

_Keywords: autopoiesis, combinatoric grammar, deterministic generation, project synthesis, reproducible research, infrastructure automation._

_Status legend: ✅ published (durable identifier recorded in `config.yaml`) · 🔵 reserved (identifier reserved but not yet registered by final publication) · 📚 historical reference (last published release; not intended-version publication evidence) · ⚪ available (adapter implemented and locally verifiable) · 🟡 planned. This block is generated — edit `manuscript/config.yaml`, then regenerate with `uv run python -m infrastructure.publishing.status_report --project <path> --write`._
<!-- PUBLISHING-STATUS:END -->

## Build

Own-source coverage uses branch-aware combined statement and branch coverage
with the existing 90% floor. The
project's explicit `tool.coverage.run.branch = true` matches the public release
gate and the other template exemplars, so local coverage and Stage 01 use the
same metric.

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
    --cov=projects/templates/template_autopoiesis/src \
    --cov-fail-under=90 -q
```


## Optional hardening

Default CI builds this template's wheel and runs focused behavioral tests. Further
hardening can add numeric stress cases and conservation checks across larger parameter sweeps. The complete suites and native/provider acceptance remain opt-in;
see [functional CI and hardening](../../../docs/development/ci.md) for commands
and the evidence each lane establishes.
