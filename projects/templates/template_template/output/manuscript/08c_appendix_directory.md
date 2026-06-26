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
├── projects/                    # Typed program subfolders (`discover_projects`)
│   ├── templates/               # Public exemplars (git-tracked)
│   │   ├── template_active_inference/
│   │   ├── template_autoresearch_project/
│   │   ├── template_code_project/
│   │   ├── template_prose_project/
│   │   └── template_template/   # Present manuscript (`manuscript/` here)
│   ├── active/                  # Hot-seat rendered set (symlinked, private)
│   ├── working/                 # Non-rendered backburner (symlinked, private)
│   ├── published/               # Non-rendered published (symlinked, private)
│   ├── archive/                 # Non-rendered retired (symlinked, private)
│   └── other/                   # Non-rendered misc (symlinked, private)
├── docs/ (18 top-level areas, 376+ markdown files per live counter)
├── tests/                       # Infra suites (426+ files)
├── AGENTS.md / README.md / CLAUDE.md / pyproject.toml
├── run.sh / secure_run.sh
└── output/ …                    # Mirrors after copy stage
```
See `docs/_generated/active_projects.md` for regenerated slugs (`uv run python scripts/generate_active_projects_doc.py`).


