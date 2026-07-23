"""Full project verification workflow: preflight, chunked pytest, coverage pass."""

from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal

VerificationProfile = Literal["quick", "release", "exhaustive"]


def _relative_test_path(project_root: Path, path: Path) -> str:
    return str(path.relative_to(project_root))


_REFRESHABLE_GENERATORS = frozenset(
    {
        "compose_manuscript.py",
        "z_generate_manuscript_variables.py",
        "generate_figures.py",
        "generate_method_inventory.py",
    }
)
_FINGERPRINT_EXCLUDED_PARTS = frozenset({".git", ".pytest_cache", ".venv", "htmlcov", "__pycache__"})


def _project_state_fingerprint(project_root: Path) -> str:
    """Return a deterministic source/output fingerprint for refresh caching.

    The fingerprint intentionally includes both inputs and generated contract
    outputs. A refresh is skipped only when the exact same generator already
    observed this byte state after a successful run, so a downstream producer
    changing any contract artifact naturally invalidates the cache.
    """
    digest = hashlib.sha256()
    for path in sorted(project_root.rglob("*")):
        if not path.is_file() or _FINGERPRINT_EXCLUDED_PARTS.intersection(path.parts):
            continue
        if path.name.startswith(".coverage"):
            continue
        relative = path.relative_to(project_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(path.read_bytes())
        except OSError:
            # A concurrently written disposable output will be reflected by
            # the next fingerprint; never turn cache bookkeeping into a gate.
            continue
        digest.update(b"\0")
    return digest.hexdigest()


def _generator_name(command: list[str]) -> str | None:
    """Return the refreshable script name in a command, if any."""
    if "--check" in command:
        return None
    for part in command:
        name = Path(part).name
        if name in _REFRESHABLE_GENERATORS:
            return name
    return None


class _RefreshCache:
    """In-run fixed-point cache for idempotent generator commands."""

    def __init__(self) -> None:
        """Initialize an empty in-run refresh cache."""
        self._last_outputs: dict[str, str] = {}

    def run(
        self,
        project_root: Path,
        command: list[str],
        label: str,
        command_runner: Callable[..., None],
    ) -> None:
        """Run a generator command, skipping it when the project state is unchanged.

        If the command's generator is refreshable and the project fingerprint
        matches the last observed state for that generator, the command is
        skipped.  Otherwise the command is executed and the new fingerprint
        is cached.
        """
        generator = _generator_name(command)
        if generator is None:
            command_runner(project_root, command, label)
            return
        before = _project_state_fingerprint(project_root)
        if self._last_outputs.get(generator) == before:
            print(f"\n==> {label}\n    fixed point unchanged; skipped {generator}")
            return
        command_runner(project_root, command, label)
        self._last_outputs[generator] = _project_state_fingerprint(project_root)


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


def _profile_marker_args(profile: VerificationProfile | None) -> list[str]:
    """Return additive pytest selection args for a named verification profile."""
    if profile is None:
        return []
    if profile == "quick":
        expression = (
            "not slow and not long_running and not requires_ollama and not requires_docker "
            "and not network and not bench and not benchmark and not performance"
        )
    elif profile == "release":
        expression = (
            "not long_running and not requires_ollama and not requires_docker and not network "
            "and not bench and not benchmark and not performance"
        )
    elif profile == "exhaustive":
        expression = (
            "not requires_ollama and not requires_docker and not network "
            "and not bench and not benchmark and not performance"
        )
    else:  # pragma: no cover - Literal callers are validated by the CLI
        raise ValueError(f"unknown verification profile: {profile}")
    return ["-m", expression]


def _coverage_command(
    modules: list[str],
    *,
    append: bool,
    final: bool,
    profile: VerificationProfile | None = None,
) -> list[str]:
    cmd = ["uv", "run", "pytest", *modules, "--cov=src", "-q"]
    cmd.extend(_profile_marker_args(profile))
    if append:
        cmd.append("--cov-append")
    if final:
        cmd.extend(["--cov-report=term-missing", "--cov-fail-under=90", "--durations=20"])
    else:
        # The project TOML sets fail_under=90 for the aggregate suite. A
        # partial chunk is intentionally below that threshold; enforce it only
        # on the final append pass.
        cmd.extend(["--cov-report=", "--cov-fail-under=0"])
    return cmd


def _run(
    project_root: Path,
    cmd: list[str],
    label: str,
    *,
    env: dict[str, str] | None = None,
    process_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    clock: Callable[[], float] = time.perf_counter,
) -> None:
    print(f"\n==> {label}")
    print(f"    $ {' '.join(shlex.quote(part) for part in cmd)}")
    start = clock()
    process_env = os.environ.copy()
    process_env.setdefault("MPLBACKEND", "Agg")
    process_env.setdefault("PYTHONUNBUFFERED", "1")
    process_env.setdefault("TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES", "2")
    if env:
        process_env.update(env)
    result = process_runner(
        cmd,
        cwd=project_root,
        env=process_env,
        text=True,
        check=False,
    )
    elapsed = clock() - start
    print(f"    status: {result.returncode}  elapsed: {elapsed:.1f}s")
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed with return code {result.returncode}")


def run_verification(
    project_root: Path,
    *,
    skip_chunks: bool = False,
    monolithic_coverage: bool = False,
    profile: VerificationProfile | None = None,
    command_runner: Callable[..., None] = _run,
) -> None:
    """Run verification, optionally applying a typed pytest profile."""
    refresh_cache = _RefreshCache()
    profile_args = _profile_marker_args(profile)
    preflight = [
        ("Compose manuscript sections", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        (
            "Validate compose contracts",
            ["uv", "run", "python", "scripts/compose_manuscript.py", "--validate-only", "--strict"],
        ),
        ("Run analytical sweep", ["uv", "run", "python", "scripts/run_analytical_sweep.py"]),
        ("Simulate SI T-maze", ["uv", "run", "python", "scripts/simulate_si_tmaze.py"]),
        ("Simulate SI graph-world", ["uv", "run", "python", "scripts/simulate_si_graph_world.py"]),
        ("Compute analysis statistics", ["uv", "run", "python", "scripts/compute_statistics.py"]),
        ("Render registered figures", ["uv", "run", "python", "scripts/generate_figures.py"]),
        ("Render belief animation", ["uv", "run", "python", "scripts/render_animation.py"]),
        ("Generate validation spine", ["uv", "run", "python", "scripts/generate_validation_spine.py"]),
        ("Generate toy sweep tracks", ["uv", "run", "python", "scripts/generate_toy_sweep_tracks.py"]),
        ("Generate formal interop tracks", ["uv", "run", "python", "scripts/generate_formal_interop_tracks.py"]),
        ("Generate integration audit", ["uv", "run", "python", "scripts/generate_integration_audit.py"]),
        ("Generate canonical sheaf tracks", ["uv", "run", "python", "scripts/generate_sheaf_tracks.py"]),
        ("Generate manuscript variables", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Settle post-figure fixed point", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Final compose before output gate", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Settle post-compose fixed point", ["uv", "run", "python", "scripts/z_generate_manuscript_variables.py"]),
        ("Settled final compose before output gate", ["uv", "run", "python", "scripts/compose_manuscript.py"]),
        ("Validate generated outputs", ["uv", "run", "python", "scripts/validate_outputs.py"]),
        ("Check documentation contract", ["uv", "run", "python", "scripts/check_documentation_contract.py", "--check"]),
        ("Generate method inventory", ["uv", "run", "python", "scripts/generate_method_inventory.py"]),
        ("Check method inventory", ["uv", "run", "python", "scripts/generate_method_inventory.py", "--check"]),
    ]
    for label, cmd in preflight:
        refresh_cache.run(project_root, cmd, label, command_runner)

    if not skip_chunks:
        for label, modules in _chunked_test_groups(project_root):
            command_runner(project_root, ["uv", "run", "pytest", *modules, *profile_args, "-q"], label)

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
        refresh_cache.run(project_root, cmd, label, command_runner)

    if monolithic_coverage:
        refresh_cache.run(
            project_root,
            [
                "uv",
                "run",
                "pytest",
                "tests/",
                "--cov=src",
                *profile_args,
                "--cov-fail-under=90",
                "--durations=20",
                "-q",
                "--maxfail=1",
            ],
            "Full suite coverage pass",
            command_runner,
        )
    else:
        coverage_groups = [(label, modules) for label, modules in _coverage_test_groups(project_root) if modules]
        for index, (label, modules) in enumerate(coverage_groups):
            refresh_cache.run(
                project_root,
                _coverage_command(
                    modules,
                    append=index > 0,
                    final=index == len(coverage_groups) - 1,
                    profile=profile,
                ),
                f"Coverage pass: {label}",
                command_runner,
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
        refresh_cache.run(project_root, cmd, label, command_runner)
