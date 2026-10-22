"""Actual Darwin worker/ToolAPI custody and independently changed owned DATA."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.auxiliary_print_code import ROLE, require_entry
from infrastructure.project.public_acceptance_auxiliary_bootstrap import WORKER, prepare_audited_auxiliary_command
from infrastructure.project.public_acceptance_auxiliary_supervision import supervise
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_auxiliary_print_custody import (
    AuxiliaryPrintOriginal,
    AuxiliaryPrintProducerOperation,
    AuxiliaryPrintReaderOperation,
)
from infrastructure.reporting.native_print_witness_validation import validate_print_witness
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_receipt_data_cannot_enter_live_or_completed_auxiliary_print_role(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="actual audited fixed worker entry"):
        require_entry(tmp_path)
    with pytest.raises(ValueError, match="actual audited fixed worker entry"):
        AuxiliaryPrintProducerOperation(tmp_path, tmp_path / "output/readiness/print")
    with pytest.raises(ValueError, match="genuine supervisor/collector"):
        AuxiliaryPrintOriginal(object(), tmp_path, {}, os.getpid(), {}, {}, time.monotonic())
    from infrastructure.reporting.native_auxiliary_print_custody import _ORIGINAL

    with pytest.raises(ValueError, match="actual supervisor/collector call"):
        AuxiliaryPrintOriginal(_ORIGINAL, tmp_path, {}, os.getpid(), {}, {}, time.monotonic())
    with pytest.raises(ValueError, match="externally held original"):
        AuxiliaryPrintReaderOperation({"pid": os.getpid()}, tmp_path, time.monotonic() + 10)  # type: ignore[arg-type]


def test_print_payload_reconstruction_is_canonical_after_json_roundtrip() -> None:
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import _body

    root = Path(__file__).resolve().parents[3]
    directory = root / "output/readiness/owned-print-generation/execution"
    spec = directory.parent / "spec.json"
    held = {
        "spec_path": str(spec),
        "spec_sha256": "a" * 64,
        "run_id": uuid.uuid4().hex,
        "deadline": time.monotonic() + 30,
        "parent_pid": os.getpid(),
        "producer_root": str(root),
    }
    original = _body(
        Path(sys.executable), root, WORKER, ("--spec", str(spec)), directory, original_root=root, print_nomination=held
    )
    retained = json.loads(json.dumps(held, sort_keys=True))
    assert list(held) != list(retained)
    assert (
        _body(
            Path(sys.executable),
            root,
            WORKER,
            ("--spec", str(spec)),
            directory,
            original_root=root,
            print_nomination=retained,
        )
        == original
    )


@pytest.mark.parametrize("escape", ["traversal", "symlink"])
def test_print_collector_refuses_escape_before_creating_evidence(tmp_path: Path, escape: str) -> None:
    from infrastructure.project.auxiliary_print_hosted import collect_auxiliary_print_original

    root = tmp_path / "source"
    readiness = root / "output/readiness"
    readiness.mkdir(parents=True)
    outside = tmp_path / "outside"
    if escape == "traversal":
        directory = readiness / "../../../outside/collected"
    else:
        outside.mkdir()
        (readiness / "alias").symlink_to(outside, target_is_directory=True)
        directory = readiness / "alias/collected"
    with pytest.raises(ValueError, match="canonical|symlink"):
        collect_auxiliary_print_original(
            root,
            directory,
            repository="docxology/template",
            run_id=39077939242,
            head_sha="a" * 40,
            deadline=time.monotonic() + 10,
            environment={},
        )
    assert not (outside / "collected").exists()
    if escape == "traversal":
        assert not outside.exists()


@pytest.fixture(scope="module")
def actual_print(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    if platform.system() != "Darwin":
        pytest.skip("the actual fixed print producer requires Darwin")
    if not all(shutil.which(name) for name in ("pandoc", "pdftoppm", "pdffonts")):
        pytest.fail("the nominated actual Darwin print tools must be prepared")
    source = Path(__file__).resolve().parents[3]
    root = tmp_path_factory.mktemp("auxiliary-print") / "producer"
    root.mkdir()
    shutil.copytree(
        source / "infrastructure", root / "infrastructure", ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(source / name, root / name)
    for kind in ("storybook", "newspaper"):
        origin = source / f"projects/templates/template_{kind}"
        project = root / f"projects/templates/template_{kind}"
        project.mkdir(parents=True)
        for name in ("src", "content"):
            shutil.copytree(origin / name, project / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(origin / "pyproject.toml", project / "pyproject.toml")
    directory = root / "output/readiness/auxiliary-darwin/001"
    deadline = time.monotonic() + 180
    spec = write_json(
        root,
        directory / "spec.json",
        {
            "gate": ROLE,
            "budget": 180,
            "raw_path": "output/readiness/auxiliary-darwin/001/facts.json",
            "run_id": uuid.uuid4().hex,
            "operation_deadline": deadline,
            "parent_pid": os.getpid(),
        },
    )
    command, payload = prepare_audited_auxiliary_command(
        Path(sys.executable), root, WORKER, ("--spec", str(root / spec["path"])), directory / "execution"
    )
    originals: list[Any] = []
    process = supervise(
        command, root, directory / "execution", deadline, bootstrap_payload=payload, print_originals=originals
    )
    facts = json.loads((directory / "facts.json").read_bytes()) if (directory / "facts.json").exists() else {}
    assert process["accepted"] and process["exit_code"] == 0, {
        "exit": process["exit_code"],
        "facts": {k: facts.get(k) for k in ("status", "diagnostic", "failure_class")},
        "stderr": (directory / "execution/stderr.txt").read_text()[-4000:],
    }
    assert len(originals) == 1 and not (directory / "execution/bytecode").exists()
    assert len(originals[0]._events) == 8
    moved = root.with_name("reader")
    shutil.copytree(root, moved)
    shutil.rmtree(root)
    return {"root": moved, "original": originals[0], "facts": facts, "process": process}


@pytest.mark.timeout(300, method="thread")
def test_actual_fixed_print_worker_and_relocated_original_replay(actual_print: dict[str, Any]) -> None:
    root, original = actual_print["root"], actual_print["original"]
    deadline = time.monotonic() + 90
    reader = SnapshotReader(
        root,
        native_control_operation=AuxiliaryPrintReaderOperation(original, root, deadline),
        operation_deadline=deadline,
    )
    validate_print_witness(
        original.binding,
        reader,
        expected_pid=actual_print["facts"]["pid"],
        expected_runtime=actual_print["facts"]["runtime"],
        deadline=deadline,
    )
    assert reader.unchanged()


@pytest.mark.timeout(300, method="thread")
@pytest.mark.parametrize(
    "fault",
    ["witness-rehash", "tool-rehash", "process-rehash", "code", "source", "plain-reader", "expired", "infinite"],
)
def test_actual_print_held_original_refuses_changed_or_unowned_replay(actual_print: dict[str, Any], fault: str) -> None:
    root, original = actual_print["root"], actual_print["original"]
    deadline = time.monotonic() + 90
    changed: Path | None = None
    before: bytes | None = None
    binding = dict(original.binding)
    try:
        if fault in {"witness-rehash", "tool-rehash", "process-rehash"}:
            changed = root / binding["path"]
            before = changed.read_bytes()
            value = json.loads(before)
            if fault == "witness-rehash":
                value["runtime"]["python_version"] = "3.12"
            else:
                tool_binding = value["versions"]["pdftoppm"]
                tool = json.loads((root / tool_binding["path"]).read_bytes())
                if fault == "process-rehash":
                    process = json.loads((root / tool["native_process_artifact"]["path"]).read_bytes())
                    process["pid"] += 1
                    process_target = changed.parent / "changed-original-process.json"
                    process_target.write_text(json.dumps(process))
                    tool["native_process_artifact"] = {
                        "path": process_target.relative_to(root).as_posix(),
                        "sha256": hashlib.sha256(process_target.read_bytes()).hexdigest(),
                    }
                else:
                    tool["pid"] += 1
                # A rehashed replacement remains DATA even when a new witness
                # consistently nominates its new bytes.
                target = changed.parent / (fault + ".json")
                target.write_text(json.dumps(tool))
                value["versions"]["pdftoppm"] = {
                    "path": target.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            changed.write_text(json.dumps(value))
            binding["sha256"] = hashlib.sha256(changed.read_bytes()).hexdigest()
        elif fault == "code":
            changed = root / original.code["path"]
            before = changed.read_bytes()
            changed.write_bytes(before + b" ")
        elif fault == "source":
            changed = root / "infrastructure/project/auxiliary_print_code.py"
            before = changed.read_bytes()
            changed.write_bytes(before + b"\n# independently changed owned Source\n")
        elif fault == "expired":
            deadline = time.monotonic() - 1
        elif fault == "infinite":
            deadline = float("inf")
        with pytest.raises((ValueError, TimeoutError)):
            operation = None if fault == "plain-reader" else AuxiliaryPrintReaderOperation(original, root, deadline)
            validate_print_witness(
                binding,
                SnapshotReader(root, native_control_operation=operation, operation_deadline=deadline),
                expected_pid=actual_print["facts"]["pid"],
                expected_runtime=actual_print["facts"]["runtime"],
                deadline=deadline,
            )
    finally:
        if changed is not None and before is not None:
            changed.write_bytes(before)


@pytest.mark.parametrize("fault", ["foreign", "digest", "missing"])
def test_authenticated_print_archive_closure_refuses_redirected_evidence(fault: str) -> None:
    from infrastructure.project.auxiliary_print_hosted import _authenticate_closure

    body = b'{"details":{}}'
    path = "output/readiness/auxiliary-darwin/001/gate.json"
    reference = {"artifact": path, "artifact_sha256": hashlib.sha256(body).hexdigest()}
    members = {"001/gate.json": body}
    if fault == "foreign":
        reference["artifact"] = "output/readiness/other/gate.json"
    elif fault == "digest":
        reference["artifact_sha256"] = "0" * 64
    else:
        members.clear()
    with pytest.raises(ValueError, match="authenticated"):
        _authenticate_closure(members, {}, reference, deadline=time.monotonic() + 10)


def test_bounded_archive_walk_keeps_complete_large_source_inventory_as_data() -> None:
    from infrastructure.project.auxiliary_print_hosted import _authenticate_closure

    rows = [[f"module-{index:05d}.py", "file", 0o644, "f" * 64] for index in range(6000)]
    body = json.dumps({"source_before": rows, "source_after": rows}).encode()
    reference = {
        "artifact": "output/readiness/auxiliary-darwin/001/gate.json",
        "artifact_sha256": hashlib.sha256(body).hexdigest(),
    }
    _authenticate_closure({"001/gate.json": body}, {}, reference, deadline=time.monotonic() + 10)
    # Successful DATA closure creates neither an original nor a live owner.
    with pytest.raises(ValueError, match="actual audited fixed worker entry"):
        require_entry(Path.cwd())
