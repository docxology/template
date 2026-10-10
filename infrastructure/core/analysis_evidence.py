"""Private, source-bound aggregate evidence for supervised analysis producers."""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

from infrastructure.core.analysis_launch import analysis_receipt_path
from infrastructure.core.analysis_data_custody import require_analysis_data
from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined, unlink_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.runtime.python_binding import admitted_runtime_report, analysis_runtime_binding


@dataclass
class AnalysisRunEvidence:
    """Bind actual leaf evidence without exposing the effective environment."""

    repo: Path
    project: Path
    run_id: str
    plan_digest: str
    expected: tuple[str, ...]
    source_before: str
    deadline: float
    policy: dict[str, str]
    leaves: dict[str, str] = field(default_factory=dict)

    @property
    def path(self) -> Path:
        return analysis_receipt_path(self.project, self.run_id, "aggregate").with_name("run.json")

    def admit_leaf(self, outcome: StageOutcome) -> None:
        """Only exact current run/stage/outcome bytes become aggregate evidence."""
        target = analysis_receipt_path(self.project, self.run_id, outcome.stage_key)
        try:
            payload = read_bytes_confined(self.project, target, max_bytes=64 * 1024 * 1024)
        except FileNotFoundError:
            if outcome.complete or outcome.child_exit_code is not None:
                raise ValueError("Executed analysis producer is missing its leaf evidence") from None
            return  # A builder refusal has no admitted runtime or executed child.
        record = json.loads(payload)
        serialized = json.loads(json.dumps(outcome.to_dict()))
        if (
            not isinstance(record, dict)
            or record.get("schema") != "template-analysis-leaf/3"
            or record.get("run_id") != self.run_id
            or record.get("stage_key") != outcome.stage_key
            or record.get("plan_digest") != self.plan_digest
            or record.get("outcome") != serialized
            or record.get("complete") is not outcome.complete
            or record.get("cache_reuse_authorized") is not False
            or record.get("dependency_proof") != "metadata-record-declarations"
        ):
            raise ValueError("Analysis leaf evidence does not match the actual selected execution")
        before, after = record.get("controller_before"), record.get("controller_after")
        if outcome.complete and (
            not isinstance(before, dict)
            or before.get("source_digest") != self.source_before
            or before != after
            or not isinstance(record.get("worker"), dict)
        ):
            raise ValueError("Analysis completion lacks the unchanged admitted source and worker evidence")
        if outcome.complete:
            assert isinstance(before, dict)  # Established by the completion custody check above.
            worker = record["worker"]
            request, completion = worker.get("request"), worker.get("completion")
            if (
                not isinstance(request, dict)
                or not isinstance(completion, dict)
                or request.get("schema") != "template-python-analysis/4"
                or request.get("cwd") != str(self.repo.absolute())
                or any(request.get(key) != record[key] for key in ("run_id", "stage_key", "plan_digest"))
                or request.get("source_digest") != self.source_before
                or request.get("source_content_digest") != before.get("source_content_digest")
                or request.get("runtime_digest") != before.get("runtime_digest")
                or request.get("runtime_binding") != before.get("runtime_binding")
                or completion.get("schema") != request["schema"]
                or any(completion.get(key) != request.get(key) for key in ("source_content_digest", "runtime_digest"))
                or not isinstance(request.get("runtime_binding"), dict)
                or request.get("runtime_digest") != canonical_digest(request["runtime_binding"])
                or request["runtime_binding"] != analysis_runtime_binding(self.project)
                or not admitted_runtime_report(completion.get("actual_runtime"), request["runtime_binding"])
                or completion.get("request_digest") != canonical_digest(request)
                or any(completion.get(key) != record[key] for key in ("run_id", "stage_key", "plan_digest"))
                or completion.get("custody") != "verified"
                or completion.get("supervisory_interrupted") is not False
                or not isinstance(request.get("analysis_nonce"), str)
                or len(request["analysis_nonce"]) != 32
                or any(char not in "0123456789abcdef" for char in request["analysis_nonce"])
                or completion.get("analysis_nonce") != request["analysis_nonce"]
                or not isinstance(request.get("data_before"), dict)
                or completion.get("data_before_digest") != request["data_before"].get("content_digest")
                or not isinstance(worker.get("original_process"), dict)
                or not isinstance(completion.get("analysis_reads"), dict)
                or type(completion.get("original_exit_code")) is not int
                or completion["original_exit_code"] != 0
            ):
                raise ValueError("Analysis worker completion is not bound to its admitted request")
            process = worker["original_process"]
            reads = completion["analysis_reads"]
            if (
                type(process.get("pid")) is not int
                or process["pid"] <= 0
                or process.get("request_digest") != canonical_digest(request)
                or process.get("analysis_nonce") != request["analysis_nonce"]
                or process.get("original_exit_code") != 0
                or process.get("observed_exit_code") != 0
                or process.get("timed_out") is not False
                or process.get("custody_refused") is not False
                or process.get("original_deadline_monotonic") != request.get("original_deadline_monotonic")
                or type(process.get("original_deadline_monotonic")) not in (int, float)
                or not math.isfinite(process["original_deadline_monotonic"])
                or type(process.get("observed_completion_monotonic")) not in (int, float)
                or not math.isfinite(process["observed_completion_monotonic"])
                or not process["observed_completion_monotonic"] < process["original_deadline_monotonic"]
                or reads.get("schema") != "template-analysis-returned-read-bytes-v2"
                or reads.get("owner_pid") != process.get("pid")
                or reads.get("analysis_nonce") != request["analysis_nonce"]
                or reads.get("request_digest") != canonical_digest(request)
                or reads.get("run_id") != self.run_id
                or reads.get("stage_key") != outcome.stage_key
                or reads.get("content_digest")
                != canonical_digest({key: value for key, value in reads.items() if key != "content_digest"})
            ):
                raise ValueError("Analysis completion lacks the actual controller-observed PID/OS result and clock")
            require_analysis_data(
                completion.get("data_after"),
                self.project,
                run_id=self.run_id,
                stage_key=outcome.stage_key,
                deadline=self.deadline,
            )
        self.leaves[outcome.stage_key] = hashlib.sha256(payload).hexdigest()

    def finish(self, outcomes: list[StageOutcome]) -> RunResult:
        """A changed source, altered leaf, or refused report prevents completion."""
        final = list(outcomes)
        source_after: str | None = None
        try:
            source_after = source_fingerprint(self.repo, self.project)
            if source_after != self.source_before:
                raise ValueError("Analysis source changed across the selected producer sequence")
            for key, digest in self.leaves.items():
                payload = read_bytes_confined(
                    self.project,
                    analysis_receipt_path(self.project, self.run_id, key),
                    max_bytes=64 * 1024 * 1024,
                )
                if hashlib.sha256(payload).hexdigest() != digest:
                    raise ValueError("Analysis leaf evidence changed after admission")
        except KeyboardInterrupt:
            final.append(StageOutcome("analysis:evidence", StageStatus.INTERRUPTED, None, "Evidence audit interrupted"))
        except (OSError, ValueError) as exc:
            final.append(StageOutcome("analysis:evidence", StageStatus.BLOCKED, None, str(exc)))
        if time.monotonic() >= self.deadline:
            final.append(
                StageOutcome("analysis:deadline", StageStatus.TIMED_OUT, None, "Analysis run deadline exhausted")
            )
        result = RunResult(self.expected, tuple(final))
        record = {
            "schema": "template-analysis-run/3",
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "policy": self.policy,
            "expected_stage_keys": self.expected,
            "outcomes": [outcome.to_dict() for outcome in final],
            "leaf_sha256": self.leaves,
            "source_before": self.source_before,
            "source_after": source_after,
            "complete": result.complete,
            "exit_code": result.exit_code,
            "cache_reuse_authorized": False,
        }
        attempted = False
        try:
            attempted = True
            atomic_write_text_confined(self.project, self.path, json.dumps(record, sort_keys=True) + "\n", mode=0o600)
            if result.complete and source_fingerprint(self.repo, self.project) != self.source_before:
                raise ValueError("Analysis source changed during aggregate evidence promotion")
            if result.complete:
                for key, digest in self.leaves.items():
                    payload = read_bytes_confined(
                        self.project,
                        analysis_receipt_path(self.project, self.run_id, key),
                        max_bytes=64 * 1024 * 1024,
                    )
                    if hashlib.sha256(payload).hexdigest() != digest:
                        raise ValueError("Analysis leaf changed during aggregate evidence promotion")
            if time.monotonic() >= self.deadline and result.exit_code not in {124, 130}:
                raise TimeoutError("Analysis evidence deadline exhausted")
        except KeyboardInterrupt:
            final.append(
                StageOutcome("analysis:report", StageStatus.INTERRUPTED, None, "Evidence promotion interrupted")
            )
        except TimeoutError as exc:
            final.append(StageOutcome("analysis:report", StageStatus.TIMED_OUT, None, str(exc)))
        except (OSError, ValueError) as exc:
            final.append(
                StageOutcome("analysis:report", StageStatus.BLOCKED, None, f"Aggregate evidence refused: {exc}")
            )
        if tuple(final) != result.outcomes and attempted:
            # Refuse a possibly promoted success receipt even when final fsync
            # failed. Preserve original leaf outcomes and supervisory precedence.
            try:
                unlink_confined(self.project, self.path)
            except KeyboardInterrupt:
                final.append(
                    StageOutcome("analysis:report-cleanup", StageStatus.INTERRUPTED, None, "Removal interrupted")
                )
            except (OSError, ValueError) as exc:
                final.append(StageOutcome("analysis:report-cleanup", StageStatus.BLOCKED, None, str(exc)))
        return RunResult(self.expected, tuple(final))


__all__ = ["AnalysisRunEvidence"]
