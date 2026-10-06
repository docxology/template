"""Fresh-bytecode worker for source-bound pipeline report generation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    atomic_write_text_confined,
    read_bytes_confined,
    unlink_confined,
)
from infrastructure.core.pipeline.execution_records import EXECUTION_RECORD_SCHEMA
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint_components
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports
from infrastructure.core.pipeline.report_finalization import REPORT_FILES, REPORT_RECEIPT_SCHEMA
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult
from infrastructure.core.pipeline.plan import ExecutionPlan
from infrastructure.core.pipeline.runtime_namespace import validate_shared_runtime
from infrastructure.core.implementation_custody import verify_fresh_module_bytecode


def _results(rows: Any) -> list[PipelineStageResult]:
    if not isinstance(rows, list) or not rows:
        raise ValueError("Reporting requires nonempty execution records")
    result = []
    for raw in rows:
        if not isinstance(raw, dict) or not isinstance(raw.get("outcome"), dict):
            raise ValueError("Reporting requires typed stage outcomes")
        row = dict(raw)
        outcome = dict(row["outcome"])
        outcome["status"] = StageStatus(outcome["status"])
        outcome["attempt_exit_codes"] = tuple(outcome["attempt_exit_codes"])
        row["outcome"] = StageOutcome(**outcome)
        row["lessons"] = tuple(row["lessons"])
        result.append(PipelineStageResult(**row))
    return result


def _archive_previous(output: Path, target: Path) -> None:
    try:
        content = read_bytes_confined(output, target)
    except FileNotFoundError:
        return
    digest = hashlib.sha256(content).hexdigest()
    archive = output / ".pipeline" / "report_history" / digest / target.name
    atomic_write_bytes_confined(output, archive, content, mode=0o600)
    unlink_confined(output, target)


def _write_identity_diagnostic(
    output: Path,
    run_id: str,
    plan_digest: str,
    before: dict[str, object],
    after: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Keep hash-only observations in control state; never expose raw paths or metadata."""
    changed = tuple(key for key in ("source", "python", "tools") if after is not None and before[key] != after[key])
    payload = {
        "schema_version": "template-report-identity-diagnostic/1",
        "run_id": run_id,
        "plan_digest": plan_digest,
        "before": {key: canonical_digest(value) for key, value in before.items()},
        "after": None if after is None else {key: canonical_digest(value) for key, value in after.items()},
        "changed_components": changed,
    }
    atomic_write_text_confined(
        output,
        output / ".pipeline/report_identity_diagnostic.json",
        json.dumps(payload, sort_keys=True) + "\n",
        mode=0o600,
    )
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--projects-dir", default="projects")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--plan-digest", required=True)
    parser.add_argument("--record-digest", required=True)
    parser.add_argument("--pycache-prefix", type=Path, required=True)
    parser.add_argument("--shared-infrastructure", action="store_true")
    args = parser.parse_args()
    try:
        implementation = Path(__file__).absolute().parents[2]
        verify_fresh_module_bytecode(implementation, args.pycache_prefix)
        config = PipelineConfig(
            args.project,
            args.repo_root,
            projects_dir=args.projects_dir,
            clean=False,
            shared_infrastructure=args.shared_infrastructure,
            pipeline_path=args.repo_root / "infrastructure/core/pipeline/pipeline.yaml",
        )
        project = config.project_dir
        output = config.runtime_output_dir
        record_path = output / ".pipeline" / "execution.json"
        record_bytes = read_bytes_confined(output, record_path)
        if hashlib.sha256(record_bytes).hexdigest() != args.record_digest:
            raise ValueError("Reporting record bytes differ from the controller")
        record = json.loads(record_bytes)
        if (
            not isinstance(record, dict)
            or record.get("schema_version") != EXECUTION_RECORD_SCHEMA
            or record.get("shared_infrastructure", False) is not args.shared_infrastructure
            or record.get("run_id") != args.run_id
            or record.get("plan_digest") != args.plan_digest
            or not isinstance(record.get("plan"), dict)
            or canonical_digest(record["plan"]) != args.plan_digest
        ):
            raise ValueError("Reporting record identity differs from the controller")
        validate_shared_runtime(config, ExecutionPlan.from_dict(record["plan"], expected_digest=args.plan_digest))
        plan = record["plan"]
        if plan["project"] != args.project:
            raise ValueError("Reporting project differs from the resolved plan")
        results = _results(record["stage_results"])
        run = RunResult.from_results(results, tuple(record["expected_stage_keys"]))
        if run.complete != record["complete"] or run.exit_code != record["exit_code"]:
            raise ValueError("Reporting outcome differs from the recorded execution")
        definition = args.repo_root / plan["provenance"]
        before_identity = source_fingerprint_components(args.repo_root, project, definition_path=definition)
        _write_identity_diagnostic(output, args.run_id, args.plan_digest, before_identity)
        if canonical_digest(before_identity) != plan["source_identity"]:
            raise ValueError("Implementation changed before report execution")
        receipt = output / ".pipeline" / "report_finalization.json"
        _archive_previous(output, receipt)
        for name in REPORT_FILES:
            _archive_previous(output, output / "reports" / name)
        write_pipeline_post_run_reports(
            results=results,
            repo_root=args.repo_root,
            project_name=args.project,
            skip_infra=record["selection"]["skip_infra"],
            runtime_output_dir=output,
            project_dir=project,
        )
        files = {
            name: hashlib.sha256(read_bytes_confined(output, output / "reports" / name)).hexdigest()
            for name in REPORT_FILES
        }
        after_identity = source_fingerprint_components(args.repo_root, project, definition_path=definition)
        changed = _write_identity_diagnostic(output, args.run_id, args.plan_digest, before_identity, after_identity)
        if canonical_digest(after_identity) != plan["source_identity"]:
            raise ValueError("Implementation changed during report execution: " + ", ".join(changed))
        if read_bytes_confined(output, record_path) != record_bytes:
            raise ValueError("Execution record changed during report execution")
        verify_fresh_module_bytecode(implementation, args.pycache_prefix)
        payload = {
            "schema_version": REPORT_RECEIPT_SCHEMA,
            "status": "succeeded",
            "run_id": args.run_id,
            "shared_infrastructure": args.shared_infrastructure,
            "plan_digest": args.plan_digest,
            "execution_record_digest": args.record_digest,
            "source_identity": plan["source_identity"],
            "files": files,
        }
        atomic_write_text_confined(output, receipt, json.dumps(payload, sort_keys=True) + "\n", mode=0o600)
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Report finalization refused: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
