"""Genuine isolated children and owned Source copies; no acceptance fabricated."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from infrastructure.project.acceptance_payload import format_acceptance_payload_loader, write_acceptance_payload
from infrastructure.project.public_acceptance_auxiliary import supervise
from infrastructure.project.public_acceptance_auxiliary_bootstrap import (
    PAYLOAD,
    WORKER,
    prepare_audited_auxiliary_command,
    validate_audited_auxiliary_command,
)
from infrastructure.project.public_acceptance_auxiliary_pipeline import (
    AuxiliaryPipelineFailure,
    _retain_pipeline_child_facts,
)
from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Copy actual SDK bodies, without private resources or replacing a member."""
    original = Path(__file__).resolve().parents[3]
    root = tmp_path / "source"
    root.mkdir()
    shutil.copytree(
        original / "infrastructure",
        root / "infrastructure",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "kmyth"),
    )
    shutil.copyfile(original / "pyproject.toml", root / "pyproject.toml")
    return root


def test_real_worker_uses_private_preimport_audit_and_portable_exact_command(source: Path, tmp_path: Path) -> None:
    directory = source / "output/readiness/owned-audit"
    directory.mkdir(parents=True)
    spec = directory / "spec.json"
    spec.write_text(
        json.dumps({"gate": "root:docs_lint", "negative": True, "raw_path": "output/readiness/owned-audit/facts.json"})
    )
    command, payload = prepare_audited_auxiliary_command(
        Path(sys.executable), source, WORKER, ("--spec", str(spec)), directory / "execution"
    )
    assert len(command[3].encode()) < 32 * 1024
    assert payload["identity"]["size"] > len(command[3].encode())
    process = supervise(command, source, directory / "execution", time.monotonic() + 30, bootstrap_payload=payload)
    assert process["exit_code"] == 23 and not process["timed_out"]
    facts = json.loads((directory / "facts.json").read_bytes())
    assert facts["status"] == "negative-control" and facts["exit_code"] == 23
    assert facts["runtime"]["pycache_prefix"] == str(directory / "execution/bytecode")
    assert not (directory / "execution/bytecode").exists()
    validate_audited_auxiliary_command(
        SnapshotReader(source),
        process,
        module=WORKER,
        arguments=("--spec", str(spec)),
        execution_relative="output/readiness/owned-audit/execution",
    )
    # Portable regeneration authenticates retained bytes without reopening the
    # deleted original prefix or requiring original inode identity at readback.
    moved = tmp_path / "relocated"
    shutil.copytree(source, moved)
    validate_audited_auxiliary_command(
        SnapshotReader(moved),
        process,
        module=WORKER,
        arguments=("--spec", str(spec)),
        execution_relative="output/readiness/owned-audit/execution",
    )
    changed = dict(process)
    changed["command"] = [*command[:-1], str(spec) + ".other"]
    with pytest.raises(ValueError, match="exact Source-derived"):
        validate_audited_auxiliary_command(
            SnapshotReader(moved),
            changed,
            module=WORKER,
            arguments=("--spec", str(spec)),
            execution_relative="output/readiness/owned-audit/execution",
        )
    (moved / "output/readiness/owned-audit/execution" / PAYLOAD).chmod(0o600)
    with (moved / "output/readiness/owned-audit/execution" / PAYLOAD).open("ab") as stream:
        stream.write(b"\n# changed owned DATA\n")
    with pytest.raises(ValueError, match="exact current Source"):
        validate_audited_auxiliary_command(
            SnapshotReader(moved),
            process,
            module=WORKER,
            arguments=("--spec", str(spec)),
            execution_relative="output/readiness/owned-audit/execution",
        )


