## Documentation Duality and AI Collaboration

Every directory at every level of the repository hierarchy contains two documentation files:

- **`README.md`**: Human-readable overview, quick-start instructions, and directory structure.
- **`AGENTS.md`**: Machine-readable technical specification optimized for AI coding assistants. Contains API tables, dependency graphs, implementation patterns, and architectural constraints.

This Documentation Duality standard serves two purposes. First, it ensures that both human researchers and AI agents can navigate the codebase efficiently—`AGENTS.md` files provide the structured context that language models need to make informed code modifications without hallucinating API signatures or violating architectural invariants. Second, it creates a self-documenting feedback loop: as AI agents modify the codebase, they update the corresponding `AGENTS.md` files, keeping documentation synchronized with implementation. Lau and Guo's survey of 90 AI coding assistant systems [@lau2025aicoding] identifies contextual code understanding as a primary bottleneck; the Documentation Duality standard addresses this by providing pre-structured context at every directory level.

The template additionally includes `CLAUDE.md` at the repository root, providing system-level instructions for AI coding assistants—architectural principles, testing requirements, and naming conventions that apply globally. This creates a three-tier documentation architecture: per-directory `AGENTS.md` for local context, root `README.md` and `CLAUDE.md` for global constraints, and `README.md` for human navigation.

## Agentic Skill Architecture

The [Documentation Duality](#documentation-duality-and-the-agentic-skill-architecture) standard addresses human and AI navigation at the directory level. A complementary layer operates at the *module* level: every infrastructure subpackage carries two additional machine-readable files that transform it from a passive code library into an active, protocol-aligned skill endpoint.

### The Three-Tier Skill Protocol

`template/` implements a progression of agent-facing documentation, escalating in specificity from global constraints to module-level API contracts:

| Tier | File | Scope | Purpose |
|------|------|-------|---------|
| 1 — System | `README.md` | Repository root | Global architectural principles, Zero-Mock policy, naming conventions |
| 2 — Structure | `AGENTS.md` | Every directory | Local file inventories, API surfaces, integration patterns, architectural constraints |
| 3 — Skill | `SKILL.md` | Every infrastructure module | Machine-parseable skill descriptor: module name, description, key imports, usage pattern |

Tier 1 and Tier 2 have direct analogues in the prompt-engineering literature: system prompts and retrieval-augmented context [@lau2025aicoding]. Tier 3 is novel. The `SKILL.md` files follow a YAML frontmatter + Markdown instruction format precisely aligned with the tool-descriptor schemas of the Model Context Protocol [@anthropic2024mcp]. The following is the exact frontmatter from `infrastructure/rendering/SKILL.md`:

```yaml
---
name: rendering
description: >
  Multi-format output generation (PDF, HTML, slides).
  Use for: Pandoc/XeLaTeX rendering, RenderManager, slide deck generation.
  Key imports: RenderManager, RenderingConfig from infrastructure.rendering
---
```

An MCP client reading this block immediately knows the module name, its natural-language activation condition ("use for"), and which Python symbols to import. No source-code inspection is required. This is the practical implementation of Toolformer-style self-documented tools [@schick2023toolformer]—rather than a language model learning tool APIs from training data, the APIs are encoded directly in version-controlled, co-located skill files that evolve with the codebase.

### Module Skill Coverage

All ten active infrastructure modules carry `SKILL.md` files. A companion `PAI.md` (Personal AI Infrastructure) file at the top of the `infrastructure/` directory documents the collection's role within a researcher's broader AI-assisted ecosystem—capturing import rules, testing obligations, and cross-module dependencies in the format used by Codomyrmex-style PAI frameworks.

This coverage is a structural invariant enforced by the Documentation Duality standard—every new module added to `infrastructure/` must carry `AGENTS.md`, `README.md`, and `SKILL.md` before it is accepted by the pipeline.

### MCP Server Mapping

The mapping from `SKILL.md` descriptors to MCP server endpoints is intentional but not yet automated; it represents the principal next integration step. In the MCP architecture [@anthropic2024mcp], a server exposes three primitive types: **Tools** (executable functions), **Resources** (data the model can read), and **Prompts** (structured query templates). Each `infrastructure` module maps naturally onto this taxonomy:

- `infrastructure.llm` → MCP **Tool** (`query`, `apply_template`) + MCP **Prompt** (research prompt templates)
- `infrastructure.rendering` → MCP **Tool** (`render_pdf`, `render_html`) + MCP **Resource** (rendered PDFs as URI-addressable resources)
- `infrastructure.validation` → MCP **Tool** (`validate_pdf_rendering`, `validate_markdown`)
- `infrastructure.publishing` → MCP **Tool** (`publish_to_zenodo`, `generate_citation_bibtex`) + MCP **Resource** (DOI registry)
- `infrastructure.steganography` → MCP **Tool** (`SteganographyProcessor.process`) + MCP **Resource** (hash manifests)

An agent orchestrating a full research pipeline could, in principle, compose these MCP tools to reproduce the entire eight-stage pipeline programmatically—discovering available tools via `SKILL.md` frontmatter, executing them via MCP protocol calls, and consuming their outputs as Resources. The `SKILL.md` files parallel Voyager's skill library [@wang2023voyager]—Voyager's agent accumulates a growing library of executable Minecraft skills represented as JavaScript functions; `template/`'s agent accumulates a curated library of research pipeline skills represented as YAML-frontmattered `SKILL.md` files. In both cases, the skill representation is machine-readable, version-controlled, and self-describing. Wang et al.'s LLM agent survey [@wang2024llmagents] identifies tool use, planning, and memory as the three fundamental capabilities of autonomous agents; Yao et al.'s ReAct framework [@yao2023react] demonstrates that interleaving reasoning traces with tool actions dramatically improves agent reliability in interactive settings. The `template/` skill architecture provides the tool-use layer aligned with these frameworks, the eight-stage pipeline provides the planning scaffold, and the checkpoint system provides the memory layer.
