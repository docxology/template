"""Performance benchmarks for :mod:`infrastructure.core.analysis_pipeline`.

Each bench builds a synthetic ``projects/<name>/scripts`` tree with N
trivial Python scripts (each only ``print("ok")``) and benchmarks
:func:`run_analysis_pipeline` end-to-end. Real subprocesses, real
filesystem — no mocks.

Three sizes — N = 1, 5, 25 — characterise the per-script overhead the
analysis pipeline imposes on top of interpreter startup.
N = 1 retains repeated samples; N = 5 and 25 record one complete cold run
each. A single cold observation does not establish timing stability.

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
@pytest.mark.parametrize(
    "n_scripts",
    [
        pytest.param(1, marks=pytest.mark.timeout(60)),
        pytest.param(5, marks=pytest.mark.timeout(60)),
        pytest.param(25, marks=pytest.mark.timeout(180)),
    ],
)
def test_bench_run_analysis_pipeline(benchmark: object, tmp_path: Path, n_scripts: int) -> None:
    """Bench ``run_analysis_pipeline`` for N = 1, 5, 25 trivial scripts.

    Each round launches ``n_scripts`` real guarded Python interpreters.
    The single-script input retains three measured rounds and one warmup.
    Larger workloads record one complete cold sample, without a stability
    claim. The 25-script member uses the documented benchmark safety budget;
    smaller members retain their 60-second limits.
    """
    repo_root = tmp_path
    project_name = f"bench_proj_n{n_scripts}"
    scripts = _make_synthetic_project(repo_root, project_name, n_scripts)

    def call() -> int:
        return run_analysis_pipeline(scripts, repo_root, project_name)

    rounds, warmups = (3, 1) if n_scripts == 1 else (1, 0)
    rc = benchmark.pedantic(call, rounds=rounds, iterations=1, warmup_rounds=warmups)  # type: ignore[attr-defined]
    assert rc == 0
