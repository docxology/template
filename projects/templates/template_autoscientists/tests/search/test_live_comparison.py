"""Actual loopback transport and supervised workers; controlled oracle, not live acceptance."""

from __future__ import annotations

import json
import hashlib
import importlib.metadata
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from email.parser import BytesParser

from packaging.requirements import Requirement
import pytest

from infrastructure.core import implementation_custody as platform_custody
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.llm.core.local_ollama import generate_local_review
from template_autoscientists.agents.live_domain import LiveSettings
from template_autoscientists.agents.live_custody import (
    environment_identity,
    implementation_custody,
    platform_sources,
    verify_custody,
)
from template_autoscientists.search.live_comparison import live_exit_code, run_live_comparison

PROJECT = Path(__file__).resolve().parents[2]

# The actual producer has a <=600s whole-run and <=60s generation deadline.
# Source admission and final custody/cleanup retain a finite outer allowance.
pytestmark = pytest.mark.timeout(720)


def project_copy(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(PROJECT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(PROJECT / "pyproject.toml", root / "pyproject.toml")
    return root


@contextmanager
def provider_oracle(*, effect="positive", fault=None, source_to_change=None, artifact_to_change=None, traffic=None):
    """A real HTTP conformance oracle with explicitly synthetic provider identity."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, payload):
            raw = json.dumps(payload).encode()
            if traffic is not None:
                traffic.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "request": getattr(self, "request_bytes", None),
                        "response": raw,
                    }
                )
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            model_digest = "b" * 64 if fault == "digest-drift" and len(requests) >= 2 else "a" * 64
            self.send(
                {"models": [] if fault == "missing-model" else [{"name": "fixture:latest", "digest": model_digest}]}
            )

        def do_POST(self):
            self.request_bytes = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(self.request_bytes)
            requests.append(request)
            if fault == "stall":
                time.sleep(2)
            axes = request.get("format", {"properties": {"axis": {"enum": [0]}}})["properties"]["axis"]["enum"]
            step = 0.5 if effect == "null" or effect == "negative" and len(axes) < 4 else -0.5
            proposal = {"axis": axes[0], "step": step, "rationale": "controlled public experiment"}
            if fault == "invalid-axis":
                proposal["axis"] = 99
            if source_to_change is not None:
                source_to_change.write_text("changed = True\n")
            if artifact_to_change is not None and len(requests) == 6:
                artifact_to_change.write_text('{"tampered": true}\n')
            try:
                self.send(
                    {
                        "model": "other-model" if fault == "wrong-model" else request["model"],
                        "done": True,
                        "response": json.dumps(proposal),
                        "eval_count": 513 if fault == "token-overflow" else 32,
                    }
                )
            except BrokenPipeError:
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("effect", ["positive", "null", "negative"])
def test_real_multistep_workers_report_observed_effect_and_matched_ceilings(tmp_path, effect) -> None:
    root = project_copy(tmp_path)
    with provider_oracle(effect=effect) as (endpoint, requests):
        receipt_path = run_live_comparison(
            root,
            root / "output/.pipeline/local_coordination/test",
            LiveSettings("fixture:latest", endpoint, experiments_per_arm=3),
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "passed", receipt
    assert receipt["effect"] == effect
    assert receipt["source_unchanged"] is True
    assert receipt["model_sha256"] == "a" * 64
    assert len(requests) == 6
    assert receipt["general_superiority_claim"] is False
    assert receipt["offline_reference"]["actual_model_generations"] == 0
    assert receipt["budget_contract"]["arm_wall_clock_ceiling_seconds"] == 180
    for arm in receipt["arms"].values():
        assert arm["generation_calls_used"] == 3
        assert arm["generation_tokens_used"] == 96
        assert arm["objective_evaluations_used"] == 12
        assert [len(call["context"]["experiment_log"]) for call in arm["calls"]] == [0, 1, 2]
        assert all(call["outcome"]["proposal"] == call["proposal"] for call in arm["calls"])
    assert live_exit_code(receipt_path) == 0


@pytest.mark.parametrize(
    "fault,status",
    [
        ("missing-model", "blocked"),
        ("wrong-model", "failed"),
        ("invalid-axis", "failed"),
        ("token-overflow", "failed"),
        ("digest-drift", "failed"),
    ],
)
def test_provider_and_domain_failures_propagate_with_diagnostics(tmp_path, fault, status) -> None:
    root = project_copy(tmp_path)
    with provider_oracle(fault=fault) as (endpoint, _):
        receipt_path = run_live_comparison(
            root,
            root / "output/.pipeline/local_coordination/test",
            LiveSettings("fixture:latest", endpoint, experiments_per_arm=3),
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == status, receipt
    assert live_exit_code(receipt_path) == (75 if status == "blocked" else 1)
    assert receipt["artifact_sha256"]
    assert receipt["diagnostic"]
    assert "baseline" not in receipt["arms"]


def test_source_change_cannot_pass(tmp_path) -> None:
    root = project_copy(tmp_path)
    with provider_oracle(source_to_change=root / "src/extra.py") as (endpoint, _):
        receipt_path = run_live_comparison(
            root,
            root / "output/.pipeline/local_coordination/test",
            LiveSettings("fixture:latest", endpoint, experiments_per_arm=3),
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "failed"
    assert receipt["source_unchanged"] is False


def test_consumed_provider_bytes_cannot_be_replaced_before_acceptance(tmp_path) -> None:
    root = project_copy(tmp_path)
    run = root / "output/.pipeline/local_coordination/test"
    with provider_oracle(artifact_to_change=run / "coordinated/experiment_1/response.json") as (endpoint, _):
        receipt_path = run_live_comparison(root, run, LiveSettings("fixture:latest", endpoint, experiments_per_arm=3))
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "failed"
    assert "consumed provider artifact changed" in receipt["diagnostic"]


def test_short_worker_budget_is_supervised_and_blocked(tmp_path) -> None:
    root = project_copy(tmp_path)
    with provider_oracle(fault="stall") as (endpoint, _):
        started = time.monotonic()
        receipt_path = run_live_comparison(
            root,
            root / "output/.pipeline/local_coordination/test",
            LiveSettings("fixture:latest", endpoint, experiments_per_arm=3, request_timeout_seconds=1),
        )
        elapsed = time.monotonic() - started
    receipt = json.loads(receipt_path.read_text())
    # The 1s worker deadline includes cold worker startup and HTTP. Source
    # observation and final custody/cleanup have a separate finite outer bound.
    assert elapsed < 30
    assert receipt["status"] == "blocked"
    calls = receipt["arms"]["coordinated"]["calls"]
    assert receipt["source_unchanged"] is True
    if calls:
        assert calls[0]["execution"]["timed_out"] is True
        assert calls[0]["execution"]["deadline_seconds"] == 1
    else:
        # Source admission can exhaust the actual matched three-second arm
        # before a worker is launched. That is an observed prelaunch refusal,
        # not evidence of an entered generation worker's request timeout.
        assert "run deadline exhausted" in receipt["diagnostic"]


@pytest.mark.timeout(180)
def test_actual_worker_one_second_http_budget_blocks_after_request_entry(tmp_path: Path) -> None:
    """An actual audited worker enters HTTP and retains its original blocked75."""
    from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
    from template_autoscientists.agents import live_transport
    from template_autoscientists.agents.live_domain import proposal_schema

    worker = Path(live_transport.__file__).resolve()
    source_root = worker.parents[2]
    platform_root = Path(platform_custody.__file__).resolve().parents[2]
    prefix = tmp_path / "fresh-worker-bytecode"
    prefix.mkdir(mode=0o700)
    directory = tmp_path / "actual-worker"
    directory.mkdir()
    custody = implementation_custody()
    sources = platform_sources()
    runtime = environment_identity()
    verify_custody(sources, runtime, custody)
    bootstrap = bytecode_audit_bootstrap(
        (
            worker.parents[1],
            source_root.parent / "scripts",
            platform_root / "infrastructure",
            platform_root / "scripts",
        ),
        prefix,
    )
    launch = (
        "import runpy,sys;sys.path[:0]=[sys.argv.pop(1),sys.argv.pop(1)];"
        "runpy.run_module('template_autoscientists.agents.live_transport',run_name='__main__')"
    )
    with provider_oracle(fault="stall") as (endpoint, requests):
        request = {
            "prompt": "Choose one bounded synthetic numeric proposal.",
            "model": "fixture:latest",
            "endpoint": endpoint,
            "format_schema": proposal_schema((0, 1, 2, 3)),
            "budget": {"timeout_seconds": 1, "num_predict": 512, "seed": 0, "temperature": 0},
            "platform_sources": sources,
            "runtime_environment": runtime,
            "implementation_custody": custody,
            "fresh_pycache_prefix": str(prefix),
        }
        invocation = directory / "invocation.json"
        live_transport.write_json(invocation, request)
        result = run_with_policy(
            [
                sys.executable,
                "-I",
                "-X",
                f"pycache_prefix={prefix}",
                "-c",
                bootstrap + launch,
                str(source_root),
                str(platform_root),
                "--request",
                str(invocation),
                "--directory",
                str(directory),
            ],
            cwd=directory,
            env=None,
            policy=SubprocessPolicy(
                policy_id="autoscientists-entered-worker-request-control",
                source_path="projects/templates/template_autoscientists/tests/search/test_live_comparison.py",
                timeout_seconds=90,
                credential_free=True,
                capture_output=True,
            ),
        )
    assert result.returncode == result.original_returncode == 75, result.stdout + result.stderr
    assert not result.timed_out and not result.custody_refused
    assert len(requests) == 1, "the real provider worker must enter generation HTTP"
    assert requests[0]["model"] == "fixture:latest"
    assert request["budget"]["timeout_seconds"] == 1
    assert "local model unavailable:" in result.stdout
    assert not (directory / "response.json").exists()
    verify_custody(sources, runtime, custody)


def test_run_deadline_is_independent_of_per_request_budget(tmp_path) -> None:
    root = project_copy(tmp_path)
    receipt_path = run_live_comparison(
        root, root / "output/.pipeline/local_coordination/test", LiveSettings("fixture:latest", run_timeout_seconds=1)
    )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "blocked"
    assert "run deadline exhausted" in receipt["diagnostic"]
    assert receipt["arms"]["coordinated"]["calls"] == []


def test_missing_service_is_blocked_without_deterministic_fallback(tmp_path) -> None:
    root = project_copy(tmp_path)
    with socket.socket() as guard:
        guard.bind(("127.0.0.1", 0))
        endpoint = f"http://127.0.0.1:{guard.getsockname()[1]}"
        receipt_path = run_live_comparison(
            root,
            root / "output/.pipeline/local_coordination/test",
            LiveSettings("fixture:latest", endpoint, experiments_per_arm=3),
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "blocked", receipt
    assert "offline_reference" not in receipt
    assert live_exit_code(receipt_path) == 75


def test_cli_live_missing_service_exits_75_and_core_remains_default(tmp_path) -> None:
    root = project_copy(tmp_path)
    script = PROJECT / "scripts/run_search_comparison.py"
    with socket.socket() as guard:
        guard.bind(("127.0.0.1", 0))
        endpoint = f"http://127.0.0.1:{guard.getsockname()[1]}"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--mode",
                "live",
                "--model",
                "fixture:latest",
                "--endpoint",
                endpoint,
                "--run-timeout-seconds",
                "120",
                "--project-root",
                str(root),
                "--output-dir",
                "output/.pipeline/local_coordination/cli",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            # Installed RECORD admission and final source custody are real
            # work outside the request budget; retain a finite outer allowance.
            timeout=180,
        )
    assert result.returncode == 75, result.stderr
    receipt = json.loads((root / "output/.pipeline/local_coordination/cli/coordination_receipt.json").read_text())
    assert receipt["status"] == "blocked" and receipt["source_unchanged"] is True
    execution = receipt["arms"]["coordinated"]["calls"][0]["execution"]
    assert execution["returncode"] == 75 and not execution["timed_out"]
    output = root / "output/core-reference"
    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(root), "--output-dir", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((output / "data/search_comparison.json").read_text())
    assert summary["budget"] == 60
    assert summary["clean_metric_advantage"] == 0.0
    assert (output / "figures/search_comparison.png").is_file()


def test_actual_fresh_standalone_controller_runs_controlled_model_workers(tmp_path) -> None:
    """Exercise the real main seed, fresh controller prefix, and supervised callbacks."""
    root = project_copy(tmp_path)
    relative_output = "output/.pipeline/local_coordination/fresh-controller"
    with provider_oracle(effect="positive") as (endpoint, requests):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT / "scripts/run_search_comparison.py"),
                "--mode",
                "live",
                "--model",
                "fixture:latest",
                "--endpoint",
                endpoint,
                "--experiments-per-arm",
                "3",
                "--project-root",
                str(root),
                "--output-dir",
                relative_output,
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=660,
        )
    receipt = json.loads((root / relative_output / "coordination_receipt.json").read_text())
    assert result.returncode == 0, result.stderr + result.stdout + json.dumps(receipt)
    assert receipt["status"] == "passed"
    assert receipt["effect"] == "positive"
    assert receipt["source_unchanged"] is True
    assert receipt["implementation_custody"]["bytecode_binding"] == "fresh-owned-prefix"
    assert any(name.startswith("active_controller/") for name in receipt["source_sha256"])
    assert len(requests) == 6
    assert all(arm["generation_calls_used"] == 3 for arm in receipt["arms"].values())


@pytest.mark.parametrize("fault", [None, "missing-project-root", "changed-hook-digest"])
def test_core_controller_preserves_and_authenticates_launcher_audit(tmp_path, fault) -> None:
    """Run the real script under a real pre-import hook, including refusal controls."""
    root = project_copy(tmp_path)
    output = root / "output/launcher-reference"
    script = PROJECT / "scripts/run_search_comparison.py"
    platform_root = Path(platform_custody.__file__).resolve().parents[2]
    prefix = tmp_path.resolve() / "launcher-cache"
    prefix.mkdir()
    roots = (platform_root / "infrastructure", platform_root / "scripts", PROJECT / "scripts")
    if fault != "missing-project-root":
        roots += (PROJECT / "src",)
    bootstrap = bytecode_audit_bootstrap(roots, prefix)
    if fault == "changed-hook-digest":
        bootstrap += (
            "from types import MappingProxyType;"
            "record=dict(sys._template_executed_bytecode_audit);"
            "record['hook_source_sha256']='0'*64;"
            "sys._template_executed_bytecode_audit=MappingProxyType(record);"
        )
    bootstrap += (
        "import runpy,sys;script=sys.argv.pop(1);"
        "prior_prefix=sys.pycache_prefix;prior_audit=sys._template_executed_bytecode_audit\n"
        "try:\n"
        " runpy.run_path(script,run_name='__main__')\n"
        "except SystemExit as error:\n"
        " if error.code not in (None,0): raise\n"
        "assert sys.pycache_prefix==prior_prefix\n"
        "assert sys._template_executed_bytecode_audit is prior_audit\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            bootstrap,
            str(script),
            "--project-root",
            str(root),
            "--output-dir",
            str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if fault is not None:
        assert result.returncode != 0, result.stdout + result.stderr
        expected = "outside the pre-import audit roots" if fault == "missing-project-root" else "active audit differs"
        assert expected in result.stderr
        assert not output.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        summary = json.loads((output / "data/search_comparison.json").read_text())
        assert summary["budget"] == 60
        assert summary["clean_metric_advantage"] == 0.0
        assert (output / "figures/search_comparison.png").is_file()


@pytest.mark.parametrize("location", ["output/data/run", "output/.pipeline/local_coordination", "../outside"])
def test_output_is_confined_to_fresh_ignored_runs(tmp_path, location) -> None:
    root = project_copy(tmp_path)
    with pytest.raises(ValueError, match="fresh run"):
        run_live_comparison(root, root / location, LiveSettings("fixture:latest"))


def test_reuse_and_symlink_output_rejected(tmp_path) -> None:
    root = project_copy(tmp_path)
    run = root / "output/.pipeline/local_coordination/run"
    run.mkdir(parents=True)
    with pytest.raises(ValueError, match="already exists"):
        run_live_comparison(root, run, LiveSettings("fixture:latest"))
    run.rmdir()
    run.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        run_live_comparison(root, run / "other", LiveSettings("fixture:latest"))


@pytest.mark.requires_ollama
def test_actual_installed_model_coordination_fails_closed_when_capability_missing(tmp_path) -> None:
    model = os.environ.get("TEMPLATE_AUTOSCIENTISTS_MODEL")
    assert model, "explicit TEMPLATE_AUTOSCIENTISTS_MODEL is required for live acceptance"
    root = project_copy(tmp_path)
    receipt_path = run_live_comparison(
        root,
        root / "output/.pipeline/local_coordination/live",
        LiveSettings(model, os.environ.get("TEMPLATE_AUTOSCIENTISTS_ENDPOINT", "http://127.0.0.1:11434")),
    )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "passed", receipt


def test_format_schema_is_added_only_when_requested() -> None:
    budget = {"timeout_seconds": 5, "num_predict": 128, "seed": 0, "temperature": 0}
    with provider_oracle() as (endpoint, requests):
        generate_local_review(
            "public",
            "fixture:latest",
            budget,
            endpoint=endpoint,
            format_schema={"type": "object", "properties": {"axis": {"enum": [0]}}},
        )
    assert requests[0]["format"]["type"] == "object"
    with provider_oracle() as (endpoint, requests):
        generate_local_review("public", "fixture:latest", budget, endpoint=endpoint)
    assert "format" not in requests[0]


@pytest.mark.parametrize("fault,exit_code", [(None, 0), ("missing-model", 75), ("wrong-model", 1)])
def test_provider_worker_persists_exact_bytes_and_classifies_failures(tmp_path, fault, exit_code) -> None:
    traffic = []
    with provider_oracle(fault=fault, traffic=traffic) as (endpoint, requests):
        request = {
            "prompt": "public numeric proposal",
            "model": "fixture:latest",
            "endpoint": endpoint,
            "format_schema": {"type": "object", "properties": {"axis": {"enum": [0]}}},
            "budget": {"timeout_seconds": 5, "num_predict": 128, "seed": 0, "temperature": 0},
            "platform_sources": platform_sources(),
            "runtime_environment": environment_identity(),
            "implementation_custody": implementation_custody(),
        }
        invocation = tmp_path / "invocation.json"
        prefix = tmp_path.resolve() / "cache"
        prefix.mkdir()
        request["fresh_pycache_prefix"] = str(prefix)
        invocation.write_text(json.dumps(request))
        platform_root = Path(platform_custody.__file__).resolve().parents[2]
        bootstrap = bytecode_audit_bootstrap(
            (
                PROJECT / "src/template_autoscientists",
                PROJECT / "scripts",
                platform_root / "infrastructure",
                platform_root / "scripts",
            ),
            prefix,
        ) + (
            "import sys,runpy;sys.path[:0]=[sys.argv.pop(1),sys.argv.pop(1)];"
            "runpy.run_module('template_autoscientists.agents.live_transport',run_name='__main__')"
        )
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-X",
                f"pycache_prefix={prefix}",
                "-c",
                bootstrap,
                str(PROJECT / "src"),
                str(platform_root),
                "--request",
                str(invocation),
                "--directory",
                str(tmp_path.resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == exit_code, result.stderr + result.stdout
        assert "pre-import executed-code audit" not in result.stdout + result.stderr
    if exit_code == 0:
        assert [(event["method"], event["path"]) for event in traffic] == [
            ("GET", "/api/tags"),
            ("POST", "/api/generate"),
            ("GET", "/api/tags"),
        ]
        assert len(requests) == 1
        assert (tmp_path / "request.json").read_bytes() == traffic[1]["request"]
        assert (tmp_path / "response.json").read_bytes() == traffic[1]["response"]
        assert json.loads((tmp_path / "request.json").read_text())["model"] == "fixture:latest"
        assert json.loads((tmp_path / "response.json").read_text())["eval_count"] == 32
        assert json.loads((tmp_path / "model_identity.json").read_text())["model_sha256"] == "a" * 64
    else:
        assert not (tmp_path / "response.json").exists()
        assert not (tmp_path / "request.json").exists()
        assert not (tmp_path / "model_identity.json").exists()
        if fault == "missing-model":
            assert [(event["method"], event["path"]) for event in traffic] == [("GET", "/api/tags")]
            assert not requests
            assert "LocalModelUnavailable: Configured local model is not uniquely installed" in result.stdout
        else:
            assert [(event["method"], event["path"]) for event in traffic] == [
                ("GET", "/api/tags"),
                ("POST", "/api/generate"),
            ]
            assert len(requests) == 1
            assert (
                "Local model generation has an incomplete response, wrong model, or invalid token count"
                in result.stdout
            )


def test_transitive_platform_and_worker_environment_are_required() -> None:
    sources, environment = platform_sources(), environment_identity()
    assert "infrastructure/core/subprocess_policy.py" in sources
    assert "infrastructure/core/execution_boundary.py" in sources
    custody = implementation_custody()
    if custody["binding_kind"] == "source-checkout":
        assert "uv.lock" in sources
    else:
        assert custody["binding_kind"] == "installed-distribution"
        selected = importlib.metadata.distribution("research-project-template")
        assert selected.version == "4.0.1" and selected.files is not None
        records = [path for path in selected.files if str(path).endswith(".dist-info/RECORD")]
        assert len(records) == 1
        record_path = Path(selected.locate_file(records[0]))
        metadata_path = Path(selected.locate_file(records[0].parent / "METADATA"))
        assert sources["distribution/RECORD"] == hashlib.sha256(record_path.read_bytes()).hexdigest()
        metadata_bytes = metadata_path.read_bytes()
        assert sources["distribution/METADATA"] == hashlib.sha256(metadata_bytes).hexdigest()
        metadata = BytesParser().parsebytes(metadata_bytes)
        assert metadata.get_all("Name") == ["research-project-template"]
        assert metadata.get_all("Version") == ["4.0.1"]
        assert metadata.get_all("Requires-Python") == [">=3.12"]
        requirements = metadata.get_all("Requires-Dist")
        assert requirements
        for declared in requirements:
            requirement = Requirement(declared)
            if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
                assert importlib.metadata.version(requirement.name) in requirement.specifier
        assert {
            "infrastructure/" + relative: digest
            for relative, digest in custody["distribution"]["public_python"].items()
        } == custody["files"]
        for field in ("distribution/RECORD", "distribution/METADATA"):
            with pytest.raises(ValueError, match="changed"):
                verify_custody(dict(sources, **{field: "0" * 64}), environment)
    changed = dict(sources, **{"infrastructure/core/subprocess_policy.py": "0" * 64})
    with pytest.raises(ValueError, match="changed"):
        verify_custody(changed, environment)
    with pytest.raises(ValueError, match="changed"):
        verify_custody(sources, dict(environment, implementation="different"))


@pytest.mark.parametrize(
    "schema",
    [
        {},
        [],
        True,
        {1: "x"},
        {"nested": {2: "x"}},
        {"minimum": float("nan")},
        {"enum": (1, 2)},
        {"description": "x" * 65537},
    ],
)
def test_invalid_format_schema_rejected_before_any_network(schema) -> None:
    with pytest.raises(ValueError, match="schema"):
        generate_local_review(
            "public",
            "fixture:latest",
            {"timeout_seconds": 5, "num_predict": 128, "seed": 0, "temperature": 0},
            endpoint="http://127.0.0.1:1",
            format_schema=schema,
        )
