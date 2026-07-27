# Repurposing template architectures for research

> **Entry point for:** "Can I repurpose the architectures you're using for
> research?"

**Yes.** The template's architectures are designed for reuse. Every
infrastructure module is a standalone Python package with no project-specific
dependencies — you import only what you need. This page maps each reusable
architecture to the module, the contract, and how to adopt it.

## Quick answer: what can I take?

| Architecture | Module | What it gives you | Adopt in isolation? |
| --- | --- | --- | --- |
| Declarative DAG pipeline | `infrastructure.core.pipeline` | A 16-stage pipeline from env setup through PDF rendering, validation, and publishing — configured via YAML, not code | Yes — `pipeline.yaml` + `infrastructure.core.pipeline` |
| Two-layer separation | `infrastructure/` + `projects/` | Generic build tools (Layer 1) never depend on project code (Layer 2); projects import infrastructure, never the reverse | Yes — copy the directory contract |
| Thin orchestrator pattern | `scripts/` + `infrastructure.orchestration` | Scripts coordinate; all business logic lives in importable packages. Enforced by CI gates and `check_template_drift.py` | Yes — adopt the `scripts/` convention |
| Multi-format rendering | `infrastructure.rendering` | Pandoc + XeLaTeX pipeline producing PDF, HTML, slides, DOCX, and EPUB from Markdown manuscripts | Yes — `infrastructure.rendering` + pandoc + texlive |
| Evidence registry | `infrastructure.validation.evidence_registry` | Every manuscript claim is bound to a registered evidence source; drift is CI-gated | Yes — `infrastructure.validation` |
| Multi-project discovery | `infrastructure.project` | Drop a `projects/{name}/` directory with `src/` + `tests/` + `manuscript/config.yaml` and it is auto-discovered, tested, analyzed, and rendered | Yes — `infrastructure.project` |
| Zero-mock testing | `scripts/audit/verify_no_mocks.py` | Lexical + semantic gate that prohibits mock frameworks and dependency replacements | Yes — copy the script + `pyproject.toml` test config |
| Cryptographic provenance | `infrastructure.steganography` + `infrastructure.provenance` | SHA-256/512 hash manifests, alpha-channel PDF watermarking, QR codes, metadata embedding | Yes — `infrastructure.steganography` |
| MCP server | `infrastructure.mcp_server` | Stdio MCP server exposing operation catalogs, pipeline descriptions, and skill routing to any MCP-speaking agent | Yes — `infrastructure.mcp_server` |
| Publishing stack | `infrastructure.publishing` | Dry-run-by-default upload to Zenodo, GitHub Releases, PyPI, IPFS, OSF, HuggingFace, Software Heritage | Yes — `infrastructure.publishing` |
| Literature search | `infrastructure.search` | Federated search across arXiv, CrossRef, OpenAlex, Semantic Scholar, Paperclip, with full-text assessment | Yes — `infrastructure.search` |
| AutoResearch loop | `infrastructure.autoresearch` | Deterministic candidate-evaluation loop: generate, evaluate, rank, and publish ML candidates | Yes — `infrastructure.autoresearch` |

## How to adopt

### Minimal: just the pipeline

```bash
# 1. Use this repo as a template
gh repo create my-research --template docxology/template --private
cd my-research

# 2. Install and run
uv sync
./run.sh --pipeline --project templates/template_code_project --core-only
```

You get the full DAG pipeline, testing, rendering, and validation with zero
configuration. Delete exemplars you don't need; the `infrastructure/` layer
works with any `projects/{name}/` that follows the directory contract.

### Partial: import specific modules

Each infrastructure package is importable independently. The root
`pyproject.toml` declares all dependencies; copy only the packages you need
and their dependency lines.

```python
# Example: use only the rendering pipeline
from infrastructure.rendering import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.web_renderer import WebRenderer

# Example: use only the evidence registry
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    validate_text_against_registry,
)

# Example: use only the pipeline DAG engine
from infrastructure.core.pipeline.executor import PipelineExecutor
```

### Fork an exemplar

Each exemplar ships a 5-minute fork guide:
[`projects/templates/template_code_project/docs/forking_guide.md`](../projects/templates/template_code_project/docs/forking_guide.md)
(numerical research) and
[`projects/templates/template_prose_project/docs/forking_guide.md`](../projects/templates/template_prose_project/docs/forking_guide.md)
(editorial review).

See also [`guides/fork-an-exemplar.md`](guides/fork-an-exemplar.md) for the
top-level entry.

## Architecture deep dives

### Declarative DAG pipeline

