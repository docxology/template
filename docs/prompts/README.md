# docs/prompts/ — Agent workflow skills

Discoverable agent skills for template-compliant work. Each workflow lives in a subdirectory with `SKILL.md` (YAML frontmatter for auto-routing).

**Hub:** [SKILL.md](SKILL.md) · **Modes:** [MODE_REGISTRY.md](MODE_REGISTRY.md) · **Technical index:** [AGENTS.md](AGENTS.md)

## How to invoke

Say what you need in natural language — no slash commands or copy-paste blocks required. Examples:

| Say something like… | Skill |
| --- | --- |
| "Pipeline failed at PDF render for template_code_project" | [pipeline-debugging/SKILL.md](pipeline-debugging/SKILL.md) |
| "Full repo audit for active projects" | [comprehensive-assessment/SKILL.md](comprehensive-assessment/SKILL.md) |
| "Research this topic and build a verified corpus" | [deep-research/SKILL.md](deep-research/SKILL.md) |
| "Plan and draft this paper from project artifacts" | [academic-paper/SKILL.md](academic-paper/SKILL.md) |
| "Review this manuscript like peer reviewers" | [academic-paper-reviewer/SKILL.md](academic-paper-reviewer/SKILL.md) |
| "Run the whole research-to-publication workflow" | [academic-pipeline/SKILL.md](academic-pipeline/SKILL.md) |
| "Audit methods against pipeline stages and evidence" | [methods-orchestration/SKILL.md](methods-orchestration/SKILL.md) |
| "Triple-check every manuscript claim before arXiv" | [manuscript-claim-verification/SKILL.md](manuscript-claim-verification/SKILL.md) |
| "Prove double-run reproducibility before Zenodo" | [reproducibility-audit/SKILL.md](reproducibility-audit/SKILL.md) |
| "Audit [[FIG:]] and labels.yaml" | [manuscript-cross-references/SKILL.md](manuscript-cross-references/SKILL.md) |
| "Scaffold new project + manuscript from brief" | [manuscript-creation/SKILL.md](manuscript-creation/SKILL.md) |
| "Add tests, no mocks" | [test-creation/SKILL.md](test-creation/SKILL.md) |
| "New infrastructure/ package" | [infrastructure-module/SKILL.md](infrastructure-module/SKILL.md) |
| "Discover skills and make template more agentic" | [agentic-use/SKILL.md](agentic-use/SKILL.md) |

## Categories

### Research content

| Skill directory | Use when |
| --- | --- |
| [deep-research/](deep-research/SKILL.md) | Research intake, literature search, fact-checking, systematic review planning |
| [academic-paper/](academic-paper/SKILL.md) | Paper planning, drafting, revision, formatting, disclosure |
| [academic-paper-reviewer/](academic-paper-reviewer/SKILL.md) | Read-only review, methodology review, re-review |
| [academic-pipeline/](academic-pipeline/SKILL.md) | Research-to-publication orchestration |
| [methods-orchestration/](methods-orchestration/SKILL.md) | Methods-to-pipeline provenance, artifact/evidence wiring |
| [manuscript-creation/](manuscript-creation/SKILL.md) | New manuscript + project from a research brief |
| [manuscript-cross-references/](manuscript-cross-references/SKILL.md) | Registry/token manuscripts and cross-ref audits |
| [manuscript-claim-verification/](manuscript-claim-verification/SKILL.md) | Triple-check every claim; stay renderable |
| [literature-synthesis/](literature-synthesis/SKILL.md) | LLM blocks for search corpus synthesis |

### Code and tests

| Skill directory | Use when |
| --- | --- |
| [code-development/](code-development/SKILL.md) | New modules, algorithms, utilities |
| [test-creation/](test-creation/SKILL.md) | Tests under the no-mocks policy |
| [feature-addition/](feature-addition/SKILL.md) | End-to-end feature work |
| [refactoring/](refactoring/SKILL.md) | Clean-break refactors |

### Infrastructure and docs

| Skill directory | Use when |
| --- | --- |
| [infrastructure-module/](infrastructure-module/SKILL.md) | New `infrastructure/*` packages |
| [documentation-creation/](documentation-creation/SKILL.md) | AGENTS.md / README.md for a directory |
| [validation-quality/](validation-quality/SKILL.md) | Validation CLI and gates |
| [comprehensive-assessment/](comprehensive-assessment/SKILL.md) | Wide audit |
| [reproducibility-audit/](reproducibility-audit/SKILL.md) | Determinism before release |
| [pipeline-debugging/](pipeline-debugging/SKILL.md) | DAG stage triage |
| [agentic-use/](agentic-use/SKILL.md) | Skill inventory, routing, and external companion review |

## Discovery

Skills are indexed in `.cursor/skill_manifest.json`:

```bash
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills write-index
uv run python -m infrastructure.skills check-contracts
```

Human browse: [`docs/_generated/skills_index.md`](../_generated/skills_index.md).

`check-contracts` validates the workflow metadata fields documented in
[MODE_REGISTRY.md](MODE_REGISTRY.md): version, last update, status, data access level,
task type, modes, and related skills.

## Attribution

The academic workflow skills are original template-native adaptations inspired by
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills),
especially its public mode registry, data-access labels, provenance checkpoints, and
benchmark disclosure practices. ARS prompt text, scripts, and schemas are not vendored
because ARS is CC-BY-NC-4.0 and this repository is Apache-2.0.

## Standards

| Resource | Role |
| --- | --- |
| [`../rules/`](../rules/) | Normative coding, testing, docs |
| [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md) | Pandoc cite + crossref |
| [`../core/architecture.md`](../core/architecture.md) | Two layers, thin orchestrator |
| [`.github/AGENTS.md`](../../.github/AGENTS.md) | CI jobs and coverage floors |

## See also

- [`../README.md`](../README.md) — documentation hub
- [`../../CLAUDE.md`](../../CLAUDE.md) — command cheat sheet
- [`../guides/new-project-one-shot-prompt.md`](../guides/new-project-one-shot-prompt.md) — one-shot LLM scaffold
