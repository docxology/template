"""Finite, source-owned project review coordination using the platform guardian."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import signal
import stat
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import yaml

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_text_confined
from infrastructure.core.subprocess_policy import BoundedSubprocessResult, SubprocessPolicy, run_with_policy

DEFAULT_REVIEW_TIMEOUT = 1800.0
DEFAULT_STAGE_TIMEOUT = 300.0
DEFAULT_PROJECT_MIN_COVERAGE = 90.0
REVIEW_RECORD_SCHEMA_VERSION = 1
_POLICY_SOURCE = "projects/templates/template_search_project/src/template_search_project/analysis/review_execution.py"


def positive_timeout(value: str | float) -> float:
    """Admit only positive finite budgets; bool is never a numeric timeout."""
    if isinstance(value, bool):
        raise argparse.ArgumentTypeError("timeout must be positive and finite")
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("timeout must be positive and finite") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("timeout must be positive and finite")
    return timeout


def run_review_child(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = DEFAULT_STAGE_TIMEOUT,
    policy_id: str = "search-review-stage",
) -> BoundedSubprocessResult:
    """Keep original process codes and the shared guardian's truthful outcome."""
    result = run_with_policy(
        argv,
        cwd=cwd,
        env=env,
        policy=SubprocessPolicy(
            policy_id=policy_id,
            source_path=_POLICY_SOURCE,
            timeout_seconds=positive_timeout(timeout),
            check=False,
        ),
    )

    # The primitive guardian retains killed child codes; this CLI applies its
    # canonical policy while preserving those original observations separately.
    interrupted = result.original_returncode in (-signal.SIGINT, 130) or result.returncode in (-signal.SIGINT, 130)
    code = 130 if interrupted else (124 if result.timed_out else result.returncode)
    return BoundedSubprocessResult(
        result.argv,
        code,
        result.timed_out,
        result.stdout,
        result.stderr,
        result.command_error,
        result.custody_refused,
        result.original_returncode,
    )


def child_observation(result: BoundedSubprocessResult) -> dict:
    """Separate actual child codes from timeout, launch, and custody failures."""
    return {
        "exit_code": result.returncode,
        "original_exit_code": result.original_returncode,
        "timed_out": result.timed_out,
        "interrupted": result.returncode == 130,
        "custody_refused": result.custody_refused,
        "command_error": result.command_error,
    }


