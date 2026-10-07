"""Actual QR children with rehashed portable replay corruption controls."""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import pytest
import qrcode
from PIL import Image

from infrastructure.reporting.native_qr_runtime import bind_qr_core, finish_qr_core, replay_projection_qr_runtime
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record


@pytest.mark.parametrize("payload", ["baseline-qr", "wrong-qr", None])
def test_real_qr_children_and_rehashed_malformed_replay(tmp_path: Path, payload: str | None) -> None:
    selected = shutil.which("zbarimg")
    if selected is None:
        pytest.skip("actual source-selected zbarimg prerequisite absent")
    directory = tmp_path / "output/readiness/qr"
    directory.mkdir(parents=True)
    pixel = directory / "qr-page-1.png"
    if payload is None:
        Image.new("RGB", (300, 300), "white").save(pixel)
    else:
        qrcode.make(payload).save(pixel)
    env = {"PATH": os.environ["PATH"]}
    deadline = time.monotonic() + 30
    runtime, core, original = bind_qr_core(tmp_path, directory, env=env, deadline=deadline, run_id="real-qr", ordinal=1)
    decoded = native_tool_record(
        tmp_path,
        directory,
        "zbarimg",
        ["--quiet", "--raw", "--set", "disable", "--set", "qrcode.enable", str(pixel)],
        env=env,
        deadline=deadline,
        run_id="real-qr",
        purpose="qr-decode-1",
    )
    binding = finish_qr_core(tmp_path, directory, runtime, core, original, ordinal=1)
    row = {
        "raster_sha256": hashlib.sha256(pixel.read_bytes()).hexdigest(),
        "target": "baseline-qr",
        "decoded": [] if payload is None else [payload],
        "tool_artifact": decoded["artifact"],
        "runtime_artifact": binding,
        "original_exit_code": 4 if payload is None else 0,
        "findings": [],
        "status": "passed" if payload == "baseline-qr" else "failed",
    }

    def read(binding: dict) -> bytes:
        return (tmp_path / binding["path"]).read_bytes()

    def replay() -> None:
        replay_projection_qr_runtime(
            row, read_artifact=read, producer_path=lambda p: str(tmp_path / p), run_id="real-qr"
        )

    replay()
    actual_outcome = row["original_exit_code"]
    for malformed in (False, 0.0):
        row["original_exit_code"] = malformed
        with pytest.raises(ValueError):
            replay()
    row["original_exit_code"] = actual_outcome
    assert not list(directory.glob("qr-core-*.bin"))
    assert sum(p.stat().st_size for p in directory.iterdir()) < 100 * 1024 * 1024
    path = tmp_path / row["tool_artifact"]["path"]
    original_tool = path.read_bytes()
    for field, value in [
        ("exit_code", False),
        ("exit_code", 0.0),
        ("original_exit_code", False),
        ("original_exit_code", 0.0),
        ("timed_out", 0),
        ("custody_refused", None),
        ("diagnostic", False),
        ("executable_observation_after", {}),
        ("executable_observation_before", {}),
    ]:
        changed = json.loads(original_tool)
        changed[field] = value
        path.write_text(json.dumps(changed))
        row["tool_artifact"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with pytest.raises(ValueError):
            replay()
    path.write_bytes(original_tool)
    row["tool_artifact"]["sha256"] = hashlib.sha256(original_tool).hexdigest()
    runtime_path = tmp_path / binding["path"]
    raw_original = runtime_path.read_bytes()
    raw = json.loads(raw_original)
    raw["core_observation_after"]["metadata"]["size"] += 1
    runtime_path.write_text(json.dumps(raw))
    row["runtime_artifact"]["sha256"] = hashlib.sha256(runtime_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        replay()
    raw = json.loads(raw_original)
    for key in ("core_observation_before", "core_observation_after"):
        raw[key]["metadata"]["mode"] = False
    runtime_path.write_text(json.dumps(raw))
    row["runtime_artifact"]["sha256"] = hashlib.sha256(runtime_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        replay()
    runtime_path.write_bytes(raw_original)
    row["runtime_artifact"]["sha256"] = hashlib.sha256(raw_original).hexdigest()
    # No producer-prefix read is needed by replay after raster deletion.
    pixel.unlink()
    replay()
