"""Supervised local-model adapter with exact provider request/response custody."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..analysis.state import Proposal, SharedState
from .live_custody import (
    environment_identity,
    implementation_custody,
    platform_sources as current_platform_sources,
    verify_custody,
)
from .live_domain import (
    CoordinationBlocked,
    CoordinationFailed,
    LiveSettings,
    parse_proposal,
    proposal_schema,
    public_context,
    public_prompt,
)

SOURCE_PATH = "projects/templates/template_autoscientists/src/template_autoscientists/agents/live_transport.py"


def write_json(path: Path, payload: Any) -> None:
    """Persist finite JSON with deterministic bytes for manifest binding."""
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    """Identify exact persisted bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LiveProposer:
    """Each actual call reads the engine's current state and retains its receipt."""

    def __init__(
        self,
        settings: LiveSettings,
        directory: Path,
        deadline: float,
        *,
        platform_sources: dict[str, str] | None = None,
        runtime_environment: dict[str, Any] | None = None,
        implementation: dict[str, Any] | None = None,
    ) -> None:
        self.settings, self.directory, self.deadline = settings, directory, deadline
        self.calls: list[dict[str, Any]] = []
        self.model_sha256: str | None = None
        self.platform_sources = platform_sources if platform_sources is not None else current_platform_sources()
        self.runtime_environment = runtime_environment if runtime_environment is not None else environment_identity()
        self.implementation = implementation if implementation is not None else implementation_custody()
        directory.mkdir()

    def propose(
        self, state: SharedState, axes: Sequence[int], proposer_id: str, avoid: frozenset[tuple[int, str]] = frozenset()
    ) -> Proposal:
        """Execute one identity-checked local generation under both deadlines."""
        from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

        verify_custody(self.platform_sources, self.runtime_environment, self.implementation)

        if len(self.calls) >= self.settings.experiments_per_arm:
            raise CoordinationFailed("generation ceiling exhausted")
        available = self.deadline - time.monotonic()
        timeout = min(self.settings.request_timeout_seconds, int(available))
        if timeout < 1:
            raise CoordinationBlocked("run deadline exhausted")
        call_dir = self.directory / f"experiment_{len(self.calls) + 1}"
        call_dir.mkdir()
        context = public_context(state, axes, proposer_id, avoid)
        request: dict[str, Any] = {
            "prompt": public_prompt(context),
            "model": self.settings.model,
            "endpoint": self.settings.endpoint,
            "format_schema": proposal_schema(axes),
            "budget": {
                "timeout_seconds": timeout,
                "num_predict": self.settings.num_predict,
                "seed": 0,
                "temperature": 0,
            },
            "platform_sources": self.platform_sources,
            "runtime_environment": self.runtime_environment,
            "implementation_custody": self.implementation,
        }
        request_path = call_dir / "invocation.json"
        write_json(request_path, request)
        call: dict[str, Any] = {
            "experiment": len(self.calls) + 1,
            "context": context,
            "request_sha256": digest(request_path),
            "status": "incomplete",
        }
        self.calls.append(call)
        worker = Path(__file__).resolve()
        # The trusted source adapter is loaded through the canonical package so its
        # relative domain imports remain valid under Python isolated mode.
        bootstrap = (
            "import runpy,sys;sys.path[:0]=[sys.argv.pop(1),sys.argv.pop(1)];"
            "runpy.run_module('template_autoscientists.agents.live_transport',run_name='__main__')"
        )
        source_root = worker.parents[2]
        platform_file = __import__("infrastructure").__file__
        if platform_file is None:
            raise CoordinationBlocked("platform source location is unavailable")
        platform_root = Path(platform_file).resolve().parent.parent
        with tempfile.TemporaryDirectory(prefix="template-autoscientists-worker-cache-") as cache:
            from infrastructure.core.implementation_custody import bytecode_audit_bootstrap

            prefix = Path(cache).resolve()
            audited_bootstrap = bytecode_audit_bootstrap(
                (
                    worker.parents[1],
                    source_root.parent / "scripts",
                    platform_root / "infrastructure",
                    platform_root / "scripts",
                ),
                prefix,
            )
            request["fresh_pycache_prefix"] = str(prefix)
            write_json(request_path, request)
            call["request_sha256"] = digest(request_path)
            result = run_with_policy(
                [
                    sys.executable,
                    "-I",
                    "-X",
                    f"pycache_prefix={prefix}",
                    "-c",
                    audited_bootstrap + bootstrap,
                    str(source_root),
                    str(platform_root),
                    "--request",
                    str(request_path),
                    "--directory",
                    str(call_dir),
                ],
                cwd=call_dir,
                env=None,
                policy=SubprocessPolicy(
                    policy_id="autoscientists-local-proposal",
                    source_path=SOURCE_PATH,
                    timeout_seconds=timeout,
                    capture_output=True,
                    credential_free=True,
                ),
            )
        execution = {
            "returncode": result.returncode,
            "timed_out": result.timed_out,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "deadline_seconds": timeout,
            "bytecode_binding": "fresh-owned-prefix",
            "cache_prefix_created_empty_before_imports": True,
        }
        write_json(call_dir / "execution.json", execution)
        call["execution"] = execution
        if result.timed_out or result.returncode == 75:
            call["status"] = "blocked"
            raise CoordinationBlocked("selected local model unavailable or generation deadline exceeded")
        if result.returncode:
            call["status"] = "failed"
            raise CoordinationFailed("local generation failed; execution.json retains diagnostics")
        verify_custody(self.platform_sources, self.runtime_environment, self.implementation)
        if digest(request_path) != call["request_sha256"]:
            raise CoordinationFailed("invocation changed during generation")
        expected_request = {
            "model": request["model"],
            "prompt": request["prompt"],
            "stream": False,
            "options": {key: request["budget"][key] for key in ("seed", "temperature", "num_predict")},
            "format": request["format_schema"],
        }
        provider_request_path = call_dir / "request.json"
        provider_request = provider_request_path.read_bytes()
        if json.loads(provider_request) != expected_request:
            raise CoordinationFailed("actual provider request differs from the bounded invocation")
        identity_path = call_dir / "model_identity.json"
        identity_bytes = identity_path.read_bytes()
        model_sha256 = json.loads(identity_bytes)["model_sha256"]
        if self.model_sha256 is not None and model_sha256 != self.model_sha256:
            raise CoordinationFailed("selected model digest changed between experiments")
        self.model_sha256 = model_sha256
        response_path = call_dir / "response.json"
        response_bytes = response_path.read_bytes()
        response = json.loads(response_bytes)
        tokens = response["eval_count"]
        if tokens > self.settings.num_predict:
            raise CoordinationFailed("provider exceeded the declared generation token ceiling")
        call.update(
            model_sha256=model_sha256,
            response_sha256=hashlib.sha256(response_bytes).hexdigest(),
            eval_count=tokens,
            artifacts={
                str(path.relative_to(self.directory.parent)): hashlib.sha256(raw).hexdigest()
                for path, raw in (
                    (provider_request_path, provider_request),
                    (identity_path, identity_bytes),
                    (response_path, response_bytes),
                )
            },
        )
        proposal = parse_proposal(response["response"], axes, proposer_id, avoid)
        call.update(
            status="passed",
            proposal={
                "axis": proposal.axis,
                "step": proposal.step,
                "rationale": proposal.rationale,
                "proposer": proposer_id,
            },
        )
        return proposal