def test_real_fresh_bytecode_verifier_passes_only_after_audited_bootstrap(source: Path, tmp_path: Path) -> None:
    probe = source / "probe.py"
    probe.write_text(
        "from pathlib import Path\nimport sys\nfrom infrastructure.core.implementation_custody import verify_fresh_module_bytecode\nverify_fresh_module_bytecode(Path(__file__).parent/'infrastructure',Path(sys.pycache_prefix))\nprint('actual preimport audit verified')\n"
    )
    prefix = tmp_path / "private-bytecode"
    prefix.mkdir(mode=0o700)
    audit = bootstrap_command(
        Path(sys.executable),
        source,
        "probe",
        command_root=source,
        implementation_root=source / "infrastructure",
        fresh_pycache_prefix=prefix,
    )
    payload = write_acceptance_payload(
        tmp_path, tmp_path / "probe.payload", audit[3].encode(), forbidden_roots=(source,)
    )
    result = subprocess.run(
        [*audit[:3], format_acceptance_payload_loader(payload), *audit[4:]],
        cwd=source,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")[-1000:]
    assert result.stdout == b"actual preimport audit verified\n"
    unaudited = subprocess.run(
        [sys.executable, "-X", f"pycache_prefix={tmp_path / 'unaudited'}", "-m", "probe"],
        cwd=source,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert unaudited.returncode != 0
    assert b"fresh bytecode requires a pre-import executed-code audit" in unaudited.stderr


@pytest.mark.parametrize("kind", ["nonempty", "alias", "permissions"])
def test_actual_bootstrap_refuses_unowned_or_reused_prefix(source: Path, tmp_path: Path, kind: str) -> None:
    if os.name != "posix":
        pytest.skip("actual UID/permission contract uses declared POSIX hosts")
    prefix = tmp_path / "bytecode"
    prefix.mkdir(mode=0o700)
    if kind == "nonempty":
        (prefix / "stale").write_bytes(b"old cache")
    elif kind == "alias":
        alias = tmp_path / "alias"
        alias.symlink_to(prefix, target_is_directory=True)
        prefix = alias
    else:
        prefix.chmod(0o755)
    command = bootstrap_command(
        Path(sys.executable),
        source,
        "no_such_probe",
        command_root=source,
        implementation_root=source / "infrastructure",
        fresh_pycache_prefix=prefix,
    )
    payload = write_acceptance_payload(
        tmp_path, tmp_path / "refused.payload", command[3].encode(), forbidden_roots=(source,)
    )
    result = subprocess.run(
        [*command[:3], format_acceptance_payload_loader(payload), *command[4:]],
        cwd=source,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0 and b"empty private owned directory" in result.stderr


def test_pipeline_failure_retains_actual_original_exit_and_stage_diagnostic() -> None:
    process = {"exit_code": 1, "timed_out": False}
    facts = {
        "original_exit_code": 1,
        "execution": {
            "outcomes": [
                {"stage_key": "project_tests", "status": "failed", "diagnostic": "actual project verifier failed"}
            ]
        },
    }
    error = AuxiliaryPipelineFailure(process, facts, {"facts_artifact": {"path": "owned-facts.json"}})
    assert error.code == 1 and error.observation["original_exit_code"] == 1
    assert "project_tests" in str(error) and "actual project verifier failed" in str(error)
    assert AuxiliaryPipelineFailure({"exit_code": -9, "timed_out": True}, facts, {}).code == 124
    assert AuxiliaryPipelineFailure({"exit_code": -2, "timed_out": False}, facts, {}).code == 130


@pytest.mark.parametrize(
    ("mode", "content", "expected"),
    [
        ("timeout", None, 124),
        ("nonzero", None, 1),
        ("interrupt", None, 130),
        ("nonzero", "{truncated", 1),
        ("nonzero", '{"execution": null}', 1),
    ],
)
def test_real_failed_child_without_complete_facts_preserves_os_outcome(
    tmp_path: Path, mode: str, content: str | None, expected: int
) -> None:
    inner = tmp_path / "output/readiness/inner"
    inner.mkdir(parents=True)
    body = (
        "import pathlib,sys,time\n"
        "if sys.argv[2] != 'absent': pathlib.Path(sys.argv[1]).write_text(sys.argv[2])\n"
        "print('actual child failure diagnostic',file=sys.stderr,flush=True)\n"
        "if sys.argv[3] == 'timeout': time.sleep(60)\n"
        "if sys.argv[3] == 'interrupt': raise KeyboardInterrupt\n"
        "raise SystemExit(7)\n"
    )
    process = supervise(
        [sys.executable, "-I", "-c", body, str(inner / "facts.json"), content or "absent", mode],
        tmp_path,
        inner / "execution",
        time.monotonic() + (1 if mode == "timeout" else 15),
    )
    assert process["timed_out"] is (mode == "timeout")
    assert process["exit_code"] == (-9 if mode == "timeout" else -2 if mode == "interrupt" else 7)
    assert b"actual child failure diagnostic" in (tmp_path / process["streams"]["stderr"]["path"]).read_bytes()
    with pytest.raises(AuxiliaryPipelineFailure) as caught:
        _retain_pipeline_child_facts(
            tmp_path, tmp_path / "output/readiness/retained", inner, process, {"streams": process["streams"]}
        )
    assert caught.value.code == expected
    assert caught.value.observation["original_exit_code"] == process["exit_code"]
    assert caught.value.observation["streams"] == process["streams"]
    if content is None:
        assert caught.value.observation["facts_artifact"] == {}
    else:
        assert (tmp_path / caught.value.observation["facts_artifact"]["path"]).read_text() == content
    # A zero exit never admits missing or malformed facts as positive evidence.
    if content is None or content == "{truncated":
        from infrastructure.project.public_acceptance_auxiliary_supervision import complete_auxiliary_observation

        positive_directory = tmp_path / "output/readiness/positive"
        successful = supervise(
            [sys.executable, "-I", "-c", "pass"],
            tmp_path,
            positive_directory / "execution",
            time.monotonic() + 15,
        )
        assert successful["exit_code"] == 0
        assert complete_auxiliary_observation(successful), "zero-exit control lacks complete supervision"
        with pytest.raises(ValueError, match="original facts") as incomplete:
            _retain_pipeline_child_facts(tmp_path, positive_directory, inner, successful, {})
        assert type(incomplete.value) is ValueError


def test_audited_launch_refuses_changed_source_hook_before_executing(source: Path) -> None:
    hook = source / "infrastructure/core/bytecode_audit.py"
    hook.write_bytes(hook.read_bytes() + b"\n# Owned changed audit DATA control.\n")
    directory = source / "output/readiness/refused-source/execution"
    with pytest.raises(ValueError, match="nominated Source body"):
        prepare_audited_auxiliary_command(Path(sys.executable), source, WORKER, (), directory)
    assert not (directory / PAYLOAD).exists()


def test_zero_exit_with_failed_logical_validation_retains_original_facts(tmp_path: Path) -> None:
    process = supervise(
        [sys.executable, "-I", "-c", "print('actual successful pipeline child')"],
        tmp_path,
        tmp_path / "output/readiness/diagnostic/execution",
        time.monotonic() + 15,
    )
    assert process["exit_code"] == 0
    facts = {"original_exit_code": 0, "execution": {"outcomes": [{"stage_key": "copy", "status": "succeeded"}]}}
    error = AuxiliaryPipelineFailure(
        process,
        facts,
        {"logical_plan_artifact": {"path": "output/readiness/diagnostic/plan.json", "sha256": "a" * 64}},
        validation_error="actual logical source differs",
    )
    assert error.code == 1
    observation = error.worker_observation
    assert observation["status"] == "fail"
    assert "actual logical source differs" in observation["diagnostic"]
    assert observation["original_pipeline_failure"]["original_exit_code"] == 0
    assert observation["original_pipeline_failure"]["outcomes"] == facts["execution"]["outcomes"]
    assert observation["original_pipeline_failure"]["logical_plan_artifact"]["path"].endswith("plan.json")


def test_combined_render_failure_logs_retain_exact_bytes_without_following_links(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline_failure import retain_pipeline_failure_logs

    copied = tmp_path / "copied"
    output = copied / "projects/templates/template_code_project/output"
    pdf = output / "pdf"
    pdf.mkdir(parents=True)
    log = pdf / "_combined_manuscript.log"
    log.write_bytes(b"! Actual compiler diagnostic\n")
    external = tmp_path / "outside.tex"
    external.write_bytes(b"must not be disclosed")
    (pdf / "_combined_manuscript.tex").symlink_to(external)
    rows = retain_pipeline_failure_logs(tmp_path, tmp_path / "output/readiness/failed", copied, output)
    assert len(rows) == 2
    assert (tmp_path / rows[0]["artifact"]["path"]).read_bytes() == log.read_bytes()
    assert "artifact" not in rows[1] and rows[1]["diagnostic"]
    assert external.read_bytes() == b"must not be disclosed"
    assert not any(b"must not be disclosed" in p.read_bytes() for p in (tmp_path / "output").rglob("*.*"))


def test_oversized_compiler_diagnostic_cannot_hide_the_original_failure(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline_failure import retain_pipeline_failure_logs

    copied = tmp_path / "copied"
    output = copied / "projects/templates/template_code_project/output"
    pdf = output / "pdf"
    pdf.mkdir(parents=True)
    (pdf / "_combined_manuscript.log").write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    rows = retain_pipeline_failure_logs(tmp_path, tmp_path / "output/readiness/failed", copied, output)
    assert len(rows) == 1 and "read budget" in rows[0]["diagnostic"]
    assert "artifact" not in rows[0]
    assert not (tmp_path / "output").exists()
