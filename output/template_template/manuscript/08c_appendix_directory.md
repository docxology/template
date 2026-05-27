\newpage

## Appendix: Repository Directory Structure {#appendix-directory}

```text
template/
├── infrastructure/
│   ├── config/ docker/ documentation/ llm/
│   ├── orchestration/   # Thin Python entry equal to `./run.sh` backend
│   ├── prose/ reference/ rendering/ reporting/
│   ├── scientific/ search/ skills/ steganography/ validation/
│   ├── project/ core/
│   └── logrotate.d/      # Operational rotation templates (no Python pkg)
├── scripts/
│   ├── 00_setup_environment.py … 07_generate_executive_report.py
│   ├── execute_pipeline.py execute_multi_project.py
├── projects/                    # ACTIVE exemplars (`discover_projects`)
│   ├── template_code_project/
│   ├── template_prose_project/
│   ├── template_search_project/
│   └── … rotated research trees + `_test_project` CI fixture stubs
├── projects_in_progress/
│   └── template/                # Present manuscript (`manuscript/` here)
├── projects_archive/            # Preserved workspaces (inactive)
├── docs/ (17 top-level areas, 351+ markdown files per live counter)
├── tests/                       # Infra suites (367+ files)
├── AGENTS.md / README.md / CLAUDE.md / pyproject.toml
├── run.sh / secure_run.sh
└── output/ …                    # Mirrors after copy stage
```
See `docs/_generated/active_projects.md` for regenerated slugs (`uv run python scripts/generate_active_projects_doc.py`).


