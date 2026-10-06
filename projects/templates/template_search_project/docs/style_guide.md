# Style Guide

Project code owns literature policy and pure transformations. Mature platform APIs
own retrieval, parsing, configuration-byte admission, logging, and confined I/O.
Keep source, controlled tests, live receipts, and historical artifacts distinct.

## 1. Zero-Mock Policy

Follow the repository's dependency-replacement policy. Do not add `unittest.mock`,
`MagicMock`, patch decorators, or runtime replacement of real dependencies.
Use real temporary files, `LocalBackend`, controlled HTTP servers, and the public
callable parameter for prompt/response contract tests. Such controlled calls
establish contract behavior; actual provider/model acceptance is separate.

```python
from template_search_project.pipeline.synthesis import synthesise_per_paper

def controlled_response(prompt: str) -> str:
    assert "PAPER" in prompt
    return "Controlled response for a prompt-contract test."

result = synthesise_per_paper(paper, "key2024", llm=controlled_response)
assert result.kind == "per_paper"
```

Read [`testing_philosophy.md`](testing_philosophy.md) for the isolated suite and
independent evidence requirements. Controlled text is never a model transcript.

## 2. Infrastructure Delegation

`manuscript/layer_contract.yaml` declares exact admitted source paths. Do not
maintain a contradictory second import allowlist in prose. The current adapters
reuse these platform responsibilities:

| Project responsibility | Mature platform surface |
|---|---|
| Typed configuration admission | Immutable UTF-8 configuration sources |
| Retrieval and caching | Literature backends, client, and optional nominated cache boundary |
| Citation identities and projection | BibTeX parsing/rendering and meaningful collision validation |
| Generated artifact writes | Held no-follow directory I/O and atomic file publication |
| Current composition dependencies | Held source inventory and exact artifact-byte custody |
| Model adapter and required live lane | Optional LLM client and audited unpaid transport |
| Dashboard | Shared interactive reporting |

Domain decisions remain in `src/template_search_project/`. Scripts parse flags,
load configuration, and call those modules. Cross-cutting changes belong in the
platform only after behavior and domain-error parity are demonstrated.

## 3. The Thin-Orchestrator Pattern

Scripts do not implement pagination, deduplication, collision rules, scoring, or
prompt assembly. They call actual named project APIs, for example:

```python
from template_search_project.pipeline.pipeline import run_literature_pipeline
artifacts = run_literature_pipeline(config, project_root=project_root)
```

### Alphabetical script-order convention

Names remain readable, but actual core selection and order come from the explicit
`analysis.scripts` list:

| Order | Script | Responsibility |
|---|---|---|
| 1 | `run_search_pipeline.py` | Standard local corpus, results, generated bibliography, and report |
| 2 | `y_generate_search_figures.py` | Diagnostic figures |
| 3 | `z_generate_manuscript_variables.py` | Variables, authored copies, generated citation projection |
| 4 | `zz_generate_review_report.py` | Review diagnostics |
| 5 | `zzz_build_dashboard.py` | Current corpus dashboard |

Deep search and composition are explicit opt-in commands. Match their overrides,
compose the generated S02, then hydrate before rendering. The dashboard omits an
old deep aggregate unless an explicit direct `--aggregate` is selected.
`scripts/review` is an out-of-band CLI used by the review producer.

## 4. Manuscript Claims and Variables

Use concrete API names and `{{TOKEN}}` variables for changing measurements.
A fixture corpus exercises the workflow and cannot establish empirical literature
findings. A current data count, source hash, model transcript, and rendered PDF
prove different things; never substitute one for another.

Generated references belong under `output/bibliography/`. Curated databases and
authored markdown stay under `manuscript/`. The resolver projects new citation
keys into `output/manuscript/generated_search.bib`; it preserves curated metadata
and refuses meaningful collisions. Default composition writes only
`output/manuscript/S02_generated_literature_review.md` and binds its current
producer/configuration/source dependency. Explicit manual `--output` is an
independent authoring action.

## 5. Portable Outputs

Use project-relative paths in public summaries. Keep credentials, absolute private
paths, runtime process state, and request diagnostics out of public artifacts.
Actual operational/model timestamps remain honest runtime evidence; deterministic
report dates use `SOURCE_DATE_EPOCH` or an explicit stable sentinel.

Nominated project cache and generated artifact writes use mature confined I/O.
Do not resolve away symlink evidence before the operation, create directories with
ordinary path I/O before confinement, or replace an unsafe authored target.
Missing/partial required producer evidence must fail with retained diagnostics.