def main(argv: list[str] | None = None) -> int:
    """Provider worker; missing service is blocked, malformed completion fails."""
    from infrastructure.llm.core.local_ollama import (
        LocalModelResponseError,
        LocalModelUnavailable,
        generate_local_review,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    request = json.loads(args.request.read_text())
    try:
        verify_custody(
            request["platform_sources"],
            request["runtime_environment"],
            request["implementation_custody"],
            fresh_prefix=Path(request["fresh_pycache_prefix"]),
        )
        identity, actual_request, response = generate_local_review(
            request["prompt"],
            model=request["model"],
            budget=request["budget"],
            endpoint=request["endpoint"],
            format_schema=request["format_schema"],
        )
        verify_custody(
            request["platform_sources"],
            request["runtime_environment"],
            request["implementation_custody"],
            fresh_prefix=Path(request["fresh_pycache_prefix"]),
        )
    except (LocalModelUnavailable, OSError, TimeoutError) as exc:
        print(f"local model unavailable: {type(exc).__name__}: {exc}")
        return 75
    except (LocalModelResponseError, ValueError) as exc:
        print(f"local generation rejected: {exc}")
        return 1
    (args.directory / "request.json").write_text(actual_request, encoding="utf-8")
    (args.directory / "response.json").write_text(response, encoding="utf-8")
    write_json(args.directory / "model_identity.json", {"model": request["model"], "model_sha256": identity})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
