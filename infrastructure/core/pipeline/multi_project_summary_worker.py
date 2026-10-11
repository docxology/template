"""Generate a typed aggregate summary only within its private scratch boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.implementation_custody import verify_implementation_custody
from infrastructure.core.pipeline.multi_project import MultiProjectResult
from infrastructure.core.pipeline.multi_project_runtime import results_from_payload
from infrastructure.core.pipeline.multi_project_support import SharedInfrastructureResult
from infrastructure.core.pipeline.multi_project_summary import SCHEMA
from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.project.project_info import ProjectInfo
from infrastructure.reporting.multi_project_report import format_multi_project_detailed_report
from infrastructure.reporting.multi_project_reporter import generate_multi_project_summary_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    root = args.request.parent
    raw = read_bytes_confined(root, args.request)
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError("Summary request changed from the supervisor's exact bytes")
    request = json.loads(raw)
    if (
        not isinstance(request, dict)
        or set(request) != {"schema_version", "nonce", "custody", "result", "projects"}
        or request["schema_version"] != SCHEMA
        or sys.pycache_prefix is None
    ):
        raise ValueError("Summary requires its exact bound input and fresh cache prefix")
    custody = request["custody"]
    prefix = Path(sys.pycache_prefix)
    verify_implementation_custody(custody, fresh_pycache_prefix=prefix)
    payload = dict(request["result"])
    payload["expected_projects"] = tuple(payload["expected_projects"])
    rows = {name: results_from_payload(value) for name, value in payload["project_results"].items()}
    payload["project_results"] = rows
    runs = {}
    for name, value in payload["run_results"].items():
        run = RunResult.from_results(rows[name], tuple(value["expected_stage_keys"]))
        # Preserve the exact parent's outcomes rather than accepting a second inferred claim.
        if json.loads(json.dumps([outcome.to_dict() for outcome in run.outcomes])) != value["outcomes"]:
            raise ValueError("Summary stage rows and typed parent outcomes differ")
        runs[name] = run
    payload["run_results"] = runs
    shared = payload.get("shared_infrastructure_result")
    if shared is not None:
        if not isinstance(shared, dict) or set(shared) != {"stage_results", "run_result"}:
            raise ValueError("Summary shared verification requires its exact typed evidence")
        shared_rows = results_from_payload(shared["stage_results"])
        shared_claim = shared["run_result"]
        if not isinstance(shared_claim, dict) or set(shared_claim) != {"expected_stage_keys", "outcomes"}:
            raise ValueError("Summary shared verification has an invalid selection/outcome claim")
        shared_run = RunResult.from_results(shared_rows, tuple(shared_claim["expected_stage_keys"]))
        if json.loads(json.dumps([outcome.to_dict() for outcome in shared_run.outcomes])) != shared_claim["outcomes"]:
            raise ValueError("Summary shared stage rows and typed parent outcomes differ")
        shared_result = SharedInfrastructureResult(tuple(shared_rows), shared_run)
        if (
            shared_result.validated_run() is None
            or shared_result.exit_code != payload["shared_infrastructure_exit_code"]
        ):
            raise ValueError("Summary shared verification identity/status/exit differs")
        payload["shared_infrastructure_result"] = shared_result
    result = MultiProjectResult(**payload)
    projects = [ProjectInfo(**{**project, "path": Path(project["path"])}) for project in request["projects"]]
    reports = root / "reports"
    reports.mkdir()
    files = generate_multi_project_summary_report(result, projects, reports)
    lines = format_multi_project_detailed_report(projects, result)
    last = reports / "last-run-summary.md"
    stamp = datetime.now(timezone.utc).isoformat()
    atomic_write_text_confined(
        root,
        last,
        "# Last Recorded Pipeline Run — Summary\n\n"
        "> Historical execution evidence; dedicated gates establish current health.\n"
        f"> Generated: {stamp}\n\n```\n" + "\n".join(lines) + "\n```\n",
    )
    files["last"] = last
    verify_implementation_custody(custody, fresh_pycache_prefix=prefix)
    receipt = {
        "schema_version": SCHEMA,
        "nonce": request["nonce"],
        "request_sha256": args.sha256,
        "artifacts": {
            path.name: hashlib.sha256(read_bytes_confined(root, path)).hexdigest() for path in files.values()
        },
    }
    atomic_write_text_confined(root, root / "receipt.json", json.dumps(receipt, sort_keys=True) + "\n", mode=0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