The pipeline is configured in
[`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml).
Each stage declares a script, tags (core/science/llm/ebook/bundle/archival),
and a failure mode (hard fail, soft fail, configurable tolerance, skip if
absent). The executor reads the YAML — no Python code changes needed to add,
reorder, or skip stages.

```yaml
# pipeline.yaml excerpt
- name: Project Tests
  script: scripts/pipeline/stage_01_test.py
  tags: [core, tests]
  failure_mode: configurable_tolerance
```

Deep dive: [`architecture/adrs/002-declarative-dag-pipeline.md`](architecture/adrs/002-declarative-dag-pipeline.md)

### Two-layer separation

Layer 1 (`infrastructure/`) contains 25 importable Python packages for
rendering, validation, publishing, search, steganography, and orchestration.
Layer 2 (`projects/{name}/src/`) contains domain-specific research code.
The boundary is enforced by:

- `scripts/audit/check_tracked_all.py` — rejects private/local paths in git
- `scripts/audit/check_template_drift.py` — 10 per-exemplar drift detectors
- `verify_no_mocks.py` — prohibits mock frameworks in tests
- Coverage gates: infrastructure >= 60%, each project `src/` >= 90%

Deep dive: [`architecture/two-layer-architecture.md`](architecture/two-layer-architecture.md)

### Thin orchestrator pattern

Scripts in `scripts/` are thin coordinators — they import from
`infrastructure/` or `projects/{name}/src/`, handle I/O and orchestration, and
never implement algorithms. This keeps business logic testable and prevents
script-level code duplication.

Deep dive: [`architecture/thin-orchestrator-summary.md`](architecture/thin-orchestrator-summary.md)

### Capability surfaces (agent-operable)

The template exposes machine-readable catalogs for agent discovery:

- **Skills**: `infrastructure.skills.discovery` -> `.cursor/skill_manifest.json`
- **Operations**: `infrastructure.skills.operation_registry` -> `.cursor/operations_manifest.json`
- **Pipeline**: `infrastructure.core.pipeline.cli` -> live from `pipeline.yaml`
- **Templates**: `infrastructure.project.exemplar_roster` -> generated roster

An MCP server (`infrastructure/mcp_server.py`) serves these as MCP tools so any
MCP-speaking agent can discover and invoke capabilities.

Deep dive: [`architecture/capability-surfaces.md`](architecture/capability-surfaces.md)

### Multi-format rendering

From Markdown manuscripts to PDF, HTML, slides, DOCX, and EPUB via a single
pipeline. Mermaid diagrams are rendered by real `mmdc` against
`chrome-headless-shell`. LaTeX is processed by XeLaTeX with conditional package
loading (`\IfFileExists`) for portability.

Deep dive: [`architecture/adrs/003-multi-format-rendering-and-toggles.md`](architecture/adrs/003-multi-format-rendering-and-toggles.md)

### Evidence registry

Every number, citation, and claim in a manuscript is validated against a
registered evidence source (`data/claim_ledger.yaml`). The registry is
built per-project and CI-gated — a manuscript with an unsupported number fails
the build.

```python
registry = build_project_evidence_registry(project_dir)
report = validate_text_against_registry(manuscript_text, registry)
assert not report.errors  # fails CI if any unsupported claims
```

Deep dive: [`architecture/adrs/005-decision-memory-and-adversarial-validation.md`](architecture/adrs/005-decision-memory-and-adversarial-validation.md)

## What you don't need to take

The template is **composable** — you can adopt any subset:

- Don't need steganography? Skip `infrastructure.steganography` and
  `secure_run.sh`.
- Don't need LLM stages? Run `--core-only` and skip `infrastructure.llm`.
- Don't need publishing? Skip `infrastructure.publishing` and
  `scripts/publish/`.
- Don't need literature search? Skip `infrastructure.search`.
- Don't want the MCP server? Skip `infrastructure.mcp_server.py`.

The pipeline respects `tags` in `pipeline.yaml` — stages tagged `llm`,
`science`, `ebook`, `bundle`, or `archival` are skipped unless explicitly
configured.

## See also

- [`guides/new-project-setup.md`](guides/new-project-setup.md) — full checklist
  for adding a new research project
- [`guides/extending-and-automation.md`](guides/extending-and-automation.md) —
  customizing the pipeline and adding CI stages
- [`best-practices/migration-guide.md`](best-practices/migration-guide.md) —
  migrating from a flat repo
- [`architecture/decision-tree.md`](architecture/decision-tree.md) — where does
  new code go?
- [`PAI.md`](PAI.md) — Personal AI Infrastructure context
