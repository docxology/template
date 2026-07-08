# `infrastructure/doctor/detectors/`

Read-only diagnostic detectors grouped by concern:

| Module | Detectors |
| --- | --- |
| `tooling.py` | `detect_uv_available`, `detect_python_version`, `detect_run_sh_executable` |
| `layout.py` | `detect_project_structure`, `detect_manuscript_config` |
| `hygiene.py` | `detect_pycache_clutter`, `detect_stale_coverage_files`, `detect_orphan_output_dirs` |
| `state.py` | `detect_pre_commit_installed`, `detect_lockfile_drift`, `detect_optional_services`, `detect_codex_startup_config`, `detect_doctor_state_writable` |
| `registry.py` | `DETECTORS`, `run_detectors` |

Import the public API from `infrastructure.doctor.detectors` (package `__init__.py` re-exports `registry`).
