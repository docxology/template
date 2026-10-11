"""Real child-process and production-checker controls for auxiliary evidence."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

from infrastructure.project.public_acceptance_auxiliary import supervise
from infrastructure.project.public_acceptance_auxiliary_worker import negative_control


def test_supervision_preserves_original_failure_and_bound_streams(tmp_path: Path) -> None:
    process = supervise(
        [sys.executable, "-I", "-c", "print('actual child'); raise SystemExit(17)"],
        tmp_path,
        tmp_path / "output/readiness/failure",
        time.monotonic() + 10,
    )
    assert process["exit_code"] == 17
    assert process["timed_out"] is False
    stdout = tmp_path / process["streams"]["stdout"]["path"]
    assert stdout.read_text() == "actual child\n"


def test_supervision_kills_actual_timeout(tmp_path: Path) -> None:
    process = supervise(
        [sys.executable, "-I", "-c", "import time; time.sleep(30)"],
        tmp_path,
        tmp_path / "output/readiness/timeout",
        time.monotonic() + 0.2,
    )
    assert process["timed_out"] is True
    assert process["exit_code"] < 0
    assert process["duration_seconds"] < 5


def test_supervision_refuses_evidence_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="canonical path"):
        supervise([sys.executable, "-c", "pass"], tmp_path, tmp_path / "outside", time.monotonic() + 5)


@pytest.mark.parametrize("gate", ["root:docs_lint", "root:methods", "root:macos:process"])
def test_negative_controls_execute_real_production_paths(gate: str) -> None:
    assert negative_control(Path.cwd(), gate) == 23


@pytest.mark.parametrize(
    "gate",
    [
        "templates/template_formal:live:network-faults",
        "templates/template_pools_rules_tools:live:bundled-resource-execution",
        "templates/template_code_project:live:local-review",
        "templates/template_pitch_deck:live:pdf-pptx",
    ],
)
def test_specialized_negative_controls_execute_actual_checkers(gate: str) -> None:
    assert negative_control(Path.cwd(), gate) == 23


def test_unselected_model_and_docker_image_are_blocked_without_acquisition(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_native import native_execution
    from infrastructure.project.public_acceptance_auxiliary_worker import MissingAuxiliaryProvider

    for gate in (
        "templates/template_sia:live:docker-sandbox",
        "templates/template_code_project:live:local-review",
    ):
        with pytest.raises(MissingAuxiliaryProvider, match="explicitly selected"):
            native_execution(Path.cwd(), gate, 30, tmp_path, {})


@pytest.mark.timeout(420)
def test_real_process_readback_after_producer_root_and_wrapper_deleted(tmp_path: Path) -> None:
    import json
    import os
    import platform
    import shutil
    import subprocess

    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.reporting.readiness_receipts import source_fingerprint

    source = Path.cwd()
    producer = tmp_path / "producer"
    producer.mkdir()
    shutil.copytree(
        source / "infrastructure", producer / "infrastructure", ignore=shutil.ignore_patterns("__pycache__")
    )
    for kind in ("storybook", "newspaper"):
        original = source / f"projects/templates/template_{kind}"
        destination = producer / f"projects/templates/template_{kind}"
        for part in ("src", "content"):
            shutil.copytree(original / part, destination / part, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(original / "pyproject.toml", destination / "pyproject.toml")
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(source / name, producer / name)
    prepared = Path(sys.prefix).resolve()
    environment = producer / ".venv"
    (environment / "bin").mkdir(parents=True)
    interpreter = environment / "bin/python"
    interpreter.symlink_to(Path(sys.executable))
    shutil.copyfile(prepared / "pyvenv.cfg", environment / "pyvenv.cfg")
    library = environment / f"lib/python{sys.version_info.major}.{sys.version_info.minor}"
    library.mkdir(parents=True)
    # Complete genuine installed RECORD files need regular held directories.
    # Hard links retain exact prepared bytes without another environment install
    # or copying its large data allocation; the producer never writes them.
    shutil.copytree(
        prepared / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages",
        library / "site-packages",
        copy_function=os.link,
    )
    shutil.copytree(prepared / "share", environment / "share", copy_function=os.link)
    for entrypoint in (prepared / "bin").iterdir():
        if entrypoint.is_file() and not entrypoint.is_symlink() and entrypoint.name != "python":
            os.link(entrypoint, environment / "bin" / entrypoint.name)
    directory = producer / "output/readiness/portable"
    gate = "root:roster"
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    # This control claims complete source-roster metadata and process
    # portability, not execution of each exemplar's algorithms.
    for scope in PUBLIC_PROJECT_NAMES:
        project = producer / "projects" / scope
        (project / "src").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "projects" / scope / "pyproject.toml", project / "pyproject.toml")
    refused_directory = producer / "output/readiness/unsupported-print"
    refused_spec = write_json(
        producer,
        refused_directory / "spec.json",
        {"gate": "root:macos:rendering", "budget": 180, "raw_path": "output/readiness/unsupported-print/raw.json"},
    )
    refused_command = [
        str(interpreter),
        "-m",
        "infrastructure.project.public_acceptance_auxiliary_worker",
        "--spec",
        str(producer / refused_spec["path"]),
    ]
    refused = supervise(refused_command, producer, refused_directory / "execution", time.monotonic() + 180)
    actual_refusal = json.loads((refused_directory / "raw.json").read_text())
    assert refused["timed_out"] is False
    assert not actual_refusal.get("details", {}).get("print_witness_artifact")
    darwin_tools = all(shutil.which(name) for name in ("pandoc", "pdftoppm", "pdffonts"))
    if platform.system() == "Darwin" and darwin_tools:
        # A standalone Darwin print witness runs its tools, but every native tool
        # record needs externally admitted source and original launch custody.
        # Without that authority the witness fails closed and grants nothing.
        refusal_code, refusal_status = 1, "fail"
        assert actual_refusal["failure_class"] == "ProjectionSourceUnsupported"
        assert "externally admitted source and original launch custody" in actual_refusal["diagnostic"]
    else:
        refusal_code, refusal_status = 75, "blocked"
        assert ("actual Darwin host" if platform.system() != "Darwin" else "unavailable") in actual_refusal[
            "diagnostic"
        ]
        assert not list(refused_directory.rglob("print-witness.json"))
    assert refused["exit_code"] == actual_refusal["exit_code"] == refusal_code
    assert actual_refusal["status"] == refusal_status
    fingerprint = source_fingerprint(producer)
    spec = write_json(
        producer,
        directory / "spec.json",
        {"gate": gate, "budget": 180, "raw_path": "output/readiness/portable/raw.json"},
    )
    command = [
        str(interpreter),
        "-m",
        "infrastructure.project.public_acceptance_auxiliary_worker",
        "--spec",
        str(producer / spec["path"]),
    ]
    process = supervise(command, producer, directory / "execution", time.monotonic() + 180)
    assert process["exit_code"] == 0, (directory / "raw.json").read_text()
    raw_binding = {
        "path": "output/readiness/portable/raw.json",
        "sha256": __import__("hashlib").sha256((directory / "raw.json").read_bytes()).hexdigest(),
    }
    raw = json.loads((directory / "raw.json").read_text())
    assert source_fingerprint(producer) == fingerprint
    process.update(
        gate=gate,
        source_fingerprint=fingerprint,
        source_before=fingerprint,
        source_after=fingerprint,
        spec_artifact=spec,
        raw_artifact=raw_binding,
    )
    binding = write_json(producer, directory / "process.json", process)
    details = {
        **raw["details"],
        "command": command,
        "execution_exit_code": 0,
        "process_artifact": binding,
        "raw_artifact": raw_binding,
    }
    write_json(producer, directory / "details.json", details)
    reader_root = tmp_path / "reader"
    shutil.copytree(producer, reader_root, ignore=shutil.ignore_patterns(".venv"))
    shutil.rmtree(producer)
    assert not interpreter.exists()
    assert source_fingerprint(reader_root) == fingerprint
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    # Retain the actual already-prepared interpreter distribution at a
    # distinct reader location; preserve its ABI without another install.
    prefix = Path(sys.base_prefix).resolve()
    binary = Path(sys.executable).resolve()
    assert binary.is_relative_to(prefix)
    members = list(prefix.rglob("*"))
    assert len(members) <= 100_000
    assert sum(item.lstat().st_size for item in members if item.is_file() and not item.is_symlink()) <= 2 * 1024**3
    reader_runtime = tmp_path / "reader-python"
    # A fresh reader must not add links to the shared interpreter distribution.
    # Retain exact ABI bytes in independent files and keep its original metadata.
    metadata_fields = ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")
    originals = {
        item.relative_to(prefix): tuple(getattr(item.stat(), field) for field in metadata_fields)
        for item in members
        if item.is_file() and not item.is_symlink()
    }
    shutil.copytree(prefix, reader_runtime, copy_function=shutil.copy2, symlinks=True)
    for relative, expected in originals.items():
        original = prefix / relative
        copied = reader_runtime / relative
        assert tuple(getattr(original.stat(), field) for field in metadata_fields) == expected
        assert (copied.stat().st_dev, copied.stat().st_ino) != (expected[0], expected[1])
        assert copied.stat().st_nlink == 1
    alternate = reader_runtime / binary.relative_to(prefix)
    assert alternate.is_file() and alternate.resolve() != Path(sys.executable).resolve()
    script = r"""
