"""Execute a declared Python stage with fresh caches and checked source custody."""

from __future__ import annotations

import json
import os
import hashlib
import sys
import traceback
from contextlib import ExitStack
from types import ModuleType
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.analysis_data_custody import capture_analysis_data, require_analysis_data
from infrastructure.core.analysis_read_custody import observe_stage_analysis_reads
from infrastructure.core.analysis_write_custody import observe_stage_analysis_writes
from infrastructure.core.implementation_custody import source_file_digest, verify_fresh_module_bytecode
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint, source_content_fingerprint
from infrastructure.core.pipeline.stage_launch import SCHEMA, ANALYSIS_SCHEMA
from infrastructure.core.runtime.python_binding import admit_current_analysis_runtime
from infrastructure.core.pipeline.stage_admission import validate_stage_admission


def main() -> int:
    """Retain the script exit while refusing unbound source or bytecode."""
    request, expected_digest = Path(sys.argv[1]), sys.argv[2]
    scratch = request.parent
    protocol = sys.argv[3] if len(sys.argv) == 4 else "stage"
    if protocol not in {"analysis", "stage"}:
        raise ValueError("Python stage protocol differs from its actual controller argv")
    ceiling = 16 * 1024 * 1024 if protocol == "analysis" else 1024 * 1024
    payload = json.loads(read_bytes_confined(scratch, request, max_bytes=ceiling))
    if (
        not isinstance(payload, dict)
        or canonical_digest(payload) != expected_digest
        or payload.get("schema") not in {SCHEMA, ANALYSIS_SCHEMA}
        or (payload.get("schema") == ANALYSIS_SCHEMA) != (protocol == "analysis")
    ):
        raise ValueError("Python stage request does not match its controller")
    repo, project = Path(payload["repo_root"]), Path(payload["project_root"])
    cwd = payload.get("cwd")
    if (
        not isinstance(cwd, str)
        or ".." in Path(cwd).parts
        or cwd not in {str(repo.absolute()), str(project.absolute())}
        or Path.cwd() != Path(cwd)
    ):
        raise ValueError("Actual stage working directory differs from its admitted request")
    definition = Path(payload["definition"]) if payload["definition"] is not None else None
    prefix = Path(sys.pycache_prefix or "")
    if sys.pycache_prefix is None or prefix != scratch / "bytecode":
        raise ValueError("Python stage did not use its private launcher cache")
    # Preserve the resolved stage environment's declared import paths. -I keeps
    # ambient Python startup options from overriding the trusted bootstrap.
    for location in reversed(os.environ.get("PYTHONPATH", "").split(os.pathsep)):
        if location:
            sys.path.insert(0, location)
    implementation = Path(__file__).absolute().parents[2]
    analysis = payload["schema"] == ANALYSIS_SCHEMA
    if analysis and (
        not isinstance(payload.get("analysis_nonce"), str)
        or len(payload["analysis_nonce"]) != 32
        or any(char not in "0123456789abcdef" for char in payload["analysis_nonce"])
    ):
        raise ValueError("Analysis request omitted its actual controller-selected fresh nonce")
    actual_runtime: dict[str, object] | None = None
    data_after: dict[str, object] | None = None
    analysis_reads: dict[str, object] | None = None
    supervisory_interrupted = False

    def verify(*, before_attempt: bool = True) -> None:
        nonlocal actual_runtime
        if analysis:
            runtime = payload.get("runtime_binding")
            if not isinstance(runtime, dict) or canonical_digest(runtime) != payload.get("runtime_digest"):
                raise ValueError("Analysis runtime admission is malformed")
            observed = admit_current_analysis_runtime(project, runtime)
            if actual_runtime is not None and observed != actual_runtime:
                raise ValueError("Actual analysis runtime changed during execution")
            actual_runtime = observed
            if (
                source_content_fingerprint(repo, project, definition_path=definition)
                != payload["source_content_digest"]
            ):
                raise ValueError("Consumed analysis source differs from its admitted content")
        elif source_fingerprint(repo, project, definition_path=definition) != payload["source_digest"]:
            raise ValueError("Consumed source differs from the resolved execution plan")
        admission = payload.get("stage_admission")
        if admission is not None:
            if any(
                payload[key] != os.environ.get(variable, "")
                for key, variable in (
                    ("run_id", "PIPELINE_RUN_ID"),
                    ("stage_key", "PIPELINE_STAGE_KEY"),
                    ("plan_digest", "PIPELINE_PLAN_DIGEST"),
                )
            ):
                raise ValueError("Actual attempt identity differs from its supervising admission")
            validate_stage_admission(
                admission,
                repo=repo,
                project=project,
                run_id=payload["run_id"],
                plan_digest=payload["plan_digest"],
                stage_key=payload["stage_key"],
                before_attempt=before_attempt,
            )
        # Check the same admitted roots as the launcher, including every
        # captured __main__/script-helper execution. Never omit a root because
        # a consumed module or its directory disappeared afterward.
        for root in (implementation, repo / "scripts", project / "src", project / "scripts"):
            verify_fresh_module_bytecode(root, prefix)

    original: int | None = None
    diagnostic, custody = "", "verified"
    try:
        verify()
        if analysis:
            require_analysis_data(
                payload.get("data_before"),
                project,
                run_id=payload["run_id"],
                stage_key=payload["stage_key"],
                deadline=payload["original_deadline_monotonic"],
            )
        sys.argv = list(payload["argv"])
        script = Path(sys.argv[0])
        raw = read_bytes_confined(project if analysis else repo, script, max_bytes=8 * 1024 * 1024)
        if hashlib.sha256(raw).hexdigest() != source_file_digest(script):
            raise ValueError("Stage source changed before frozen-byte compilation")
        verify()
        compiled = compile(raw, str(script), "exec", dont_inherit=True, optimize=sys.flags.optimize)
        module = ModuleType("__main__")
        module.__dict__.update(__file__=str(script), __package__=None, __spec__=None, __loader__=None, __cached__=None)
        previous_main, previous_path = sys.modules["__main__"], list(sys.path)
        sys.modules["__main__"] = module
        sys.path.insert(0, str(script.parent))
        try:
            with ExitStack() as reads_stack:
                reads = (
                    reads_stack.enter_context(
                        observe_stage_analysis_reads(
                            repo,
                            project,
                            run_id=payload["run_id"],
                            stage_key=payload["stage_key"],
                            nonce=payload["analysis_nonce"],
                            request_digest=expected_digest,
                            incoming=payload["data_before"],
                            deadline=payload["original_deadline_monotonic"],
                        )
                    )
                    if analysis
                    else None
                )
                if reads is not None:
                    reads_stack.enter_context(observe_stage_analysis_writes(reads))
                try:
                    exec(compiled, module.__dict__)  # nosec B102 - actual frozen Source stage, not a callback
                    original = 0
                except SystemExit as exc:
                    if exc.code is None:
                        original = 0
                    elif isinstance(exc.code, int):
                        original = int(exc.code) % 256
                    else:
                        print(exc.code, file=sys.stderr)
                        original = 1
                except KeyboardInterrupt:
                    original = 130
                except Exception:
                    traceback.print_exc()
                    original = 1
                finally:
                    if analysis and original is not None:
                        # This is an early original observation only. It cannot
                        # authorize success, skip or custody after incomplete
                        # verification. The controller uses it solely to retain
                        # known originals under interruption/timeout/refusal.
                        checkpoint = {
                            "schema": "template-analysis-original-checkpoint/1",
                            "request_digest": expected_digest,
                            "run_id": payload["run_id"],
                            "stage_key": payload["stage_key"],
                            "analysis_nonce": payload["analysis_nonce"],
                            "pid": os.getpid(),
                            "original_exit_code": original,
                            "completion_authorized": False,
                        }
                        atomic_write_text_confined(
                            scratch,
                            scratch / "original.json",
                            json.dumps(checkpoint, sort_keys=True) + "\n",
                            mode=0o600,
                        )
                    if reads is not None:
                        analysis_reads = reads.data()
        finally:
            sys.modules["__main__"] = previous_main
            sys.path[:] = previous_path
        verify(before_attempt=False)
        if analysis:
            data_after = capture_analysis_data(
                project,
                run_id=payload["run_id"],
                stage_key=payload["stage_key"],
                deadline=payload["original_deadline_monotonic"],
            )
    except (OSError, ValueError) as exc:
        custody, diagnostic = "blocked", str(exc)
    except KeyboardInterrupt:
        custody, diagnostic = "blocked", "Python stage supervisory verification/capture interrupted"
        supervisory_interrupted = True
    receipt = {
        "schema": payload["schema"],
        "request_digest": expected_digest,
        "run_id": payload["run_id"],
        "stage_key": payload["stage_key"],
        "custody": custody,
        "original_exit_code": original,
        "diagnostic": diagnostic,
    }
    if analysis:
        receipt.update(
            source_content_digest=payload["source_content_digest"],
            runtime_digest=payload["runtime_digest"],
            actual_runtime=actual_runtime,
            plan_digest=payload["plan_digest"],
            data_before_digest=payload["data_before"]["content_digest"],
            data_after=data_after,
            analysis_nonce=payload["analysis_nonce"],
            analysis_reads=analysis_reads,
            supervisory_interrupted=supervisory_interrupted,
        )
    try:
        atomic_write_text_confined(
            scratch, scratch / "result.json", json.dumps(receipt, sort_keys=True) + "\n", mode=0o600
        )
    except KeyboardInterrupt:
        # The earlier checkpoint retains an already observed script original
        # if repeated interruption prevents any final receipt from closing.
        custody, diagnostic, supervisory_interrupted = "blocked", "Python stage result promotion interrupted", True
        receipt.update(custody=custody, diagnostic=diagnostic)
        if analysis:
            receipt["supervisory_interrupted"] = True
        atomic_write_text_confined(
            scratch, scratch / "result.json", json.dumps(receipt, sort_keys=True) + "\n", mode=0o600
        )
    if supervisory_interrupted:
        return 130
    if custody == "blocked":
        print(f"Python stage blocked: {diagnostic}", file=sys.stderr)
        return 75
    assert original is not None
    return original


if __name__ == "__main__":
    raise SystemExit(main())
