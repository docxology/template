"""Numeric-domain controls, real loopback HTTP, and real Docker execution.

The controlled HTTP server tests API custody and faults. It is not an Ollama
model and its receipts do not constitute actual model acceptance.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from template_sia.loop.live_proposals import ProposalSettings, request_proposal, run_live_proposals
from template_sia.loop.proposal_domain import (
    LiveCapabilityBlocked,
    LiveProposalFailed,
    mutate_threshold,
    public_prompt,
    read_dataset,
    score_predictions,
    validated_threshold,
)
from template_sia.loop.proposal_sandbox import container_argv, require_docker_image, run_target
from template_sia.loop.proposal_transport import main as transport_main
from template_sia.loop.proposal_transport import ollama_generate

PROJECT = Path(__file__).resolve().parents[2]
REFERENCE = PROJECT / "tasks/mini_classify/reference/reference_target_agent.py"


@contextmanager
def controlled_provider(
    *,
    response: dict[str, object] | None = None,
    status: int = 200,
    digests: tuple[str, ...] = ("a" * 64,),
    on_request=None,
):
    requests: list[dict[str, object]] = []
    inventories = 0

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal inventories
            digest = digests[min(inventories, len(digests) - 1)]
            inventories += 1
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"models": [{"name": "controlled-http-fixture", "digest": digest}]}).encode())

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            if on_request is not None:
                on_request()
            payload = (
                response
                if response is not None
                else {
                    "model": "controlled-http-fixture",
                    "done": True,
                    "eval_count": 12,
                    "response": json.dumps({"threshold": 0.4, "rationale": "Evaluate a distinct public threshold."}),
                }
            )
            self.send_response(status)
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def image_id() -> str:
    selected_image = os.environ.get("TEMPLATE_SIA_TEST_IMAGE")
    if not shutil.which("docker"):
        if selected_image:
            pytest.fail("CI selected a required Docker image but Docker CLI is unavailable")
        pytest.skip("Docker execution requires the Docker CLI")
    result = subprocess.run(
        ["docker", "image", "inspect", selected_image or "python:3.14-slim", "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if result.returncode:
        if selected_image:
            pytest.fail("Explicitly selected Docker image is unavailable; no download or skip fallback")
        pytest.skip("Real Docker tests require an already installed Python image; never pull implicitly")
    return result.stdout.strip()


@pytest.mark.parametrize("bad", [True, "0.5", None, float("nan"), float("inf"), -1, 2])
def test_numeric_proposals_reject_nonfinite_or_nonnumeric_values(bad) -> None:
    with pytest.raises(ValueError, match="finite numeric"):
        validated_threshold(bad)


def test_mutation_changes_only_one_literal_and_cannot_supply_code() -> None:
    source = REFERENCE.read_text(encoding="utf-8")
    changed = mutate_threshold(source, 0.4)
    assert changed.replace("THRESHOLD = 0.4", "THRESHOLD = 0.5") == source
    with pytest.raises(ValueError):
        mutate_threshold(source, "__import__('os')")


def test_public_prompt_excludes_frozen_holdout() -> None:
    rows = read_dataset(PROJECT / "tasks/mini_classify/data/public/train.csv")
    prompt = public_prompt(rows, 0.5, 1.0)
    assert "public_cases" in prompt
    assert "holdout_0" not in prompt and "0.49" not in prompt


def test_missing_prediction_rows_do_not_inflate_score(tmp_path: Path) -> None:
    rows = read_dataset(PROJECT / "tasks/mini_classify/data/public/train.csv")
    path = tmp_path / "predictions.csv"
    path.write_text("id,label\n0,negative\n", encoding="utf-8")
    with pytest.raises(LiveProposalFailed, match="every case"):
        score_predictions(rows, path)


def test_remote_or_credentialed_model_endpoints_are_rejected() -> None:
    for endpoint in ("https://example.com", "http://user:password@127.0.0.1", "http://127.0.0.1/other"):
        with pytest.raises(ValueError, match="loopback"):
            ollama_generate(endpoint, {"model": "anything"})


def test_real_http_transport_retains_selected_model_evidence() -> None:
    with controlled_provider() as (endpoint, requests):
        response = ollama_generate(endpoint, {"model": "controlled-http-fixture", "prompt": "public cases only"})
    assert response["eval_count"] == 12
    assert requests[0]["prompt"] == "public cases only"


def test_unavailable_or_incomplete_model_never_falls_back() -> None:
    with controlled_provider(status=404) as (endpoint, _):
        with pytest.raises(ConnectionError):
            ollama_generate(endpoint, {"model": "controlled-http-fixture"})
    with controlled_provider(response={"model": "controlled-http-fixture", "done": False}) as (endpoint, _):
        with pytest.raises(ValueError):
            ollama_generate(endpoint, {"model": "controlled-http-fixture"})


def test_absent_docker_tool_is_blocked_without_host_fallback(tmp_path: Path) -> None:
    with pytest.raises(LiveCapabilityBlocked, match="CLI"):
        require_docker_image("sha256:" + "a" * 64, tmp_path, executable="template-sia-no-such-docker-tool")


def test_container_restrictions_bind_only_three_scoped_mounts(tmp_path: Path) -> None:
    argv = container_argv("docker", "sha256:" + "a" * 64, tmp_path, "test-container")
    assert argv.count("--mount") == 3
    assert argv[argv.index("--network") + 1] == "none"
    assert "--read-only" in argv and "--cap-drop" in argv
    assert "--pull=never" in argv and "65534:65534" in argv
    assert "/var/run/docker.sock" not in " ".join(argv)


def test_real_docker_classifier_is_complete_and_cleanup_is_verified(tmp_path: Path, image_id: str) -> None:
    docker = require_docker_image(image_id, tmp_path)
    rows = read_dataset(PROJECT / "tasks/mini_classify/data/public/train.csv")
    predictions = run_target(docker, image_id, REFERENCE.read_text(), rows, tmp_path / "result", 30)
    assert score_predictions(rows, predictions) == 1.0
    execution = json.loads((tmp_path / "result/execution.json").read_text())
    assert execution["cleanup_verified"] and execution["network"] == "none"
    assert execution["host_credentials_forwarded"] is False


def test_real_docker_and_controlled_http_loop_mutate_then_restore(
    tmp_path: Path,
    image_id: str,
    copy_project_sandbox,
) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    baseline = (project / "tasks/mini_classify/reference/reference_target_agent.py").read_bytes()
    with controlled_provider() as (endpoint, requests):
        receipt_path = run_live_proposals(
            project, project / "output/proposal-test", ProposalSettings("controlled-http-fixture", image_id, endpoint)
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "passed" and receipt["mutation_count"] == 2
    assert receipt["model_sha256"] == "a" * 64 and receipt["frozen_inputs_verified"]
    assert receipt["elapsed_sec"] < receipt["run_deadline_sec"] == 600
    assert receipt["rollback_verified"] and not receipt["production_source_applied"]
    assert receipt["heldout_accuracy"] == 1.0 and not receipt["holdout_used_for_selection"]
    assert all(record["selection"] == "reject_no_improvement" for record in receipt["generations"][1:])
    assert (receipt_path.parent / "sandbox_target.py").read_bytes() == baseline
    assert (project / "tasks/mini_classify/reference/reference_target_agent.py").read_bytes() == baseline
    assert all("holdout_0" not in request["prompt"] for request in requests)
    for generation in (2, 3):
        assert (receipt_path.parent / f"gen_{generation}/proposal.diff").read_text()
        approval = json.loads((receipt_path.parent / f"gen_{generation}/approval_receipt.json").read_text())
        assert approval["approval_status"] == "pending" and not approval["production_apply_permitted"]


def test_cli_missing_model_returns_blocked_75_with_retained_receipt(tmp_path: Path, copy_project_sandbox) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    proc = subprocess.run(
        [sys.executable, str(PROJECT / "scripts/run_sia_loop.py"), "--project-root", str(project), "--live-proposals"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 75
    receipt = json.loads((project / "output/live_proposals_run_1/live_proposal_receipt.json").read_text())
    assert receipt["status"] == "blocked"


def test_real_docker_timeout_retains_diagnostics_and_removes_container(tmp_path: Path, image_id: str) -> None:
    docker = require_docker_image(image_id, tmp_path)
    rows = read_dataset(PROJECT / "tasks/mini_classify/data/public/train.csv")
    with pytest.raises(LiveProposalFailed, match="Docker target failed"):
        run_target(docker, image_id, "while True: pass\n", rows, tmp_path / "timeout", 1)
    receipt = json.loads((tmp_path / "timeout/execution.json").read_text())
    assert receipt["timed_out"] and receipt["cleanup_verified"]


def test_actual_provider_failure_retains_blocked_receipt_and_restores_source(
    tmp_path: Path, image_id: str, copy_project_sandbox
) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    original = (project / "tasks/mini_classify/reference/reference_target_agent.py").read_bytes()
    output = project / "output/blocked-model"
    with controlled_provider(status=404) as (endpoint, _):
        with pytest.raises(LiveCapabilityBlocked, match="unavailable"):
            run_live_proposals(project, output, ProposalSettings("controlled-http-fixture", image_id, endpoint))
    receipt = json.loads((output / "live_proposal_receipt.json").read_text())
    assert receipt["status"] == "blocked" and receipt["rollback_verified"]
    assert (output / "sandbox_target.py").read_bytes() == original
    assert json.loads((output / "gen_2/model_execution.json").read_text())["returncode"] == 75
    assert not (output / "gen_2/target_agent.py").exists()


@pytest.mark.parametrize(
    "proposal",
    [
        "not-json",
        json.dumps({"threshold": 0.4, "rationale": "valid", "code": "import os"}),
        json.dumps({"threshold": "0.4", "rationale": "valid"}),
        json.dumps({"threshold": 0.4, "rationale": ""}),
    ],
)
def test_actual_http_proposal_rejects_malformed_or_executable_payloads(tmp_path: Path, proposal: str) -> None:
    payload = {"model": "controlled-http-fixture", "done": True, "eval_count": 1, "response": proposal}
    with controlled_provider(response=payload) as (endpoint, _):
        with pytest.raises(LiveProposalFailed):
            request_proposal(ProposalSettings("controlled-http-fixture", "", endpoint), "public cases", tmp_path)
    assert (tmp_path / "model_response.json").is_file()
    assert json.loads((tmp_path / "model_execution.json").read_text())["returncode"] == 0


def test_distinct_proposal_is_required_and_perfect_baseline_is_not_claimed_improved(
    tmp_path: Path, image_id: str, copy_project_sandbox
) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    output = project / "output/no-mutation"
    payload = {
        "model": "controlled-http-fixture",
        "done": True,
        "eval_count": 1,
        "response": json.dumps({"threshold": 0.5, "rationale": "Keep existing threshold."}),
    }
    with controlled_provider(response=payload) as (endpoint, _):
        with pytest.raises(LiveProposalFailed, match="no distinct numeric mutation"):
            run_live_proposals(project, output, ProposalSettings("controlled-http-fixture", image_id, endpoint, 2))
    receipt = json.loads((output / "live_proposal_receipt.json").read_text())
    assert receipt["status"] == "failed" and receipt["rollback_verified"]
    assert receipt["generations"][1]["selection"] == "reject_no_improvement"
    assert not (output / "heldout").exists()


def test_strict_public_improvement_selects_candidate_without_using_holdout(
    tmp_path: Path, image_id: str, copy_project_sandbox
) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    reference = project / "tasks/mini_classify/reference/reference_target_agent.py"
    reference.write_text(mutate_threshold(reference.read_text(), 0.9))
    original = reference.read_bytes()
    with controlled_provider() as (endpoint, requests):
        receipt_path = run_live_proposals(
            project, project / "output/selection", ProposalSettings("controlled-http-fixture", image_id, endpoint, 2)
        )
    receipt = json.loads(receipt_path.read_text())
    assert receipt["generations"][1]["selection"] == "keep_in_sandbox"
    assert receipt["selected_threshold"] == 0.4 and receipt["public_accuracy"] == 1.0
    assert reference.read_bytes() == original and receipt["rollback_verified"]
    assert all("holdout_" not in request["prompt"] for request in requests)


def test_proposal_outputs_and_limits_cannot_escape_bounded_lane(tmp_path: Path, copy_project_sandbox) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    with pytest.raises(ValueError, match="confined"):
        run_live_proposals(project, tmp_path / "outside", ProposalSettings("model", ""))
    for generations in (1, 4, True, 2.5):
        with pytest.raises(ValueError, match="2–3"):
            ProposalSettings("model", "", max_generations=generations)
    for timeout in (0, 61, True, 1.5):
        with pytest.raises(ValueError, match="1,60"):
            ProposalSettings("model", "", target_timeout_sec=timeout)
    for timeout in (0, 601, True, 1.5):
        with pytest.raises(ValueError, match="run timeout"):
            ProposalSettings("model", "", run_timeout_sec=timeout)


def test_transport_entrypoint_preserves_actual_response_and_explicit_fault_exit(tmp_path: Path) -> None:
    request, response = tmp_path / "request.json", tmp_path / "response.json"
    request.write_text(json.dumps({"model": "controlled-http-fixture"}))
    with controlled_provider() as (endpoint, _):
        assert transport_main(["--endpoint", endpoint, "--request", str(request), "--response", str(response)]) == 0
    assert json.loads(response.read_text())["eval_count"] == 12
    response.unlink()
    with controlled_provider(status=404) as (endpoint, _):
        assert transport_main(["--endpoint", endpoint, "--request", str(request), "--response", str(response)]) == 75
    assert not response.exists()
    with controlled_provider(response={"done": False}) as (endpoint, _):
        assert transport_main(["--endpoint", endpoint, "--request", str(request), "--response", str(response)]) == 1
    assert not response.exists()


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"error": "model unavailable"}, ConnectionError),
        ({"model": "other-model", "done": True, "eval_count": 1}, ValueError),
        ({"model": "controlled-http-fixture", "done": True, "eval_count": 0}, ValueError),
        ({"model": "controlled-http-fixture", "done": True, "eval_count": 1, "response": "x" * 65536}, ValueError),
    ],
)
def test_real_http_receipts_reject_wrong_model_empty_generation_or_oversize(payload, expected) -> None:
    with controlled_provider(response=payload) as (endpoint, _):
        with pytest.raises(expected):
            ollama_generate(endpoint, {"model": "controlled-http-fixture"})


def test_prediction_ids_and_labels_must_match_exact_domain(tmp_path: Path) -> None:
    rows = ({"id": "a", "feature_0": "0.1", "label": "negative"},)
    path = tmp_path / "predictions.csv"
    path.write_text("id,label\nother,negative\n")
    with pytest.raises(LiveProposalFailed, match="ids differ"):
        score_predictions(rows, path)
    path.write_text("id,label\na,unknown\n")
    with pytest.raises(LiveProposalFailed, match="unsupported label"):
        score_predictions(rows, path)


@pytest.mark.parametrize(
    "data",
    [
        "id,feature_0,label\n",
        "id,feature_0,label\na,0.1,unknown\n",
        "id,feature_0,label\na,0.1,negative\na,0.2,negative\n",
    ],
)
def test_empty_duplicated_or_invalid_labelled_datasets_are_rejected(tmp_path: Path, data: str) -> None:
    dataset = tmp_path / "invalid.csv"
    dataset.write_text(data)
    with pytest.raises(ValueError):
        read_dataset(dataset)


def test_missing_or_computed_threshold_source_is_rejected() -> None:
    for source in ("OTHER=0.5\n", "THRESHOLD=0.2+0.3\n", "THRESHOLD=0.5\nTHRESHOLD=0.6\n"):
        with pytest.raises(ValueError, match="one literal"):
            mutate_threshold(source, 0.4)


def test_missing_or_unpinned_images_do_not_trigger_download_or_host_execution(tmp_path: Path) -> None:
    with pytest.raises(LiveCapabilityBlocked, match="pinned local"):
        require_docker_image("", tmp_path)
    with pytest.raises(ValueError, match="immutable"):
        require_docker_image("python:latest", tmp_path)


def test_model_digest_is_bound_before_and_after_actual_http_generation(tmp_path: Path) -> None:
    with controlled_provider(digests=("a" * 64, "b" * 64)) as (endpoint, _):
        with pytest.raises(LiveProposalFailed, match="response failed"):
            request_proposal(ProposalSettings("controlled-http-fixture", "", endpoint), "public only", tmp_path)
    identity = json.loads((tmp_path / "model_identity.json").read_text())
    assert identity == {
        "model": "controlled-http-fixture",
        "before_sha256": "a" * 64,
        "after_sha256": "b" * 64,
        "status": "failed",
    }
    assert not (tmp_path / "model_response.json").exists()


def test_invalid_installed_model_digest_cannot_establish_model_custody(tmp_path: Path) -> None:
    with controlled_provider(digests=("mutable-name",)) as (endpoint, _):
        with pytest.raises(ValueError, match="SHA-256"):
            ollama_generate(endpoint, {"model": "controlled-http-fixture"})


def test_frozen_dataset_change_invalidates_live_acceptance(
    tmp_path: Path,
    image_id: str,
    copy_project_sandbox,
) -> None:
    project = copy_project_sandbox(tmp_path / "project")
    dataset = project / "tasks/mini_classify/data/public/train.csv"
    original = dataset.read_bytes()
    with controlled_provider(on_request=lambda: dataset.write_bytes(original + b"\n")) as (endpoint, _):
        with pytest.raises(LiveProposalFailed, match="frozen dataset changed"):
            run_live_proposals(
                project,
                project / "output/input-drift",
                ProposalSettings("controlled-http-fixture", image_id, endpoint, 2),
            )
    receipt = json.loads((project / "output/input-drift/live_proposal_receipt.json").read_text())
    assert receipt["status"] == "failed" and not receipt["frozen_inputs_verified"]
    assert receipt["rollback_verified"] and not (project / "output/input-drift/heldout").exists()


def test_container_watchdog_survives_entire_supervised_controller_tree_kill(tmp_path: Path, image_id: str) -> None:
    from template_sia.loop.proposal_sandbox import command

    output = tmp_path / "interrupted"
    docker = require_docker_image(image_id, tmp_path)
    execution = output / "execution.json"
    observed_running = threading.Event()
    stop_monitor = threading.Event()

    def monitor() -> None:
        while not stop_monitor.wait(0.05):
            if not execution.is_file():
                continue
            try:
                receipt = json.loads(execution.read_text())
            except ValueError:
                continue
            result = subprocess.run(
                [docker, "container", "inspect", "--format", "{{.State.Running}}", receipt["container_name"]],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip() == "true":
                observed_running.set()
                return

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    source = (
        "import sys; from pathlib import Path; "
        f"sys.path[:0]=[{str(PROJECT.parents[2])!r},{str(PROJECT / 'src')!r}]; "
        "from template_sia.loop.proposal_sandbox import run_target; "
        f"run_target({docker!r},{image_id!r},'while True: pass\\n',"
        f"({{'id':'a','feature_0':'0.1','label':'negative'}},),Path({str(output)!r}),60)"
    )
    name = None
    sandbox = None
    try:
        command_started = time.monotonic()
        killed = command([sys.executable, "-I", "-c", source], tmp_path, 6)
        assert killed.timed_out and killed.returncode < 0
        assert observed_running.is_set(), "interruption control must observe an actual running container"
        receipt = json.loads(execution.read_text())
        name, sandbox = receipt["container_name"], Path(receipt["sandbox_root"])
        assert receipt["status"] == "launching" and not receipt["cleanup_verified"]
        assert receipt["container_deadline_sec"] == 60 and receipt["controller_heartbeat_grace_sec"] == 2
        deadline = command_started + 6 + 8
        while True:
            inspected = subprocess.run(
                [docker, "container", "inspect", name], capture_output=True, text=True, timeout=5, check=False
            )
            if inspected.returncode and (
                "No such object" in inspected.stderr or "No such container" in inspected.stderr
            ):
                break
            assert time.monotonic() < deadline, "container watchdog failed to remove the interrupted daemon container"
            time.sleep(0.1)
    finally:
        stop_monitor.set()
        thread.join(timeout=6)
        if name is None and execution.is_file():
            receipt = json.loads(execution.read_text())
            name, sandbox = receipt["container_name"], Path(receipt["sandbox_root"])
        if name is not None:
            subprocess.run([docker, "rm", "--force", name], capture_output=True, timeout=5, check=False)
        if sandbox is not None:
            shutil.rmtree(sandbox, ignore_errors=True)