import sys,json,pathlib
sys.path[:0]=sys.argv[1:3]
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.project.public_acceptance_auxiliary_validation import validate_auxiliary_process
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import source_fingerprint
root=pathlib.Path(sys.argv[1])
details=json.loads((root/'output/readiness/portable/details.json').read_text())
gate,refusal_code,refusal_status=sys.argv[4],int(sys.argv[5]),sys.argv[6]
assert source_fingerprint(root)==sys.argv[3]
validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
observations=details['source_roster_observations']
assert details['projects']==list(PUBLIC_PROJECT_NAMES)
assert [item['scope'] for item in observations]==list(PUBLIC_PROJECT_NAMES)
metadata=root/observations[0]['metadata_artifact']['path'];original_metadata=metadata.read_bytes()
metadata.write_bytes(original_metadata+b'\n# changed after actual roster producer\n')
try:validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
except ValueError:pass
else:raise AssertionError('changed current roster metadata admitted')
finally:metadata.write_bytes(original_metadata)
sdk=root/'infrastructure/core/execution_boundary.py';original_sdk=sdk.read_bytes()
sdk.write_bytes(original_sdk+b'\n# changed current source after portable producer\n')
current=source_fingerprint(root);assert current!=sys.argv[3]
try:
    validate_auxiliary_process(gate,current,details,SnapshotReader(root))
