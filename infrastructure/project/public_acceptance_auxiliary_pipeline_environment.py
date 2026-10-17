"""Source components, confined environments and independent logical pipeline reads."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import math
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint_components
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def copy_public_pipeline_source(root: Path, destination: Path, reader: SnapshotReader) -> list[dict[str, Any]]:
    """Copy admitted bytes and executable roles; never export local Git metadata."""
    from infrastructure.reporting.readiness_receipts import public_source_paths

    files = []
    for path in public_source_paths(root):
        relative = path.relative_to(root).as_posix()
        snapshot = reader.read(relative)
        executable = bool(path.stat(follow_symlinks=False).st_mode & stat.S_IXUSR)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(snapshot.content)
        target.chmod(0o755 if executable else 0o644)
        files.append({"path": relative, "sha256": snapshot.sha256, "executable": executable})
    if not reader.unchanged():
        raise ValueError("public pipeline source changed during confined export")
    return files


_LABELS = (
    "PATH",
    "UV_PYTHON",
    "UV_OFFLINE",
    "COVERAGE_FILE",
    "HYPOTHESIS_STORAGE_DIRECTORY",
    "PYTHONPYCACHEPREFIX",
    "MPLCONFIGDIR",
    "TEMPLATE_SKIP_LINK_SYNC",
    "SOURCE_DATE_EPOCH",
    "TEMPLATE_ROOT_PYTHON",
    "PYTEST_ADDOPTS",
)


_SAFE_ENV = frozenset(
    {
        "HOME",
        "PATH",
        "TMPDIR",
        "TMP",
        "TEMP",
        "LANG",
        "TZ",
        "SOURCE_DATE_EPOCH",
        "UV_CACHE_DIR",
        "UV_PYTHON",
        "UV_OFFLINE",
        "UV_NO_SYNC",
        "UV_NO_MANAGED_PYTHON",
        "UV_PYTHON_DOWNLOADS",
        "PANDOC_PATH",
        "LATEX_COMPILER",
        "FORMAL_JAVA_BIN",
        "JAVA_HOME",
        "ELAN_HOME",
        "ELAN_TOOLCHAIN",
        "MPLBACKEND",
        "MPLCONFIGDIR",
        "PYTHONUNBUFFERED",
        "PYTHONIOENCODING",
        "PYTHONHASHSEED",
        "PYTHONPYCACHEPREFIX",
        "COVERAGE_FILE",
        "HYPOTHESIS_STORAGE_DIRECTORY",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "CI",
        "GITHUB_ACTIONS",
        "GITHUB_SHA",
        "GITHUB_REPOSITORY",
        "GITHUB_RUN_ID",
        "GITHUB_RUN_ATTEMPT",
        "TEXMFHOME",
        "TEXMFVAR",
        "TEXMFCACHE",
        "TTFONTS",
    }
)


def _clean_environment() -> dict[str, str]:
    from infrastructure.core.secrets import is_secret_env_name

    def admitted(name: str) -> bool:
        return (
            (name in _SAFE_ENV or name.startswith(("ANALYSIS_", "TEMPLATE_", "LC_")))
            and not is_secret_env_name(name)
            and "AUTH" not in name.upper()
            and "ACCESS_KEY" not in name.upper()
            and not name.startswith("TEMPLATE_PROJECT_LOCK_")
        )

    return {name: os.environ[name] for name in os.environ if admitted(name)}


def _read_logical_plan(
    root: Path, scope: str, budget: float, epoch: str, *, deadline: float | None = None
) -> dict[str, Any]:
    """Compile only current reader source in a fresh credential-free reader child."""
    from infrastructure.core.execution_policy import apply_execution_policy

    if deadline is not None and (type(deadline) not in (int, float) or not math.isfinite(deadline)):
        raise ValueError("logical pipeline reader requires a finite original deadline")
    end = min(time.monotonic() + 60, deadline) if deadline is not None else time.monotonic() + 60
    if time.monotonic() >= end:
        raise TimeoutError("original auxiliary deadline exhausted before logical reader admission")
    with tempfile.TemporaryDirectory(prefix="pipeline-logical-reader-") as temporary:
        directory = Path(temporary).resolve(strict=True)
        result_file = directory / "plan.json"
        from infrastructure.project.public_acceptance_auxiliary_bootstrap import (
            PIPELINE,
            prepare_audited_auxiliary_command,
        )

        command, _ = prepare_audited_auxiliary_command(
            Path(sys.executable),
            root,
            PIPELINE,
            ("--logical-root", str(root), "--scope", scope, "--budget", str(budget), "--result", str(result_file)),
            directory / "execution",
        )
        environment = _clean_environment()
        environment.update(SOURCE_DATE_EPOCH=epoch, UV_OFFLINE="1", UV_PYTHON=sys.executable)
        environment = apply_execution_policy(environment, root, mode="core")
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("original auxiliary deadline exhausted before logical reader launch")
        try:
            result = subprocess.run(
                command,
                cwd=root,
                env=environment,
                capture_output=True,
                timeout=remaining,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("logical pipeline reader exhausted its bounded original window") from error
        if time.monotonic() >= end:
            raise TimeoutError("original auxiliary deadline exhausted during logical reader execution")
        if result.returncode != 0 or not result_file.is_file() or result_file.stat().st_size > 16 * 1024 * 1024:
            raise ValueError(
                "independent logical pipeline reader failed: " + result.stderr.decode(errors="replace")[-1000:]
            )
        return dict(json.loads(result_file.read_text()))


def _components(root: Path, scope: str) -> dict[str, object]:
    from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source

    project = root / "projects" / scope
    declaration = resolve_pipeline_source(root, project, purpose=PipelinePurpose.EXECUTION).path
    return source_fingerprint_components(root, project, definition_path=declaration)


def _source_records(root: Path, scope: str) -> list[Any]:
    from infrastructure.core.pipeline.definition import PipelinePurpose, resolve_pipeline_source
    from infrastructure.core.pipeline.fingerprints import tree_records

    project = root / "projects" / scope
    declaration = resolve_pipeline_source(root, project, purpose=PipelinePurpose.EXECUTION).path
    paths = {
        root / "infrastructure",
        root / "scripts",
        project,
        declaration,
        *(root / name for name in ("pyproject.toml", "uv.lock", ".python-version", "pipeline.yaml")),
    }
    return [
        (
            path.relative_to(root).as_posix(),
            tree_records(path, source=True, excluded_roots=frozenset({(project / "output").absolute()})),
        )
        for path in sorted(paths)
    ]


def environment_observation(root: Path, scope: str) -> dict[str, Any]:
    from infrastructure.core.files.project_lock import _env_var, _lock_key
    from infrastructure.core.pipeline.execution_environment import VOLATILE_CONTROL_KEYS, environment_digest
    from infrastructure.core.pipeline.stages import build_stage_subprocess_env
    from infrastructure.core.secrets import is_secret_env_name

    project = root / "projects" / scope
    environment = build_stage_subprocess_env(root, project, mode="core")
    if any(is_secret_env_name(key) or key in {"SSH_AUTH_SOCK", "GPG_AGENT_INFO"} for key in environment):
        raise ValueError("pipeline child environment contains protected credential names")
    excluded = VOLATILE_CONTROL_KEYS | {_env_var(_lock_key(project))}
    hashes = {
        key: hashlib.sha256(value.encode()).hexdigest() for key, value in environment.items() if key not in excluded
    }
    return {
        "aggregate_digest": environment_digest(environment, project_dir=project),
        "key_hashes": hashes,
        "key_hashes_digest": canonical_digest(hashes),
        "labels": {key: environment[key] for key in _LABELS if key in environment},
    }
