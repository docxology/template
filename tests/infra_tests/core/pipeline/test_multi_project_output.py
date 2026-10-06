"""Actual noisy workers cannot exceed the spool cap or leave detached children."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core._bounded_run_guardian import start_bounded_run_guardian
from infrastructure.core.execution_boundary import build_bounded_env, build_bounded_run_env
from infrastructure.core.pipeline.multi_project_output import BoundedWorkerOutput, WORKER_OUTPUT_LIMIT
from infrastructure.core.pipeline.multi_project_runtime import _Running, _finish, freeze_project_plans
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


@pytest.mark.timeout(30)
def test_actual_noisy_worker_spool_is_hard_capped_and_descendants_reaped(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("templates/alpha",))
    spec = freeze_project_plans(("templates/alpha",), tmp_path, mode="core", resume=False, timeout=20)[0]
    environment = build_bounded_env()
    process_env, token = build_bounded_run_env(environment)
    guardian = start_bounded_run_guardian(environment)
    marker = tmp_path / "worker-pids.json"
    program = (
        "import json,os,subprocess,sys,time;from pathlib import Path;"
        "child=subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(30)'],start_new_session=True);"
        "Path(sys.argv[1]).write_text(json.dumps({'worker':os.getpid(),'detached':child.pid}));"
        "block=b'x'*65536;"
        "[os.write(1,block) for _ in range(1024)];time.sleep(30)"
    )
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", program, str(marker)],
        env=process_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    assert process.stdout is not None
    output = BoundedWorkerOutput(process.stdout)
    running = _Running(spec, process, guardian, token, "test", tmp_path / "missing.json", tmp_path, output)
    try:
        if guardian is not None:
            guardian.arm(root_pid=process.pid, run_token=token)
        deadline = time.monotonic() + 10
        while not output.overflow.is_set() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert output.overflow.is_set()
        assert output.size == WORKER_OUTPUT_LIMIT
        assert os.fstat(output.log.fileno()).st_size <= WORKER_OUTPUT_LIMIT
        rows, run = _finish(running, deadline)
        assert run.exit_code == 1 and not run.complete
        assert any("8 MiB bound" in row.error_message for row in rows)
        assert (
            len((spec.config.project_dir / "output/logs/multi_project_worker.log").read_bytes()) == WORKER_OUTPUT_LIMIT
        )
        assert not output.thread.is_alive()
        for pid in json.loads(marker.read_text()).values():
            status = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
            assert not status.stdout.strip() or status.stdout.strip().startswith("Z")
    finally:
        running.close(terminate=True)
        output.close()
