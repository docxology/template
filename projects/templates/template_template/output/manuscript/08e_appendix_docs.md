\newpage

## Appendix: Documentation Inventory {#appendix-docs}

The repository maintains documentation at three levels:

\begin{table}[h]
\caption{Documentation inventory across the four-layer documentation architecture, from repository-wide system files to per-module skill descriptors.}
\label{tab:documentation-inventory}
\end{table}

| Level | Files | Purpose |
|-------|:-----:|---------| 
| Repository root | `AGENTS.md`, `CLAUDE.md`, `README.md`, `RUN_GUIDE.md` | Global navigation and AI agent context |
| `docs/` directory | 390 files across 18 subdirectories | User guides, API reference, troubleshooting |
| Per-directory | `AGENTS.md` + `README.md` at every directory | Documentation Duality standard |
| Per-module (Tier 3) | `SKILL.md` at every infrastructure module | Machine-parseable MCP-aligned skill descriptor |
| Infrastructure-level (PAI) | `PAI.md` at `infrastructure/` directory | Personal AI Infrastructure integration contract |

The `docs/` subdirectories cover: `core/` (essential docs), `guides/` (progressive skill-level guides), `architecture/` (system design), `usage/` (content authoring), `operational/` (build, config, logging, troubleshooting), `reference/` (API, FAQ, glossary), `modules/` (28 infrastructure modules), `development/` (contributing, testing), `best-practices/` (version control, migration), `prompts/` (21 AI prompt templates), `security/` (steganography, hashing), and `audit/` (review reports).

Every count in this appendix is injected from live repository introspection rather than hand-maintained: `390` counts every Markdown file beneath `docs/` recursively, `18` counts its first-level subdirectories, and `21` counts the workflow subdirectories that each carry a `SKILL.md` descriptor. This is the same discipline the manuscript argues for throughout—a hand-typed documentation total silently rots as the tree grows, whereas a token re-resolves on every render. A reader onboarding to the repository should start at `docs/core/`, follow the graduated `docs/guides/` skill ladder, and consult the per-directory `AGENTS.md`/`README.md` pair nearest to whatever code they are editing; AI agents additionally read each module's `SKILL.md` to locate capabilities without guessing API signatures.
