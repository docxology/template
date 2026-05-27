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
| `docs/` directory | 90+ files across 12 subdirectories | User guides, API reference, troubleshooting |
| Per-directory | `AGENTS.md` + `README.md` at every directory | Documentation Duality standard |
| Per-module (Tier 3) | `SKILL.md` at every infrastructure module | Machine-parseable MCP-aligned skill descriptor |
| Infrastructure-level (PAI) | `PAI.md` at `infrastructure/` directory | Personal AI Infrastructure integration contract |

The `docs/` subdirectories cover: `core/` (essential docs), `guides/` (skill levels 1–12), `architecture/` (system design), `usage/` (content authoring), `operational/` (build, config, logging, troubleshooting), `reference/` (API, FAQ, glossary), `modules/` (${module_count} infrastructure modules), `development/` (contributing, testing), `best-practices/` (version control, migration), `prompts/` (9 AI prompt templates), `security/` (steganography, hashing), and `audit/` (review reports).