@dataclass(frozen=True)
class ReviewStage:
    """Resolved own-review stage; configuration extras are descriptive only."""

    name: str
    enabled: bool
    kind: str
    module: str = ""
    command: str = ""
    args: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class ReviewPlan:
    """One selected domain review with a monotonic whole-operation deadline."""

    run_id: str
    project_root: str
    project_root_identity: tuple[int, int]
    own_source_root: str
    stages: tuple[ReviewStage, ...]
    output_dir: str
    summary_json: str
    fail_fast: bool
    stage_timeout: float
    deadline_monotonic: float
    schema_version: int = REVIEW_RECORD_SCHEMA_VERSION

    def encode(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @classmethod
    def decode(cls, value: str) -> ReviewPlan:
        payload = json.loads(value)
        if (
            not isinstance(payload, dict)
            or type(payload.get("schema_version")) is not int
            or payload["schema_version"] != REVIEW_RECORD_SCHEMA_VERSION
        ):
            raise ValueError("unsupported review plan schema; resolve a fresh review")
        payload["project_root_identity"] = tuple(payload["project_root_identity"])
        payload["stages"] = tuple(ReviewStage(**{**row, "args": tuple(row["args"])}) for row in payload["stages"])
        return cls(**payload)

    @property
    def plan_sha256(self) -> str:
        return hashlib.sha256(self.encode().encode("utf-8")).hexdigest()

    def remaining(self) -> float:
        return self.deadline_monotonic - time.monotonic()


def _relative_output(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must remain within the project")
    return value


def review_stage_key(row: dict, names: set[str]) -> str:
    """Use one stable public key/enablement contract across review views."""
    name = row.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", name) or name in names:
        raise ValueError("review stage names must be unique stable file-safe keys")
    if type(row.get("enabled", True)) is not bool:
        raise ValueError(f"review stage {name!r} enabled must be boolean")
    return name


def review_output_settings(review: dict, names: set[str]) -> tuple[str, str]:
    """Resolve local-only operational records separately from public reports."""
    output = review.get("output", {})
    if not isinstance(output, dict):
        raise ValueError("review output configuration must be a mapping")
    output_dir = _relative_output(output.get("dir", "output/.pipeline/review"), "output directory")
    if Path(output_dir).parts[:2] != ("output", ".pipeline") or len(Path(output_dir).parts) < 3:
        raise ValueError("operational review output must be below output/.pipeline/")
    summary = _relative_output(output.get("summary_json", "summary.json"), "summary filename")
    if len(Path(summary).parts) != 1:
        raise ValueError("summary filename must be one filename")
    if summary in {f"stage_{name}.json" for name in names}:
        raise ValueError("summary filename collides with a configured stage record")
    return output_dir, summary


def resolve_plan(
    project_root: Path,
    own_source_root: Path,
    *,
    selected: list[str] | None,
    fail_fast: bool,
    stage_timeout: float,
    deadline_monotonic: float,
) -> ReviewPlan:
    """Reject malformed declarations and unknown selections before execution."""
    from .analysis import REVIEW_STAGE_FUNCTIONS

    project = project_root.resolve(strict=True)
    source = own_source_root.resolve(strict=True)
    if not project.is_dir() or not source.is_dir():
        raise ValueError("project data and own source roots must be directories")
    project_stat = project.stat()
    project_identity = (project_stat.st_dev, project_stat.st_ino)
    config = (
        yaml.safe_load(
            read_text_confined(project, project / "review_config.yaml", expected_root_identity=project_identity)
        )
        or {}
    )
    if not isinstance(config, dict) or not isinstance(config.get("review", {}), dict):
        raise ValueError("review configuration must be a mapping")
    review = config.get("review", {})
    rows = review.get("stages", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("review stages must be a nonempty list")
    stages: list[ReviewStage] = []
    names: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each review stage must be a mapping")
        name = review_stage_key(row, names)
        enabled = row.get("enabled", True)
        names.add(name)
        module = row.get("infra_module", "")
        custom = row.get("stage_type") == "custom"
        arguments = row.get("args", [])
        description = row.get("description", "")
        if not isinstance(arguments, list) or any(not isinstance(argument, str) for argument in arguments):
            raise ValueError(f"review stage {name!r} args must be strings")
        if not isinstance(description, str):
            raise ValueError(f"review stage {name!r} description must be text")
        if bool(module) == custom:
            raise ValueError(f"review stage {name!r} needs exactly one infra or custom target")
        if module:
            command = row.get("command", "")
            if not isinstance(module, str) or not module.startswith("infrastructure."):
                raise ValueError(f"review stage {name!r} must name an infrastructure module")
            if not isinstance(command, str) or not command:
                raise ValueError(f"review stage {name!r} requires a command")
            stage = ReviewStage(name, enabled, "infra", module, command, tuple(arguments), description)
        else:
            if name not in REVIEW_STAGE_FUNCTIONS:
                raise ValueError(f"unknown custom review stage {name!r}")
            actual_module = "template_search_project.analysis.analysis"
            actual_function = REVIEW_STAGE_FUNCTIONS[name].__name__
            if (
                row.get("module", actual_module) != actual_module
                or row.get("function", actual_function) != actual_function
            ):
                raise ValueError(f"review stage {name!r} declaration differs from actual dispatch")
            if arguments:
                raise ValueError(f"review stage {name!r} does not consume custom arguments")
            stage = ReviewStage(name, enabled, "custom", actual_module, actual_function, description=description)
        stages.append(stage)
    if selected:
        missing = sorted(set(selected) - names)
        if missing:
            raise ValueError("Unknown stage(s): " + ", ".join(missing))
        stages = [stage for stage in stages if stage.name in set(selected)]
    output_dir, summary = review_output_settings(review, names)
    return ReviewPlan(
        uuid.uuid4().hex,
        str(project),
        project_identity,
        str(source),
        tuple(stages),
        output_dir,
        summary,
        fail_fast,
        positive_timeout(stage_timeout),
        deadline_monotonic,
    )


def _out_dir(plan: ReviewPlan) -> Path:
    root = Path(plan.project_root)
    observed = root.stat(follow_symlinks=False)
    if not stat.S_ISDIR(observed.st_mode) or (observed.st_dev, observed.st_ino) != plan.project_root_identity:
        raise ValueError("project data root changed after review resolution")
    directory = root / plan.output_dir
    if any(path.is_symlink() for path in (directory, *directory.parents) if path != root and path.is_relative_to(root)):
        raise ValueError("review output directory must not traverse a symlink")
    return directory


def _validate_output_files(plan: ReviewPlan) -> None:
    directory = _out_dir(plan)
    for target in (directory / plan.summary_json, *(directory / f"stage_{stage.name}.json" for stage in plan.stages)):
        if target.is_symlink() or target.is_dir():
            raise ValueError("review output file must be a regular owned path")


def _write_record(plan: ReviewPlan, target: Path, value: dict) -> None:
    atomic_write_text_confined(
        Path(plan.project_root),
        target,
        json.dumps(value, indent=2) + "\n",
        expected_root_identity=plan.project_root_identity,
    )


def _read_record(plan: ReviewPlan, target: Path) -> dict:
    value = json.loads(
        read_text_confined(Path(plan.project_root), target, expected_root_identity=plan.project_root_identity)
    )
    if not isinstance(value, dict):
        raise ValueError("review record must be a mapping")
    return value


def _summary(plan: ReviewPlan, results: list[dict], *, execution_exit_code: int, complete: bool) -> dict:
    failed = sum(1 for result in results if not result.get("success") and result.get("status") != "skipped")
    return {
        "schema_version": REVIEW_RECORD_SCHEMA_VERSION,
        "total": len(results),
        "passed": sum(1 for result in results if result.get("success")),
        "failed": failed,
        "skipped": sum(1 for result in results if result.get("status") == "skipped"),
        "overall_exit_code": 0 if complete and failed == 0 and execution_exit_code == 0 else 1,
        "execution_exit_code": execution_exit_code,
        "run_id": plan.run_id,
        "plan_sha256": plan.plan_sha256,
        "expected_stages": [stage.name for stage in plan.stages],
        "complete": complete,
    }


def _write_summary(plan: ReviewPlan, results: list[dict], *, code: int, complete: bool) -> dict:
    summary = _summary(plan, results, execution_exit_code=code, complete=complete)
    _write_record(plan, _out_dir(plan) / plan.summary_json, summary)
    return summary


def _custom_payload_valid(value: object, stage: ReviewStage) -> bool:
    if not (
        isinstance(value, dict)
        and value.get("name") == stage.name
        and value.get("status") == "passed"
        and type(value.get("exit_code")) is int
        and value["exit_code"] == 0
        and isinstance(value.get("details"), dict)
    ):
        return False
    if stage.name == "test_suite_health":
        details = value["details"]
        nested = details.get("execution")
        coverage = details.get("coverage")
        if not (
            isinstance(nested, dict)
            and type(nested.get("exit_code")) is int
            and nested["exit_code"] == 0
            and type(nested.get("original_exit_code")) is int
            and nested["original_exit_code"] == 0
            and nested.get("timed_out") is False
            and nested.get("custody_refused") is False
            and nested.get("interrupted") is False
            and nested.get("command_error") == ""
            and type(coverage) is int
            and DEFAULT_PROJECT_MIN_COVERAGE <= coverage <= 100
        ):
            return False
    return True


def _successful_stage_set(plan: ReviewPlan, summary: dict) -> bool:
    """Recheck current bound stage records before allowing a complete result."""
    counts = {
        "total": len(plan.stages),
        "passed": sum(stage.enabled for stage in plan.stages),
        "failed": 0,
        "skipped": sum(not stage.enabled for stage in plan.stages),
    }
    if any(type(summary.get(key)) is not int or summary[key] != value for key, value in counts.items()):
        return False
    for stage in plan.stages:
        if not stage.enabled:
            continue
        path = _out_dir(plan) / f"stage_{stage.name}.json"
        if path.is_symlink():
            return False
        try:
            record = _read_record(plan, path)
        except OSError, ValueError:
            return False
        if not isinstance(record, dict) or (
            type(record.get("schema_version")) is not int
            or record["schema_version"] != REVIEW_RECORD_SCHEMA_VERSION
            or record.get("name") != stage.name
            or record.get("type") != stage.kind
            or record.get("run_id") != plan.run_id
            or record.get("plan_sha256") != plan.plan_sha256
            or record.get("success") is not True
            or type(record.get("exit_code")) is not int
            or record["exit_code"] != 0
            or type(record.get("original_exit_code")) is not int
            or record["original_exit_code"] != 0
            or record.get("timed_out") is not False
            or record.get("custody_refused") is not False
            or record.get("interrupted") is not False
            or record.get("command_error") != ""
        ):
            return False
        if stage.kind == "infra":
            if (record.get("module"), record.get("command"), record.get("args")) != (
                stage.module,
                stage.command,
                list(stage.args),
            ):
                return False
        elif not _custom_payload_valid(record.get("result"), stage) or record.get("domain_error"):
            return False
    return True


def run_stage(stage: ReviewStage, plan: ReviewPlan) -> dict:
    """Preserve the existing infra/custom classification and actual child code."""
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    if stage.kind == "infra":
        command = [sys.executable, "-I", "-m", stage.module, stage.command, *stage.args]
    else:
        bootstrap = (
            "import infrastructure,runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
            "runpy.run_module('template_search_project.analysis.analysis',run_name='__main__')"
        )
        command = [
            sys.executable,
            "-I",
            "-c",
            bootstrap,
            plan.own_source_root,
            "--stage",
            stage.name,
            "--project-root",
            plan.project_root,
        ]
    remaining = plan.remaining()
    if remaining <= 0:
        result = BoundedSubprocessResult(
            tuple(command), 124, True, command_error="review deadline expired before stage launch"
        )
    else:
        result = run_review_child(
            command, cwd=Path(plan.project_root), env=environment, timeout=min(plan.stage_timeout, remaining)
        )
    response = {
        "schema_version": REVIEW_RECORD_SCHEMA_VERSION,
        "name": stage.name,
        "type": stage.kind,
        "run_id": plan.run_id,
        "plan_sha256": plan.plan_sha256,
        **child_observation(result),
        "stdout": result.stdout[-1000:] if stage.kind == "infra" else result.stdout[-500:],
        "stderr": result.stderr[-500:] if stage.kind == "infra" else result.stderr[-200:],
        "success": result.returncode == 0 and not result.timed_out and not result.custody_refused,
    }
    if stage.kind == "infra":
        response.update(module=stage.module, command=stage.command, args=list(stage.args))
    else:
        parsed = {}
        if result.returncode in (0, 1) and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError:
                parsed = {"raw_stdout": result.stdout[:200]}
        response["result"] = parsed
        response["domain_error"] = ""
        if result.returncode == 0 and not _custom_payload_valid(parsed, stage):
            response.update(
                success=False, domain_error="custom stage returned zero without a valid matching domain result"
            )
        if stage.name == "test_suite_health" and isinstance(parsed, dict) and isinstance(parsed.get("details"), dict):
            nested = parsed["details"].get("execution")
            if isinstance(nested, dict):
                response["nested_execution"] = nested
                if nested.get("interrupted") is True:
                    response.update(exit_code=130, interrupted=True, success=False)
                elif nested.get("timed_out") is True:
                    response.update(exit_code=124, timed_out=True, success=False)
                elif nested.get("custody_refused") is True:
                    response.update(exit_code=75, custody_refused=True, success=False)
    return response


def execute_plan(plan: ReviewPlan) -> int:
    """Run only the resolved stages; all reporting is inside the outer guardian."""
    results: list[dict] = []
    code = 0
    for stage in plan.stages:
        if not stage.enabled:
            result = {"name": stage.name, "status": "skipped", "message": "disabled", "run_id": plan.run_id}
        else:
            result = run_stage(stage, plan)
            _write_record(plan, _out_dir(plan) / f"stage_{stage.name}.json", result)
            if result["interrupted"]:
                code = 130
            elif result["timed_out"] and code != 130:
                code = 124
            elif result["custody_refused"] and code != 124:
                code = 75 if code == 0 else code
            elif not result["success"] and code not in (130, 124, 1):
                code = 1
        results.append(result)
        _write_summary(plan, results, code=code or 1, complete=False)
        if plan.remaining() <= 0:
            code = 130 if code == 130 else 124
            break
        if (
            result.get("interrupted")
            or result.get("timed_out")
            or result.get("custody_refused")
            or (not result.get("success") and result.get("status") != "skipped" and plan.fail_fast)
        ):
            break
    complete = len(results) == len(plan.stages) and code == 0 and plan.remaining() > 0
    if not complete and code == 0:
        code = 124 if plan.remaining() <= 0 else 1
    summary = _write_summary(plan, results, code=code, complete=complete)
    print(f"\nReview: {summary['passed']} passed, {summary['failed']} failed, {summary['skipped']} skipped")
    for result in results:
        icon = "✓" if result.get("success") else ("○" if result.get("status") == "skipped" else "✗")
        print(f"  {icon} {result['name']}")
    return code


def _finalize_execution(plan: ReviewPlan, result: BoundedSubprocessResult) -> BoundedSubprocessResult:
    """Bind the final summary to this run and the guardian's completed cleanup."""
    summary_path = _out_dir(plan) / plan.summary_json
    try:
        summary = _read_record(plan, summary_path)
    except OSError, ValueError:
        summary = {}
    valid = (
        isinstance(summary, dict)
        and type(summary.get("schema_version")) is int
        and summary["schema_version"] == REVIEW_RECORD_SCHEMA_VERSION
        and summary.get("run_id") == plan.run_id
        and summary.get("plan_sha256") == plan.plan_sha256
        and summary.get("expected_stages") == [stage.name for stage in plan.stages]
    )
    if not valid:
        summary = _summary(plan, [], execution_exit_code=1, complete=False)
    if result.returncode == 0 and (
        not valid
        or summary.get("complete") is not True
        or type(summary.get("overall_exit_code")) is not int
        or summary["overall_exit_code"] != 0
        or type(summary.get("execution_exit_code")) is not int
        or summary["execution_exit_code"] != 0
        or not _successful_stage_set(plan, summary)
    ):
        result = BoundedSubprocessResult(
            result.argv,
            1,
            False,
            result.stdout,
            result.stderr,
            "review worker returned success without the complete bound stage set",
            result.custody_refused,
            result.original_returncode,
        )
    if plan.remaining() <= 0 and result.returncode != 130:
        result = BoundedSubprocessResult(
            result.argv,
            124,
            True,
            result.stdout,
            result.stderr,
            "whole-review reporting deadline exhausted",
            result.custody_refused,
            result.original_returncode,
        )
    if result.returncode != 0 or result.timed_out or result.custody_refused:
        summary.update(overall_exit_code=1, complete=False)
    summary["execution_exit_code"] = result.returncode
    summary["execution"] = child_observation(result)
    _write_record(plan, summary_path, summary)
    if result.returncode == 0 and plan.remaining() <= 0:
        result = BoundedSubprocessResult(
            result.argv,
            124,
            True,
            result.stdout,
            result.stderr,
            "whole-review reporting deadline exhausted",
            result.custody_refused,
            result.original_returncode,
        )
        summary.update(
            overall_exit_code=1, complete=False, execution_exit_code=124, execution=child_observation(result)
        )
        _write_record(plan, summary_path, summary)
    return result


def launch_plan(plan: ReviewPlan) -> BoundedSubprocessResult:
    """Supervise stages and reporting, reserving part of the original deadline."""
    _write_summary(plan, [], code=1, complete=False)
    bootstrap = (
        "import infrastructure,sys;sys.path.insert(0,sys.argv.pop(1));"
        "from template_search_project.analysis.review_execution import ReviewPlan,execute_plan;"
        "raise SystemExit(execute_plan(ReviewPlan.decode(sys.argv[1])))"
    )
    command = [sys.executable, "-I", "-c", bootstrap, plan.own_source_root, plan.encode()]
    remaining = plan.remaining()
    # Keep final outcome recording within the same deadline, after guardian cleanup.
    reporting_reserve = min(5.0, max(0.0, remaining * 0.05))
    if remaining <= 0:
        result = BoundedSubprocessResult(
            tuple(command), 124, True, command_error="review deadline expired before worker launch"
        )
    else:
        try:
            result = run_review_child(
                command,
                cwd=Path(plan.project_root),
                timeout=remaining - reporting_reserve,
                policy_id="search-review-whole",
            )
        except KeyboardInterrupt:
            _finalize_execution(
                plan,
                BoundedSubprocessResult(
                    tuple(command), 130, False, command_error="review interrupted after guardian cleanup"
                ),
            )
            raise
    return _finalize_execution(plan, result)


def review_cli(own_source_root: Path, argv: list[str] | None = None) -> int:
    """Canonical CLI: invalid input exits 2 before any worker or stage executes."""
    started = time.monotonic()
    parser = argparse.ArgumentParser(description="Unified project-specific review orchestration")
    parser.add_argument("--project-root", default=str(own_source_root.parent))
    parser.add_argument("--stage", action="append")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--list", action="store_true", dest="list_stages")
    parser.add_argument("--timeout", type=positive_timeout, default=DEFAULT_REVIEW_TIMEOUT)
    parser.add_argument("--stage-timeout", type=positive_timeout, default=DEFAULT_STAGE_TIMEOUT)
    args = parser.parse_args(argv)
    try:
        plan = resolve_plan(
            Path(args.project_root),
            own_source_root,
            selected=args.stage,
            fail_fast=args.fail_fast,
            stage_timeout=args.stage_timeout,
            deadline_monotonic=started + args.timeout,
        )
        if args.list_stages:
            print("Configured review stages:")
            for stage in plan.stages:
                print(f"  [{'✓' if stage.enabled else '✗'}] {stage.name}: {stage.description}")
            return 0
        _validate_output_files(plan)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    try:
        result = launch_plan(plan)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print(f"review execution failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.command_error:
        print(result.command_error, file=sys.stderr)
    return result.returncode
