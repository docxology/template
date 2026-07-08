"""Full project verification workflow: preflight, chunked pytest, coverage pass."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path


def _relative_test_path(project_root: Path, path: Path) -> str:
    return str(path.relative_to(project_root))


def _all_test_modules(project_root: Path) -> list[str]:
    return [_relative_test_path(project_root, path) for path in sorted((project_root / "tests").rglob("test_*.py"))]


def _chunked_test_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    chunks: list[tuple[str, list[str]]] = [
        (
            "Focused contract and infrastructure checks",
            [
                "tests/test_validation_spine.py",
                "tests/test_documentation_contracts.py",
                "tests/test_method_inventory.py",
                "tests/test_gate_support_contracts.py",
            ],
        ),
        (
            "Gate and manuscript-focused checks",
            [
                "tests/gates/test_claim_ledger.py",
                "tests/gates/test_manuscript_gates.py",
                "tests/gates/test_output_gates.py",
            ],
        ),
    ]
    sheaf_chunks = [
        _relative_test_path(project_root, path) for path in sorted((project_root / "tests").glob("test_sheaf_*.py"))
    ]
    chunks.append(
        (
            "Roadmap and sheaf consolidation checks",
            [
                "tests/test_roadmap_promotion.py",
                *sheaf_chunks,
                "tests/test_track_consolidation_negative.py",
                "tests/test_track_consolidation_surface.py",
                "tests/test_track_consolidation_support_contracts.py",
            ],
        )
    )
    return [(label, modules) for label, modules in chunks if modules]


def _coverage_test_groups(project_root: Path) -> list[tuple[str, list[str]]]:
    chunks = _chunked_test_groups(project_root)
    chunked_modules = {module for _, modules in chunks for module in modules}
    remaining = [module for module in _all_test_modules(project_root) if module not in chunked_modules]
    return [*chunks, ("Remaining active-inference tests", remaining)]


def _coverage_command(modules: list[str], *, append: bool, final: bool) -> list[str]:
    cmd = ["uv", "run", "pytest", *modules, "--cov=src", "-q"]
    if append:
        cmd.append("--cov-append")
    if final:
        cmd.extend(["--cov-report=term-missing", "--cov-fail-under=90", "--durations=20"])
    else:
        cmd.append("--cov-report=")
    return cmd


def _run(project_root: Path, cmd: list[str], label: str, *, env: dict[str, str] | None = None) -> None:
    print(f"\n==> {label}")
    print(f"    $ {' '.join(shlex.quote(part) for part in cmd)}")
    start = time.perf_counter()
    process_env = os.environ.copy()
    process_env.setdefault("MPLBACKEND", "Agg")
    process_env.setdefault("PYTHONUNBUFFERED", "1")
    process_env.setdefault("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", "2")
    if env:
        process_env.update(env)
    result = subprocess.run(
        cmd,
        cwd=project_root,
        env=process_env,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    print(f"    status: {result.returncode}  elapsed: {elapsed:.1f}s")
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed with return code {result.returncode}")


def run_verification(project_root: Path, *, skip_chunks: bool = False, monolithic_coverage: bool = False) -> None:
    """Run verification."""
    preflight = [
        ("Run analytical sweep", ["uv", "run", "python", "scripts/run_analytical_sweep.py"]),
        ("Compute analysis statistics", ["uv", "run", "python", "scripts/compute_statistics.py"]),
        ("Compose manuscript sections", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Validate compose contracts",
            ["uv", "run", "python", "scripts/compose_manuscript.py", "--validate-only", "--strict"],
        ),
        ("Generate manuscript variables", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Render registered figures", ["uv", "run", "python", "scripts/generate_figures.py"]),
        ("Settle post-figure fixed point", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Final compose before output gate", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Settle post-compose fixed point", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Settled final compose before output gate", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Validate generated outputs", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        ("Check documentation contract", ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"]),
        ("Check method inventory", ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"]),
    ]
    for label, cmd in preflight:
        _run(project_root, cmd, label)

    if not skip_chunks:
        for label, modules in _chunked_test_groups(project_root):
            _run(project_root, ["uv", "run", "pytest", *modules, "-q"], label)

    postflight = [
        ("Pre-coverage compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Pre-coverage fixed-point refresh", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Pre-coverage figure refresh", ["uv", "run", "python", "scripts/generate_figures.py"]),
        (
            "Pre-coverage post-figure fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Pre-coverage final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Pre-coverage post-compose fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Pre-coverage settled final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Pre-coverage output gate", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        (
            "Pre-coverage documentation gate",
            ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"],
        ),
        (
            "Pre-coverage method inventory gate",
            ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"],
        ),
    ]
    for label, cmd in postflight:
        _run(project_root, cmd, label)

    if monolithic_coverage:
        _run(
            project_root,
            [
                "uv",
                "run",
                "pytest",
                "tests/",
                "--cov=src",
                "--cov-fail-under=90",
                "--durations=20",
                "-q",
                "--maxfail=1",
            ],
            "Full suite coverage pass",
        )
    else:
        coverage_groups = [(label, modules) for label, modules in _coverage_test_groups(project_root) if modules]
        for index, (label, modules) in enumerate(coverage_groups):
            _run(
                project_root,
                _coverage_command(
                    modules,
                    append=index > 0,
                    final=index == len(coverage_groups) - 1,
                ),
                f"Coverage pass: {label}",
            )

    final_refresh = [
        ("Post-coverage compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Post-coverage fixed-point refresh", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Post-coverage figure refresh", ["uv", "run", "python", "scripts/generate_figures.py"]),
        (
            "Post-coverage post-figure fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Post-coverage final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Post-coverage post-compose fixed-point refresh",
            ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"],
        ),
        ("Post-coverage settled final compose refresh", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Post-coverage output gate", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        (
            "Post-coverage documentation gate",
            ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"],
        ),
        (
            "Post-coverage method inventory gate",
            ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"],
        ),
    ]
    for label, cmd in final_refresh:
        _run(project_root, cmd, label)
