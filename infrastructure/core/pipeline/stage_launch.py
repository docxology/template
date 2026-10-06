"""Fresh Python stage supervision and source-bound original exit receipts."""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_content_fingerprint
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.skip_receipts import validate_skip_receipt
from infrastructure.core.runtime.python_binding import admitted_runtime_report

SCHEMA = "template-python-stage/3"
ANALYSIS_SCHEMA = "template-python-analysis/2"

_BOOTSTRAP = (
    "import runpy,sys;sys.dont_write_bytecode=False;"
    "sys.path.insert(0,sys.argv.pop(1));"
    "runpy.run_module('infrastructure.core.pipeline.stage_worker',run_name='__main__')"
)


def launch_python_stage(
    *,
    repo: Path,
    project: Path,
    argv: list[str],
    env: dict[str, str],
    deadline: float,
    stage_key: str,
    run_id: str,
    source_digest: str,
    definition: Path | None,
    skip_path: Path,
    allow_skip: bool,
    interpreter: Path | None = None,
    analysis_runtime: dict[str, object] | None = None,
    analysis_receipt: dict[str, object] | None = None,
    cwd: Path | None = None,
    stage_admission: dict[str, object] | None = None,
) -> StageOutcome:
    """Only an actual fresh worker receipt may authorize stage success or skip."""
    if cwd is not None and not isinstance(cwd, Path):
        raise ValueError("Stage working directory must be a Path")
    working_directory = (repo if cwd is None else cwd).absolute()
    if ".." in working_directory.parts or working_directory not in {repo.absolute(), project.absolute()}:
        raise ValueError("Stage working directory must be its admitted repository or project")
    original: int | None = None
    admitted: dict[str, object] | None = None
    receipt_error = ""
    with tempfile.TemporaryDirectory(prefix="template-python-stage-") as temporary:
        scratch = Path(temporary).resolve()
        prefix = scratch / "bytecode"
        prefix.mkdir(mode=0o700)
        payload: dict[str, object] = {
            "schema": ANALYSIS_SCHEMA if analysis_runtime is not None else SCHEMA,
            "repo_root": str(repo),
            "project_root": str(project),
            "argv": argv[1:],
            "source_digest": source_digest,
            "definition": str(definition) if definition is not None else None,
            "run_id": run_id,
            "stage_key": stage_key,
            "cwd": str(working_directory),
            "stage_admission": stage_admission,
            "plan_digest": env.get("PIPELINE_PLAN_DIGEST", ""),
        }
        if analysis_runtime is not None:
            payload.update(
                source_content_digest=source_content_fingerprint(repo, project, definition_path=definition),
                runtime_binding=analysis_runtime,
                runtime_digest=canonical_digest(analysis_runtime),
            )
        digest = canonical_digest(payload)
        request = scratch / "request.json"
        atomic_write_text_confined(scratch, request, json.dumps(payload, sort_keys=True), mode=0o600)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return StageOutcome(stage_key, StageStatus.TIMED_OUT, None, "Deadline expired before stage launch")
        selected_env = dict(env, PYTHONPYCACHEPREFIX=str(prefix))
        selected_env.pop("PYTHONDONTWRITEBYTECODE", None)
        worker = Path(__file__).with_name("stage_worker.py")
        implementation_root = worker.parents[3]
        bootstrap = (
            bytecode_audit_bootstrap(
                (implementation_root / "infrastructure", repo / "scripts", project / "src", project / "scripts"),
                prefix,
            )
            + _BOOTSTRAP
        )
        child = run_bounded_subprocess(
            [
                str(interpreter) if interpreter is not None else sys.executable,
                "-I",
                "-X",
                f"pycache_prefix={prefix}",
                "-c",
                bootstrap,
                str(implementation_root),
                str(request),
                digest,
            ],
            cwd=working_directory,
            env=selected_env,
            timeout=remaining,
            capture_output=False,
        )
        observed = child.original_returncode if child.original_returncode is not None else child.returncode
        try:
            receipt = json.loads(read_bytes_confined(scratch, scratch / "result.json", max_bytes=64 * 1024))
            fields = {"schema", "request_digest", "run_id", "stage_key", "custody", "original_exit_code", "diagnostic"}
            if analysis_runtime is not None:
                fields.update({"source_content_digest", "runtime_digest", "actual_runtime", "plan_digest"})
            if (
                not isinstance(receipt, dict)
                or set(receipt) != fields
                or receipt["schema"] != payload["schema"]
                or receipt["request_digest"] != digest
                or receipt["run_id"] != run_id
                or receipt["stage_key"] != stage_key
                or receipt["custody"] not in {"verified", "blocked"}
                or not isinstance(receipt["diagnostic"], str)
                or (
                    receipt["original_exit_code"] is not None
                    and (
                        type(receipt["original_exit_code"]) is not int or not 0 <= receipt["original_exit_code"] <= 255
                    )
                )
                or (receipt["custody"] == "verified" and receipt["original_exit_code"] is None)
                or observed != (75 if receipt["custody"] == "blocked" else receipt["original_exit_code"])
            ):
                raise ValueError("Python stage receipt does not match actual worker completion")
            if analysis_runtime is not None:
                if (
                    receipt["source_content_digest"] != payload["source_content_digest"]
                    or receipt["runtime_digest"] != payload["runtime_digest"]
                    or receipt["plan_digest"] != payload["plan_digest"]
                    or (
                        receipt["custody"] == "verified"
                        and not admitted_runtime_report(receipt["actual_runtime"], analysis_runtime)
                    )
                ):
                    raise ValueError("Analysis receipt lacks its admitted actual runtime/source identity")
            admitted, original = receipt, receipt["original_exit_code"]
            if analysis_receipt is not None and analysis_runtime is not None:
                analysis_receipt.update(request=payload, completion=receipt)
        except (OSError, ValueError) as exc:
            receipt_error = str(exc)
    custody_diagnostic = (
        str(admitted["diagnostic"]) if admitted is not None and admitted["custody"] == "blocked" else ""
    )
    if child.custody_refused and child.command_error:
        custody_diagnostic = "; ".join(filter(None, (custody_diagnostic, child.command_error)))
    attempts = (original,) if analysis_runtime is not None and admitted is not None and original is not None else ()
    if observed in {130, -2} or (admitted is not None and original == 130):
        interruption = (
            "Analysis script exited 130 (interruption convention)"
            if analysis_runtime is not None and admitted is not None and original == 130
            else "Python stage was interrupted"
        )
        return StageOutcome(
            stage_key,
            StageStatus.INTERRUPTED,
            original if admitted else child.original_returncode,
            interruption + (f"; {custody_diagnostic}" if custody_diagnostic else ""),
            attempt_exit_codes=attempts,
        )
    if child.timed_out or time.monotonic() >= deadline or (admitted is not None and original == 124):
        timeout = (
            "Analysis script exited 124 (timeout convention)"
            if analysis_runtime is not None
            and admitted is not None
            and original == 124
            and not child.timed_out
            and time.monotonic() < deadline
            else "Python stage timeout"
        )
        return StageOutcome(
            stage_key,
            StageStatus.TIMED_OUT,
            original if admitted else child.original_returncode,
            timeout + (f"; {custody_diagnostic}" if custody_diagnostic else ""),
            attempt_exit_codes=attempts,
        )
    if child.custody_refused:
        state = StageStatus.FAILED if admitted is not None and original not in {None, 0, 75} else StageStatus.BLOCKED
        return StageOutcome(
            stage_key,
            state,
            original if admitted else child.original_returncode,
            child.command_error,
            attempt_exit_codes=attempts,
        )
    if child.command_error or admitted is None:
        return StageOutcome(
            stage_key,
            StageStatus.FAILED,
            original if admitted else child.original_returncode,
            child.command_error or f"Python stage has no valid completion receipt: {receipt_error}",
            attempt_exit_codes=attempts,
        )
    if admitted["custody"] == "blocked":
        # Source refusal prevents completion, but cannot demote the positively
        # recorded interruption, timeout, or failure of the executed script.
        state = StageStatus.BLOCKED if original in {None, 0, 75} else StageStatus.FAILED
        return StageOutcome(stage_key, state, original, str(admitted["diagnostic"]), attempt_exit_codes=attempts)
    if original == 0:
        return StageOutcome(stage_key, StageStatus.SUCCEEDED, 0, attempt_exit_codes=attempts)
    if allow_skip and original == 2:
        receipt = validate_skip_receipt(skip_path, env=env)
        if receipt is not None:
            reason, diagnostic = receipt
            return StageOutcome(stage_key, StageStatus.SKIPPED, 2, diagnostic, reason=reason, receipt_validated=True)
    state = StageStatus.BLOCKED if original == 75 else StageStatus.TIMED_OUT if original == 124 else StageStatus.FAILED
    return StageOutcome(stage_key, state, original, f"Stage script exited {original}", attempt_exit_codes=attempts)


__all__ = ["launch_python_stage"]
