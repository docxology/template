"""Performance benchmarks for :mod:`infrastructure.core.analysis_pipeline`.

Each bench builds a synthetic ``projects/<name>/scripts`` tree with N
trivial Python scripts (each only ``print("ok")``) and benchmarks
:func:`run_analysis_pipeline` end-to-end. Real subprocesses, real
filesystem — no mocks.

Three sizes — N = 1, 5, 25 — characterise the per-script overhead the
analysis pipeline imposes on top of interpreter startup.

Run with::

    uv run pytest tests/infra_tests/benchmark/test_analysis_pipeline_bench.py \
        -m bench --benchmark-only --benchmark-min-rounds=3 --timeout=180
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.analysis_pipeline import run_analysis_pipeline

_TRIVIAL_SCRIPT_BODY = '#!/usr/bin/env python3\nprint("ok")\n'


def _make_synthetic_project(repo_root: Path, project_name: str, n_scripts: int) -> list[Path]:
    """Create ``projects/<name>/scripts/0N_step.py`` files.

    Args:
        repo_root: Synthetic repository root (typically ``tmp_path``).
        project_name: Project subdirectory name to create under ``projects/``.
        n_scripts: Number of trivial scripts to emit.

    Returns:
        Lexicographically ordered list of script paths, mirroring what
        ``discover_analysis_scripts`` would return.
    """
    project_root = repo_root / "projects" / project_name
    scripts_dir = project_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    # Also create a src/ tree so build_analysis_script_cmd_and_env's
    # PYTHONPATH entry resolves to a real directory.
    (project_root / "src").mkdir(exist_ok=True)

    paths: list[Path] = []
    for i in range(n_scripts):
        script = scripts_dir / f"{i:02d}_step.py"
        script.write_text(_TRIVIAL_SCRIPT_BODY, encoding="utf-8")
        paths.append(script)
    return sorted(paths)


@pytest.mark.bench
@pytest.mark.parametrize("n_scripts", [1, 5, 25])
def test_bench_run_analysis_pipeline(benchmark: object, tmp_path: Path, n_scripts: int) -> None:
    """Bench ``run_analysis_pipeline`` for N = 1, 5, 25 trivial scripts.

    Each round forks ``n_scripts`` real Python interpreters, so we use
    ``benchmark.pedantic`` with a small fixed round count to keep wall
    time bounded while still producing a stable median.
    """
    repo_root = tmp_path
    project_name = f"bench_proj_n{n_scripts}"
    scripts = _make_synthetic_project(repo_root, project_name, n_scripts)

    def call() -> int:
        return run_analysis_pipeline(scripts, repo_root, project_name)

    rc = benchmark.pedantic(call, rounds=3, iterations=1, warmup_rounds=1)  # type: ignore[attr-defined]
    assert rc == 0
