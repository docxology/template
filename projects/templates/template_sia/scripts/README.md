# Scripts — template_sia

Thin orchestrators for the SIA analysis stage. Import computation from `../src/`.

`run_sia_loop.py` defaults to fixture replay. `--live-sia` runs fixed reference
diagnostics. `--live-proposals` selects the bounded local Ollama/Docker numeric
proposal controller; exit 75 means a required live capability is blocked, and
nonzero failed runs retain diagnostics under the selected fresh output directory.
