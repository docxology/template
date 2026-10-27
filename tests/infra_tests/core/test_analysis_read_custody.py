"""Actual selected-runtime reads and genuine post-script interruption controls."""

import json
import os
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from infrastructure.core.analysis_launch import analysis_receipt_path, launch_analysis_script
from infrastructure.core.pipeline.outcomes import StageStatus
from infrastructure.core.runtime._python_env import build_analysis_script_cmd_and_env

pytestmark = pytest.mark.timeout(180)


@pytest.fixture(autouse=True)
def _source_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")


def _project(tmp_path: Path, body: str) -> tuple[Path, Path, Path]:
    repo = tmp_path.resolve()
    project = repo / "projects/demo"
    for directory in ("src", "scripts", "tests", "output"):
        (project / directory).mkdir(parents=True)
    script = project / "scripts/leaf.py"
    script.write_text(body)
    return repo, project, script


def _launch(repo: Path, project: Path, script: Path):
    cmd, env = build_analysis_script_cmd_and_env(script, project, repo)
    env.update(PIPELINE_RUN_ID="actual-read-control", PIPELINE_PLAN_DIGEST="a" * 64)
    result = launch_analysis_script(script, repo, project, cmd, env, time.monotonic() + 90)
    receipt = json.loads(analysis_receipt_path(project, env["PIPELINE_RUN_ID"], result.stage_key).read_text())
    return result, receipt


def test_actual_api_returns_and_retains_each_repeated_input_body(tmp_path: Path) -> None:
    repo, project, script = _project(
        tmp_path,
        "from pathlib import Path\nfrom infrastructure.core.analysis_read_custody import read_analysis_bytes\n"
        "root=Path(__file__).parents[1]\n"
        "first=read_analysis_bytes(root,root/'data/input.csv')\n"
        "second=read_analysis_bytes(root,root/'data/input.csv')\n"
        "assert first == second == b'value\\n-2.50\\n'\n",
    )
    (project / "data").mkdir()
    (project / "data/input.csv").write_bytes(b"value\n-2.50\n")
    result, receipt = _launch(repo, project, script)
    assert result.status is StageStatus.SUCCEEDED
    packet = receipt["worker"]
    reads = packet["completion"]["analysis_reads"]
    assert reads["owner_pid"] == packet["original_process"]["pid"]
    assert reads["analysis_nonce"] == packet["request"]["analysis_nonce"]
    assert [row["ordinal"] for row in reads["records"]] == [1, 2]
    for row in reads["records"]:
        assert row["origin"] == "original-incoming-body"
        assert row["consumer"]["source"] == "projects/demo/scripts/leaf.py"
        assert project.joinpath(row["retained_path"]).read_bytes() == b"value\n-2.50\n"


def test_real_repeated_long_path_reads_refuse_oversized_metadata_and_keep_known_original(tmp_path: Path) -> None:
    repo, project, script = _project(
        tmp_path,
        "from pathlib import Path\nfrom infrastructure.core.analysis_read_custody import read_analysis_bytes\n"
        "root=Path(__file__).parents[1]\n"
        "path=root/'data'\n"
        "for _ in range(20): path=path/'abcdefghijklmnopqrstuvwxy'\n"
        "for _ in range(6000): assert read_analysis_bytes(root,path/'body.txt') == b'x'\n",
    )
    path = project / "data"
    for _ in range(20):
        path /= "abcdefghijklmnopqrstuvwxy"
    path.mkdir(parents=True)
    (path / "body.txt").write_bytes(b"x")
    result, receipt = _launch(repo, project, script)
    assert result.status is StageStatus.BLOCKED and result.attempt_exit_codes == (0,)
    assert result.child_exit_code == 0 and receipt["complete"] is False
    assert "metadata exceeds" in result.diagnostic


@pytest.mark.parametrize(
    ("script_intent", "status"),
    [(0, StageStatus.BLOCKED), (17, StageStatus.FAILED), (124, StageStatus.TIMED_OUT), (130, StageStatus.INTERRUPTED)],
)
def test_actual_result_persistence_failure_keeps_script_intent_and_independently_reaped_worker_os(
    tmp_path: Path, script_intent: int, status: StageStatus
) -> None:
    repo, project, script = _project(
        tmp_path,
        "import sys\nfrom pathlib import Path\n"
        "scratch=Path(sys.pycache_prefix).parent\n"
        "(scratch/'result.json').mkdir()\n"
        f"raise SystemExit({script_intent})\n",
    )
    result, receipt = _launch(repo, project, script)
    assert result.status is status and result.child_exit_code == script_intent
    assert result.attempt_exit_codes == (script_intent,) and receipt["complete"] is False
    worker = receipt["worker"]
    checkpoint, process = worker["original_checkpoint"], worker["original_process"]
    assert checkpoint["original_exit_code"] == script_intent and checkpoint["completion_authorized"] is False
    assert process["original_exit_code"] == process["observed_exit_code"] == 1
    assert process["pid"] == checkpoint["pid"]
    assert process["request_digest"] == checkpoint["request_digest"]
    assert process["analysis_nonce"] == checkpoint["analysis_nonce"]
    assert "completion" not in worker


@pytest.mark.parametrize("original", [0, 7])
def test_post_script_interrupt_retains_original_without_completion(tmp_path: Path, original: int) -> None:
    repo, project, script = _project(
        tmp_path,
        "import json,os,sys\nfrom pathlib import Path\n"
        "root=Path(__file__).parents[1]\n(root/'output/data').mkdir()\n"
        "for i in range(3000): (root/'output/data'/f'body-{i}.txt').write_text('held')\n"
        "(root/'output/worker-state.json').write_text(json.dumps({'pid':os.getpid(),"
        "'scratch':str(Path(sys.pycache_prefix).parent)}))\n"
        f"raise SystemExit({original})\n",
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_launch, repo, project, script)
        stop = time.monotonic() + 90
        signalled = False
        while not future.done() and time.monotonic() < stop:
            state_file = project / "output/worker-state.json"
            if state_file.is_file():
                try:
                    state = json.loads(state_file.read_text())
                    checkpoint = Path(state["scratch"]) / "original.json"
                    if checkpoint.is_file():
                        observed = json.loads(checkpoint.read_text())
                        if observed["original_exit_code"] == original and observed["pid"] == state["pid"]:
                            os.kill(state["pid"], signal.SIGINT)
                            signalled = True
                            break
                except OSError, ValueError:
                    pass  # Atomic private promotion may still be in flight.
            time.sleep(0.001)
        result, receipt = future.result(timeout=90)
    assert signalled and result.status is StageStatus.INTERRUPTED
    assert result.child_exit_code == original and result.attempt_exit_codes == (original,)
    assert receipt["complete"] is False