except ValueError:pass
else:raise AssertionError('changed current SDK source fingerprint admitted')
finally:sdk.write_bytes(original_sdk)
assert source_fingerprint(root)==sys.argv[3]
validate_auxiliary_process(gate,sys.argv[3],details,SnapshotReader(root))
refusal=json.loads((root/'output/readiness/unsupported-print/raw.json').read_text())
assert refusal['exit_code']==refusal_code and refusal['status']==refusal_status
assert not refusal.get('details',{}).get('print_witness_artifact')
print(json.dumps({'role':'actual-portable-roster-controls','projects':len(observations),
                  'unsupported_print_original_exit':refusal_code,'source_and_metadata_controls':2}))
"""
    result = subprocess.run(
        [
            str(alternate),
            "-I",
            "-c",
            script,
            str(reader_root),
            str(prepared / f"lib/python{minor}/site-packages"),
            fingerprint,
            gate,
            str(refusal_code),
            refusal_status,
        ],
        cwd=reader_root,
        capture_output=True,
        text=True,
        timeout=180,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    (tmp_path / "portable-observation.json").write_text(result.stdout)


def test_mandatory_raw_custody_rejects_bare_success_flags(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_validation import (
        validate_auxiliary_process,
        validate_sandbox_transfer,
    )
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    with pytest.raises(ValueError, match="exact artifact binding"):
        validate_auxiliary_process("root:docs_lint", "a" * 64, {"execution_exit_code": 0}, SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="exact artifact bindings"):
        validate_sandbox_transfer({"destination_kind": "sandbox", "remote_verified": True}, SnapshotReader(tmp_path))


def test_transfer_rejects_unscoped_identity_before_export_or_remote_io(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary import run_sandbox_transfer

    with pytest.raises(ValueError, match="exact repository"):
        run_sandbox_transfer(
            tmp_path,
            export_receipt=tmp_path / "missing.json",
            upload_outputs=tmp_path / "missing-outputs.json",
            downloaded_directory=tmp_path / "output/readiness/download",
            repository="unselected",
            run_id="0",
            source_commit="branch-name",
            evidence_dir=tmp_path / "output/readiness/transfer",
        )
    assert not (tmp_path / "output").exists()


def test_roster_executes_actual_source_admission_and_rejects_missing_roots(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_worker import execute

    with pytest.raises(ValueError, match="canonical public source root"):
        execute(tmp_path, "root:roster", 10)


@pytest.mark.parametrize(
    "name",
    [
        "template_textbook",
        "template_code_project",
        "template_gold_refinement",
        "template_registered_report",
        "template_template",
        "template_sia",
        "template_experiment_tree",
        "template_madlib",
        "template_prose_project",
        "template_search_project",
        "template_literature_meta_analysis",
        "template_advanced_literature_review",
        "template_autoresearch_project",
    ],
)
def test_actual_deterministic_domains_reject_corrupt_measurements(name: str) -> None:
    import copy
    import tempfile

    from infrastructure.project.public_acceptance_auxiliary_domains import (
        domain_negative,
        execute_domain,
        validate_domain,
    )
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    root = Path.cwd()
    base = root / "output/readiness"
    base.mkdir(parents=True, exist_ok=True)
    scope = f"templates/{name}"
    with tempfile.TemporaryDirectory(prefix="domain-control-", dir=base) as temporary:
        result = execute_domain(root, scope, Path(temporary), 120)
        assert result is not None
        validate_domain(result, SnapshotReader(root))
        assert domain_negative(root, scope) == 23
        corrupt = copy.deepcopy(result)
        measured = corrupt["measurements"]
        if name == "template_textbook":
            measured["logistic_growth"]["N"][0] += 1
        elif name == "template_code_project":
            next(iter(measured["runs"].values()))["objective_value"] += 1
        elif name == "template_gold_refinement":
            measured["purities"][-1] = -1
        elif name == "template_registered_report":
            measured["frozen"]["registration_hash"] = "0" * 64
        elif name == "template_template":
            measured["receipt"]["public_exemplar_count"] = 0
        elif name == "template_sia":
            measured["score"] = 0
        elif name == "template_experiment_tree":
            measured["summary"]["total_nodes"] = 0
        elif name == "template_madlib":
            measured["field_counts"] = {}
        elif name == "template_prose_project":
            measured["total_words"] = 0
        elif name == "template_search_project":
            measured["invariants"][0]["actual"] += 1
        elif name == "template_literature_meta_analysis":
            measured["statistics"]["total"] = 0
        elif name == "template_advanced_literature_review":
            measured["phase_corpora"]["combined_corpus.jsonl"] = []
        elif name == "template_autoresearch_project":
            measured["result"]["baseline"]["test_accuracy"] = 0
        with pytest.raises(ValueError):
            validate_domain(corrupt, SnapshotReader(root))


def test_portable_pipeline_rejects_bare_success_before_compilation(tmp_path: Path) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline import SCHEMA, validate_portable_pipeline
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    with pytest.raises(ValueError, match="original artifact binding"):
        validate_portable_pipeline(
            "templates/template_madlib", {"pipeline_schema": SCHEMA, "mode": "core"}, SnapshotReader(tmp_path)
        )
    assert negative_control(Path.cwd(), "templates/template_madlib:pipeline") == 23


def test_explicit_supervision_rejects_protected_environment_names_before_reading_values(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="protected credential names"):
        supervise(
            [sys.executable, "-c", "raise SystemExit(0)"],
            tmp_path,
            tmp_path / "output/readiness/forbidden",
            time.monotonic() + 5,
            environment={"EXAMPLE_API_KEY": "invalid-control"},
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("budget", [600, 600.0])
def test_portable_logical_plan_preserves_original_budget_serialization(budget: float) -> None:
    from infrastructure.project.public_acceptance_auxiliary_pipeline import _read_logical_plan

    root = Path(__file__).resolve().parents[3]
    plan = _read_logical_plan(root, "templates/template_madlib", budget, "1760000000")["plan"]
    assert type(plan["run_timeout_seconds"]) is type(budget)
    assert plan["run_timeout_seconds"] == budget


@pytest.mark.skipif(sys.platform != "darwin", reason="actual Darwin print worker control")
@pytest.mark.parametrize("control", ["missing-tools", "caller-timer", "deadline"])
def test_print_worker_retains_real_preflight_and_guard_failures(tmp_path: Path, control: str) -> None:
    import json
    import subprocess
    import uuid

    from infrastructure.project.public_acceptance_evidence import write_json

    root = Path.cwd()
    directory = root / "output/readiness" / ("worker-failure-" + uuid.uuid4().hex + "-" + control)
    spec = write_json(
        root,
        directory / "spec.json",
        {
            "gate": "root:macos:rendering",
            "budget": 1 if control == "deadline" else 30,
            "raw_path": (directory / "raw.json").relative_to(root).as_posix(),
        },
    )
    script = (
        "import pathlib,signal,sys; "
        + ("signal.setitimer(signal.ITIMER_REAL,60); " if control == "caller-timer" else "")
        + "from infrastructure.project.public_acceptance_auxiliary_worker import main; "
        + "sys.argv=['worker','--spec',sys.argv[1]]; raise SystemExit(main())"
    )
    from infrastructure.core.execution_boundary import build_bounded_env

    env = build_bounded_env()
    if control == "missing-tools":
        env["PATH"] = str(tmp_path / "empty-path")
    result = subprocess.run(
        [sys.executable, "-c", script, str(root / spec["path"])],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    raw = json.loads((directory / "raw.json").read_text())
    if control == "missing-tools":
        assert result.returncode == raw["exit_code"] == 75
        assert raw["status"] == "blocked"
        assert "unavailable" in raw["diagnostic"]
    else:
        assert result.returncode == raw["exit_code"] == (124 if control == "deadline" else 1), result.stderr
        assert raw["status"] == ("timeout" if control == "deadline" else "fail")
        expected = "NativeDeadlineExpired" if control == "deadline" else "NativeDeadlineUnavailable"
        assert raw["failure_class"] == expected
        assert "deadline" in raw["diagnostic"] or "timer" in raw["diagnostic"]
