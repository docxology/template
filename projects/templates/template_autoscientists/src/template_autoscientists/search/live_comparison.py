"""Bounded real local coordination, paired baseline, and honest source custody."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from ..agents.live_domain import CoordinationBlocked, CoordinationFailed, LiveSettings
from ..agents.live_transport import LiveProposer, digest, write_json
from ..agents.live_custody import environment_identity, implementation_custody, platform_sources, verify_custody
from infrastructure.core.implementation_custody import source_file_manifest, source_file_digest
from .comparison import build_comparison_payload, build_objective, run_comparison
from .search import SearchConfig, run_search

SCHEMA = "template-autoscientists/local-coordination/1"


def _source_manifest(project_root: Path) -> dict[str, str]:
    manifest = {
        "project/src/" + key: value
        for key, value in source_file_manifest(project_root / "src", frozenset({".py"})).items()
    }
    manifest["project/pyproject.toml"] = source_file_digest(project_root / "pyproject.toml")
    manifest.update(
        {
            "project/scripts/" + key: value
            for key, value in source_file_manifest(project_root / "scripts", frozenset({".py"})).items()
        }
    )
    manifest.update({"platform/" + key: value for key, value in platform_sources().items()})
    active_package = Path(__file__).absolute().parents[1]
    manifest.update(
        {
            "active_producer/" + key: value
            for key, value in source_file_manifest(active_package, frozenset({".py"})).items()
        }
    )
    active_project = active_package.parent.parent
    if (active_project / "pyproject.toml").is_file():
        manifest.update(
            {
                "active_controller/" + key: value
                for key, value in source_file_manifest(active_project / "scripts", frozenset({".py"})).items()
            }
        )
    return manifest


def _fresh_directory(project_root: Path, output_dir: Path) -> Path:
    root = project_root.absolute()
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("project source cannot traverse symlinks")
    allowed = root / "output/.pipeline/local_coordination"
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    if not output_dir.is_relative_to(allowed) or output_dir == allowed or ".." in output_dir.parts:
        raise ValueError("live output must be a fresh run beneath output/.pipeline/local_coordination")
    cursor = output_dir
    while cursor != root:
        if cursor.is_symlink():
            raise ValueError("live output cannot traverse symlinks")
        cursor = cursor.parent
    if output_dir.exists():
        raise ValueError("live output already exists; select a fresh run directory")
    output_dir.mkdir(parents=True)
    return output_dir


def run_live_comparison(project_root: Path, output_dir: Path, settings: LiveSettings) -> Path:
    """Require real calls in both arms; never substitute the offline reference."""
    output_dir = _fresh_directory(project_root, output_dir)
    started = time.monotonic()
    deadline = started + settings.run_timeout_seconds
    arm_wall_clock_ceiling = min(
        settings.experiments_per_arm * settings.request_timeout_seconds, settings.run_timeout_seconds / 2
    )
    receipt_path = output_dir / "coordination_receipt.json"
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA,
        "status": "incomplete",
        "mode": "live",
        "execution_mode": "local_ollama_multistep_coordination",
        "settings": asdict(settings),
        "paid_integrations_used": False,
        "source_applied": False,
        "scope": "bounded numeric proposals on the public four-axis synthetic objective",
        "general_superiority_claim": False,
        "arms": {},
        "source_unchanged": False,
        "budget_contract": {
            "experiments_per_arm": settings.experiments_per_arm,
            "generation_calls_per_arm": settings.experiments_per_arm,
            "generation_tokens_ceiling_per_arm": settings.experiments_per_arm * settings.num_predict,
            "generation_time_ceiling_seconds_per_arm": settings.experiments_per_arm * settings.request_timeout_seconds,
            "arm_wall_clock_ceiling_seconds": arm_wall_clock_ceiling,
            "run_deadline_seconds": settings.run_timeout_seconds,
            "confirmation_evaluations_per_experiment": 3,
            "initial_confirmation_evaluations_per_arm": 3,
            "matched_ceilings_do_not_assert_equal_consumed_tokens": True,
        },
    }
    write_json(receipt_path, receipt)
    before: dict[str, str] | None = None
    proposers: dict[str, LiveProposer] = {}
    try:
        try:
            import infrastructure
            from infrastructure.llm.core.local_ollama import validate_local_endpoint
        except ImportError as exc:
            raise CoordinationBlocked("platform 4.1.0 is required for live coordination") from exc
        if infrastructure.__version__ != "4.1.0":
            raise CoordinationBlocked("live coordination requires platform 4.1.0")
        validate_local_endpoint(settings.endpoint)
        implementation_before = implementation_custody()
        platform_before = platform_sources()
        runtime_before = environment_identity()
        verify_custody(platform_before, runtime_before, implementation_before)
        before = _source_manifest(project_root.absolute())
        receipt["source_sha256"] = before
        receipt["runtime_environment"] = runtime_before
        receipt["implementation_custody"] = implementation_before
        receipt["loaded_implementation_verified"] = True
        write_json(receipt_path, receipt)
        objective = build_objective()
        results = {}
        for name, config in (
            (
                "coordinated",
                SearchConfig(budget=settings.experiments_per_arm, stagnation_window=3, dead_end_threshold=2),
            ),
            ("baseline", SearchConfig.single_thread_baseline(budget=settings.experiments_per_arm)),
        ):
            arm_started = time.monotonic()
            proposer = LiveProposer(
                settings,
                output_dir / name,
                min(deadline, arm_started + arm_wall_clock_ceiling),
                platform_sources=platform_before,
                runtime_environment=runtime_before,
                implementation=implementation_before,
            )
            proposers[name] = proposer
            result = run_search(objective, proposer, config)
            if len(result.log) != settings.experiments_per_arm:
                raise CoordinationFailed("an arm ended before the required matched experiment count")
            if any(p.model_sha256 != proposer.model_sha256 for p in proposers.values()):
                raise CoordinationFailed("both arms must use one identical installed model digest")
            results[name] = result
            for call, outcome in zip(proposer.calls, result.log, strict=True):
                call["outcome"] = asdict(outcome)
            arm = {
                "config": asdict(config),
                "champion": asdict(result.champion),
                "calls": proposer.calls,
                "generation_calls_used": len(proposer.calls),
                "generation_tokens_used": sum(call["eval_count"] for call in proposer.calls),
                "elapsed_seconds": time.monotonic() - arm_started,
                "objective_evaluations_used": 3 + 3 * len(result.log),
            }
            receipt["arms"][name] = arm
            write_json(output_dir / name / "transcript.json", arm)
            write_json(receipt_path, receipt)
        summary = build_comparison_payload(
            objective, results["coordinated"], results["baseline"], budget=settings.experiments_per_arm
        )
        advantage = cast(float, summary["clean_metric_advantage"])
        receipt.update(
            summary=summary,
            model_sha256=proposers["coordinated"].model_sha256,
            effect="positive" if advantage > 0 else "negative" if advantage < 0 else "null",
        )
        reference_a, reference_b = run_comparison(objective, budget=settings.experiments_per_arm)
        receipt["offline_reference"] = {
            "mode": "core",
            "actual_model_generations": 0,
            "comparison": build_comparison_payload(
                objective, reference_a, reference_b, budget=settings.experiments_per_arm
            ),
        }
        if time.monotonic() >= deadline:
            raise CoordinationBlocked("run deadline exhausted")
        for proposer in proposers.values():
            for call in proposer.calls:
                for relative, expected in call["artifacts"].items():
                    if digest(output_dir / relative) != expected:
                        raise CoordinationFailed("consumed provider artifact changed during the run")
        receipt["status"] = "passed"
    except CoordinationBlocked as exc:
        receipt.update(status="blocked", diagnostic=str(exc))
    except (CoordinationFailed, ValueError, OSError, KeyError, TypeError) as exc:
        receipt.update(status="failed", diagnostic=f"{type(exc).__name__}: {exc}")
    finally:
        for name, proposer in proposers.items():
            receipt["arms"].setdefault(name, {"calls": proposer.calls})
        if before is not None:
            try:
                verify_custody(platform_before, runtime_before, implementation_before)
                receipt["source_unchanged"] = before == _source_manifest(project_root.absolute())
            except (ValueError, OSError):
                receipt["source_unchanged"] = False
            if not receipt["source_unchanged"]:
                receipt.update(status="failed", diagnostic="source changed during live coordination")
        try:
            receipt["artifact_sha256"] = {
                key: value
                for key, value in source_file_manifest(output_dir, frozenset({".json"})).items()
                if key != "coordination_receipt.json"
            }
            if before is not None:
                verify_custody(platform_before, runtime_before, implementation_before)
                if before != _source_manifest(project_root.absolute()):
                    receipt.update(
                        status="failed",
                        source_unchanged=False,
                        diagnostic="source changed during final artifact custody",
                    )
            if receipt["status"] == "passed" and time.monotonic() >= deadline:
                receipt.update(status="blocked", diagnostic="run deadline exceeded during final custody checks")
        except (ValueError, OSError) as exc:
            receipt.update(status="failed", diagnostic=f"final artifact custody failed: {exc}")
        receipt["elapsed_seconds"] = time.monotonic() - started
        write_json(receipt_path, receipt)
        finished = time.monotonic()
        if receipt["status"] == "passed" and finished >= deadline:
            receipt.update(
                status="blocked",
                elapsed_seconds=finished - started,
                diagnostic="run deadline exceeded during receipt promotion",
            )
            write_json(receipt_path, receipt)
    return receipt_path


def live_exit_code(path: Path) -> int:
    """Expose required capability failure to the supervising pipeline."""
    status = json.loads(path.read_text())["status"]
    return 0 if status == "passed" else 75 if status == "blocked" else 1
