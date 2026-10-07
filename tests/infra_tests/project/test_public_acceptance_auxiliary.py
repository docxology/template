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


def test_real_process_readback_after_producer_root_and_wrapper_deleted(tmp_path: Path) -> None:
    import json
    import os
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
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(source / name, producer / name)
    environment = producer / ".venv"
    (environment / "bin").mkdir(parents=True)
    interpreter = environment / "bin/python"
    interpreter.symlink_to(Path(sys.executable))
    shutil.copyfile(source / ".venv/pyvenv.cfg", environment / "pyvenv.cfg")
    library = environment / f"lib/python{sys.version_info.major}.{sys.version_info.minor}"
    library.mkdir(parents=True)
    (library / "site-packages").symlink_to(
        source / f".venv/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    directory = producer / "output/readiness/portable"
    gate = "root:macos:rendering"
    spec = write_json(
        producer,
        directory / "spec.json",
        {"gate": gate, "budget": 30, "raw_path": "output/readiness/portable/raw.json"},
    )
    command = [
        str(interpreter),
        "-m",
        "infrastructure.project.public_acceptance_auxiliary_worker",
        "--spec",
        str(producer / spec["path"]),
    ]
    process = supervise(command, producer, directory / "execution", time.monotonic() + 30)
    assert process["exit_code"] == 0
    raw_binding = {
        "path": "output/readiness/portable/raw.json",
        "sha256": __import__("hashlib").sha256((directory / "raw.json").read_bytes()).hexdigest(),
    }
    raw = json.loads((directory / "raw.json").read_text())
    fingerprint = source_fingerprint(source)
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
    alternate = Path("/opt/homebrew/bin/python3.14")
    assert alternate.is_file() and alternate.resolve() != Path(sys.executable).resolve()
    script = (
        "import sys,json,pathlib; sys.path[:0]=sys.argv[1:3]; "
        "from infrastructure.reporting.release_readiness_snapshot import SnapshotReader; "
        "from infrastructure.project.public_acceptance_auxiliary_validation import validate_auxiliary_process; "
        "root=pathlib.Path(sys.argv[1]); details=json.loads((root/'output/readiness/portable/details.json').read_text()); "
        "validate_auxiliary_process('root:macos:rendering',sys.argv[3],details,SnapshotReader(root))"
    )
    result = subprocess.run(
        [
            str(alternate),
            "-I",
            "-c",
            script,
            str(reader_root),
            str(library.resolve() if library.exists() else source / ".venv/lib/python3.14/site-packages"),
            fingerprint,
        ],
        cwd=reader_root,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPYCACHEPREFIX": str(tmp_path / "reader-cache")},
    )
    assert result.returncode == 0, result.stderr


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
