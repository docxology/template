"""Fresh-bytecode worker consuming the parent's exact immutable execution plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.multi_project_runtime import WORKER_SCHEMA
from infrastructure.core.pipeline.plan import ExecutionPlan
from infrastructure.core.pipeline.types import PipelineConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        content = read_bytes_confined(args.request.parent, args.request)
        if hashlib.sha256(content).hexdigest() != args.request_sha256:
            raise ValueError("Worker request differs from the parent's exact frozen bytes")
        request = json.loads(content)
        if not isinstance(request, dict) or set(request) != {
            "schema_version",
            "nonce",
            "config",
            "plan",
            "plan_digest",
            "deadline_monotonic",
        }:
            raise ValueError("Worker request requires exact transport fields")
        if request["schema_version"] != WORKER_SCHEMA or not isinstance(request["nonce"], str) or not request["nonce"]:
            raise ValueError("Worker invocation identity is invalid")
        deadline = request["deadline_monotonic"]
        if type(deadline) not in {int, float} or not math.isfinite(deadline):
            raise ValueError("Worker supervising deadline must be finite")
        from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
        import infrastructure

        if sys.pycache_prefix is None or infrastructure.__file__ is None:
            raise ValueError("Worker requires a private fresh bytecode prefix")
        prefix = Path(sys.pycache_prefix)
        implementation = Path(infrastructure.__file__).absolute().parent
        verify_fresh_module_bytecode(implementation, prefix)
        if not isinstance(request["config"], dict) or set(request["config"]) != {
            "project_name",
            "repo_root",
            "projects_dir",
            "clean",
            "skip_infra",
            "resume",
            "shared_infrastructure",
            "mode",
            "run_timeout_seconds",
            "pipeline_path",
        }:
            raise ValueError("Worker configuration requires the exact current storage role fields")
        config = dict(request["config"])
        config["repo_root"] = Path(config["repo_root"])
        config["pipeline_path"] = Path(config["pipeline_path"]) if config["pipeline_path"] is not None else None
        resolved = PipelineConfig(**config)
        plan = ExecutionPlan.from_dict(request["plan"], expected_digest=request["plan_digest"])
        from infrastructure.core.pipeline.runtime_namespace import validate_shared_runtime

        validate_shared_runtime(resolved, plan)
        executor = PipelineExecutor(resolved)
        results = executor.execute_plan(plan, deadline_monotonic=deadline)
        verify_fresh_module_bytecode(implementation, prefix)
        run = executor.run_result(results)
        payload = {
            "schema_version": WORKER_SCHEMA,
            "nonce": request["nonce"],
            "project": plan.project,
            "shared_infrastructure": resolved.shared_infrastructure,
            "plan_digest": plan.digest,
            "source_identity": plan.source_identity,
            "environment_identity": plan.environment_identity,
            "expected_stage_keys": list(plan.expected_stage_keys),
            "stage_results": [asdict(row) for row in results],
            "exit_code": run.exit_code,
        }
        atomic_write_text_confined(
            args.request.parent, args.receipt, json.dumps(payload, sort_keys=True, allow_nan=False) + "\n", mode=0o600
        )
        return run.exit_code
    except (OSError, ValueError, TypeError, KeyError):
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
