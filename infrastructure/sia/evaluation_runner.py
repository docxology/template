"""Run task evaluate.py scripts and normalize results.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from infrastructure.core.exceptions import BuildError, ValidationError
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

from .models import EvaluationResult

REQUIRED_RESULT_KEYS = ("metric_name", "metric_value", "n_samples")


def read_results_json(path: Path) -> EvaluationResult:
    """Parse and validate a results.json file."""
    if not path.is_file():
        raise ValidationError(f"results.json not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"results.json must be an object: {path}")
    missing = [key for key in REQUIRED_RESULT_KEYS if key not in payload]
    if missing:
        raise ValidationError(f"results.json missing keys {missing}: {path}")
    return EvaluationResult.from_dict(payload)


def write_results_json(path: Path, result: EvaluationResult) -> Path:
    """Write canonical results.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def run_evaluation(
    evaluate_script: Path,
    *,
    gen_dir: Path,
    task_dir: Path,
    timeout_sec: int = 120,
) -> EvaluationResult:
    """Execute evaluate.py with --gen-dir and read results.json.

    Args:
        evaluate_script: Path to data/public/evaluate.py.
        gen_dir: Generation directory passed to the script.
        task_dir: Task root for cwd resolution.
        timeout_sec: Subprocess timeout.

    Returns:
        Parsed EvaluationResult.

    Raises:
        BuildError: When the script exits non-zero or times out.
        ValidationError: When results.json is missing or invalid.
    """
    gen_dir = gen_dir.resolve()
    task_dir = task_dir.resolve()
    results_path = gen_dir / "results.json"

    cmd = [
        sys.executable,
        str(evaluate_script.resolve()),
        "--gen-dir",
        str(gen_dir),
    ]
    proc = run_with_policy(
        cmd,
        cwd=task_dir,
        env=None,
        policy=SubprocessPolicy(
            policy_id="sia-evaluation",
            source_path="infrastructure/sia/evaluation_runner.py",
            timeout_seconds=timeout_sec,
            capture_output=True,
            credential_free=True,
        ),
    )
    if proc.timed_out:
        raise BuildError(
            f"evaluate.py timed out after {timeout_sec}s "
            f"(script={evaluate_script.relative_to(task_dir)} gen_dir={gen_dir.name})"
        )
    if proc.returncode != 0:
        stderr_tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = stderr_tail[-1] if stderr_tail else "(no stderr)"
        raise BuildError(f"evaluate.py failed (exit {proc.returncode}, timeout={timeout_sec}s): {detail}")
    return read_results_json(results_path)


__all__ = [
    "read_results_json",
    "run_evaluation",
    "write_results_json",
]
