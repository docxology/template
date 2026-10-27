"""Actual native controls, exact variants and source/input custody regressions."""

from __future__ import annotations

import hashlib
import platform
import shutil
import sys
import time
import signal
import stat
from io import BytesIO
from pathlib import Path

import pytest
import yaml
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_acceptance_evidence import bootstrap_command, read_json
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
    audit_pdf_raster,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    WORKER_MODULE,
    native_artifact_contract,
    native_environment,
    public_source_digest,
    unsupported_native_controls,
    validate_native_specification,
    create_private_native_directory,
    native_deadline_guard,
    NativeDeadlineExpired,
)
from infrastructure.reporting.native_format_acceptance_validation import _tool
from infrastructure.reporting.native_format_joint_source import JOINT_SCHEMA
from infrastructure.reporting.native_full_worker_pdfium import SCHEMA as PDFIUM_INPUT_SCHEMA
from infrastructure.reporting.native_mermaid_runtime_selection import SELECTION_SCHEMA as MERMAID_SELECTION_SCHEMA
from infrastructure.reporting.native_office_full_worker_context import observe_office_font_nominations
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.native_format_acceptance import (
    _finalize_profile,
    _executed_failure_exit,
    _executed_failure_result,
)
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance

REPO = Path(__file__).absolute().parents[3]
SCOPE = "templates/template_code_project"
pytestmark = pytest.mark.timeout(180)


def _project(root: Path, scope: str = SCOPE, *, slides: bool = False) -> Path:
    project = root / "projects" / scope
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        yaml.safe_dump(
            {"render": {"formats": {"pdf": True, "html": True, "slides": slides}, "slides": {"profile": "accessible"}}}
        )
    )
    (manuscript / "01_intro.md").write_text("# Invented public introduction\n\nActual content.\n")
    (manuscript / "02_methods.md").write_text("# Invented public methods\n\nActual methods.\n")
    return project


def _pdf(text: str) -> bytes:
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(144, 144), invariant=1)
    canvas.drawString(10, 70, text)
    canvas.save()
    return stream.getvalue()


def test_contract_requires_all_sections_and_accessible_pairs(tmp_path: Path) -> None:
    project = _project(tmp_path, slides=True)
    (project / "manuscript/03_skip.md").write_text("<!-- render:skip-beamer -->\n# No presentation\n")
    rows = native_artifact_contract(tmp_path, SCOPE, ("pdf", "html", "slides"), SnapshotReader(tmp_path))
    ids = {row.id for row in rows}
    assert {
        "section:01_intro.md:slides",
        "section:02_methods.md:slides",
        "section:01_intro.md:reveal",
        "section:02_methods.md:reveal",
    } <= ids
    assert "section:03_skip.md:slides" not in ids
    assert "section:03_skip.md:html" in ids
    assert "manuscript:pdf" in ids and "manuscript:html" in ids


def test_pitch_contract_requires_all_three_pdf_pptx_pairs_without_output_discovery(tmp_path: Path) -> None:
    scope = "templates/template_pitch_deck"
    project = _project(tmp_path, scope)
    config = yaml.safe_load((project / "manuscript/config.yaml").read_text())
    config["project_config"] = {"deck": {"formats": ["pdf", "pptx"], "pitch_subject": "template_template"}}
    (project / "manuscript/config.yaml").write_text(yaml.safe_dump(config))
    rows = native_artifact_contract(tmp_path, scope, ("pdf",), SnapshotReader(tmp_path))
    assert {row.id for row in rows if row.id.startswith("pitch:")} == {
        f"pitch:{length}:{kind}" for length in ("short", "medium", "long") for kind in ("pdf", "pptx")
    }
    assert not (project / "output").exists()
    config["project_config"]["deck"]["pitch_subject"] = "../../private"
    (project / "manuscript/config.yaml").write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="unsafe"):
        native_artifact_contract(tmp_path, scope, ("pdf",), SnapshotReader(tmp_path))


def test_source_digest_excludes_outputs_but_binds_authored_directory_changes(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = public_source_digest(tmp_path)
    output = project / "output/pdf/example.pdf"
    output.parent.mkdir(parents=True)
    output.write_bytes(_pdf("first invented result"))
    assert public_source_digest(tmp_path) == before
    (project / "manuscript/01_intro.md").write_text("# Changed actual source\n")
    assert public_source_digest(tmp_path) != before
    renamed = project / "manuscript/renamed.md"
    (project / "manuscript/01_intro.md").rename(renamed)
    assert public_source_digest(tmp_path) != before


def test_inventory_only_native_receipt_cannot_pass(tmp_path: Path) -> None:
    project = _project(tmp_path)
    output = project / "output/pdf/example.pdf"
    output.parent.mkdir(parents=True)
    content = _pdf("Invented existing artifact")
    output.write_bytes(content)
    requirement = Requirement(f"{SCOPE}:formats", "formats", SCOPE, "3.0.0", "4.0.1", "f" * 64, formats=("pdf",))
    details = {
        "execution_exit_code": 0,
        "formats": {
            "pdf": {
                "path": output.relative_to(tmp_path).as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "validated": True,
            }
        },
    }
    # Format acceptance first requires the reader's externally admitted Source
    # and original launch custody; inventory DATA alone is refused before any
    # artifact listing is even considered.
    with pytest.raises(ProjectionSourceUnsupported, match="externally admitted source and original launch custody"):
        validate_acceptance(requirement, {"details": details}, SnapshotReader(tmp_path))


def test_zero_page_and_empty_html_fail_actual_native_parsers() -> None:
    content = BytesIO()
    PdfWriter().write(content)
    with pytest.raises(ValueError, match="no pages"):
        parse_native_bytes("pdf", content.getvalue())
    with pytest.raises(ValueError, match="body content"):
        parse_native_bytes("html", b"<html><body></body></html>")
    observed = parse_native_bytes("pdf", _pdf("Independent actual content"))
    assert observed == {"pages": 1, "page_boxes_pt": [[0.0, 0.0, 144.0, 144.0]]}


def test_visual_oracles_remain_required_after_native_conformance() -> None:
    assert unsupported_native_controls(SCOPE, ("pdf",))[0]["tool"] == "pdf-visual-source-parity"
    assert {row["tool"] for row in unsupported_native_controls("templates/template_pitch_deck", ("pdf", "html"))} == {
        "pdf-visual-source-parity",
        "browser-layout",
        "pitch-native-parity",
    }


def test_actual_nested_control_suite_preserves_module_identity(tmp_path: Path) -> None:
    # The real worker is run as __main__; its nested controls must still launch
    # the canonical importable module rather than __main__ with no spec.
    directory = tmp_path / "output/readiness/controls"
    nonce = "a" * 32
    command = bootstrap_command(
        Path(sys.executable),
        REPO,
        WORKER_MODULE,
        "--root",
        str(tmp_path),
        "--control-suite",
        "--run-id",
        nonce,
        "--control-output",
        str(directory),
    )
    result = run_bounded_subprocess(
        command, cwd=REPO, env=native_environment(REPO, Path(sys.executable), directory), timeout=150
    )
    assert result.returncode == result.original_returncode == 0, (result.command_error, result.stdout, result.stderr)
    raw = read_json(tmp_path, directory / "parser-controls.json")
    assert raw["run_id"] == nonce and len(raw["controls"]) == 6
    for row in raw["controls"]:
        process = read_json(tmp_path, tmp_path / row["process_artifact"]["path"])
        assert process["command"][5] == WORKER_MODULE
        assert process["exit_code"] == process["original_exit_code"] == 1
        assert process["timed_out"] is False


def test_actual_failed_tool_and_wrong_run_cannot_authorize_native_pass(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness/tool"
    # The native supervisor writes only into an existing owned private leaf.
    create_private_native_directory(tmp_path, directory)
    env = native_environment(REPO, Path(sys.executable), directory)
    record = native_tool_record(
        tmp_path,
        directory,
        sys.executable,
        ["-I", "-c", "raise SystemExit(7)"],
        env=env,
        deadline=time.monotonic() + 30,
        run_id="a" * 32,
        purpose="actual-exit-seven",
    )
    assert record["exit_code"] == record["original_exit_code"] == 7
    with pytest.raises(ValueError, match="outcome differs"):
        _tool(
            record["artifact"],
            SnapshotReader(tmp_path),
            "a" * 32,
            sys.executable,
            "actual-exit-seven",
            ["-I", "-c", "raise SystemExit(7)"],
        )
    with pytest.raises(ValueError, match="outcome differs"):
        _tool(
            record["artifact"],
            SnapshotReader(tmp_path),
            "b" * 32,
            sys.executable,
            "actual-exit-seven",
            ["-I", "-c", "raise SystemExit(7)"],
            7,
        )


def test_raster_tools_consume_held_pdf_bytes_after_original_output_changes(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness/raster"
    env = native_environment(REPO, Path(sys.executable), directory)
    missing = [name for name in ("pdftoppm", "pdffonts") if not shutil.which(name, path=env["PATH"])]
    if missing:
        create_private_native_directory(tmp_path, directory)
        with pytest.raises(NativeToolUnavailable):
            native_tool_record(
                tmp_path,
                directory,
                missing[0],
                ["-v"],
                env=env,
                deadline=time.monotonic() + 30,
                run_id="a" * 32,
                purpose="missing-native-tool",
            )
        return
    project = _project(tmp_path)
    path = project / "output/pdf/original.pdf"
    path.parent.mkdir(parents=True)
    original = _pdf("Held admitted invented content")
    path.write_bytes(original)
    snapshot = SnapshotReader(tmp_path).read(path.relative_to(tmp_path).as_posix())
    path.write_bytes(_pdf("Different mutable output"))
    raw = audit_pdf_raster(
        tmp_path,
        directory,
        snapshot,
        parse_native_bytes("pdf", original),
        env=env,
        deadline=time.monotonic() + 60,
        run_id="a" * 32,
        ordinal=0,
    )
    consumed = SnapshotReader(tmp_path).read(raw["input_artifact"]["path"])
    assert consumed.content == original and consumed.sha256 == snapshot.sha256
    assert len(raw["rasters"]) == 1 and raw["rasters"][0]["width_px"] == 300
    for binding in raw["tool_artifacts"]:
        tool = read_json(tmp_path, tmp_path / binding["path"])
        assert str(consumed.path) in tool["command"] and str(path) not in tool["command"]


def _canonical_source_inputs() -> dict[str, object]:
    """Closed joint Source launch DATA labels; validation never admits them."""
    artifact = {"path": "output/readiness/actual/source-descriptor.json", "sha256": "c" * 64}
    return {
        "schema_version": JOINT_SCHEMA,
        "descriptor": artifact,
        "implementation": {**artifact, "path": "output/readiness/actual/implementation-input.json"},
        "providers": {},
        "provider_roots": [],
        "closure": {"directory": "output/readiness/actual/sdk-execution-closure", "identity": [1, 2]},
        "mermaid_runtime": {
            "schema_version": MERMAID_SELECTION_SCHEMA,
            "package_root_path": "/nominated/mermaid/package",
            "dependency_root_path": "/nominated/mermaid/dependencies",
            "node_executable_path": "/nominated/node",
            "chrome_executable_path": "/nominated/chrome",
            "runtime_content_digest": "d" * 64,
        },
        "pdfium": {"schema_version": PDFIUM_INPUT_SCHEMA},
        "office_fonts": observe_office_font_nominations((), deadline=time.monotonic() + 30),
    }


def test_invalid_worker_specification_refuses_scope_and_deadline_before_execution() -> None:
    raw = {
        "scope": SCOPE,
        "run_id": "a" * 32,
        "directory": "output/readiness/actual",
        "formats": ["pdf"],
        "source_digest": "b" * 64,
        "timeout_seconds": 30,
        "deadline_monotonic": 1.0,
        "expected_platform": "Linux",
        "source_inputs": _canonical_source_inputs(),
    }
    validate_native_specification(raw)
    for change in (
        {"scope": "working/private"},
        {"directory": "../private"},
        {"timeout_seconds": float("inf")},
        {"formats": ["pdf", "pdf"]},
        {"expected_platform": "Windows"},
        {"source_inputs": {**raw["source_inputs"], "schema_version": "template-native-source-launch-inputs-v3"}},
    ):
        with pytest.raises(ValueError):
            validate_native_specification({**raw, **change})
    for missing in ("expected_platform", "source_inputs"):
        with pytest.raises(ValueError, match="exact canonical public specification"):
            validate_native_specification({key: value for key, value in raw.items() if key != missing})


def test_actual_source_removal_after_launch_is_executed_failure(tmp_path: Path) -> None:
    from tests.infra_tests.reporting.test_required_readiness import _declarations

    _declarations(tmp_path)
    source = tmp_path / "pyproject.toml"
    before = public_source_digest(tmp_path)
    assert _finalize_profile(tmp_path, before)[0] is True
    # This real child removes a consumed source after admission. It does not
    # replace the producer/runtime/validator or fabricate a process outcome.
    command = [sys.executable, "-I", "-c", "import pathlib,sys;pathlib.Path(sys.argv[1]).unlink()", str(source)]
    result = run_bounded_subprocess(
        command,
        cwd=tmp_path,
        env=native_environment(REPO, Path(sys.executable), tmp_path / "output/readiness/finalization"),
        timeout=30,
    )
    assert result.returncode == result.original_returncode == 0 and not source.exists()
    with pytest.raises(ValueError, match="final source-owned readiness"):
        _finalize_profile(tmp_path, before)
    assert _executed_failure_exit([result.returncode]) == 1
    assert _executed_failure_exit([124, result.returncode]) == 124
    assert _executed_failure_exit([124, 130, result.returncode]) == 130


def test_private_directory_refuses_linked_ancestor_without_external_side_effect(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    parent = root / "output/readiness"
    parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o755)
    mode = stat.S_IMODE(outside.stat().st_mode)
    (parent / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        create_private_native_directory(root, parent / "linked/templates/template_code_project")
    assert stat.S_IMODE(outside.stat().st_mode) == mode and list(outside.iterdir()) == []
    target = parent / "owned/templates/template_code_project"
    create_private_native_directory(root, target)
    assert stat.S_IMODE(target.stat().st_mode) == 0o700
    with pytest.raises(ValueError, match="fresh"):
        create_private_native_directory(root, target)


def test_actual_observer_expiry_escapes_routine_error_capture_and_restores_timer() -> None:
    original = signal.getsignal(signal.SIGALRM)
    previous = signal.getitimer(signal.ITIMER_REAL)
    assert previous == (0.0, 0.0)
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    swallowed = False
    started = time.monotonic()
    try:

        def observer() -> None:
            time.sleep(3)

        with pytest.raises(NativeDeadlineExpired):
            with native_deadline_guard(started + 0.2):
                # Match the producer's ordinary observer-error capture. Its
                # one-shot deadline must escape and stop all later gates.
                try:
                    observer()
                except OSError, ValueError, TypeError, KeyError:
                    swallowed = True
        assert not swallowed and time.monotonic() - started < 2
        assert signal.getsignal(signal.SIGALRM) == signal.SIG_IGN
        assert signal.getitimer(signal.ITIMER_REAL) == previous
    finally:
        signal.signal(signal.SIGALRM, original)
        signal.setitimer(signal.ITIMER_REAL, *previous)


def test_actual_cli_oversized_timer_refuses_before_admission(tmp_path: Path) -> None:
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    with pytest.raises(ValueError, match="cannot be represented"):
        with native_deadline_guard(time.monotonic() + 1e100):
            pytest.fail("unrepresentable timer must refuse before native admission")
    assert signal.getsignal(signal.SIGALRM) == previous_handler
    assert signal.getitimer(signal.ITIMER_REAL) == previous_timer
    # Every required Source/SDK/runtime nomination is supplied, so only the
    # unrepresentable timer can refuse. Nominations are never admitted first.
    nominations = tmp_path / "nominations"
    nominations.mkdir()
    implementation = nominations / "implementation-input.json"
    implementation.write_bytes(b'{"binding_kind": "nominated-only"}\n')
    command = bootstrap_command(
        Path(sys.executable),
        REPO,
        "infrastructure.reporting.native_format_acceptance",
        "--repo-root",
        str(tmp_path),
        "--project",
        SCOPE,
        "--timeout",
        str(10**100),
        "--current-analysis-root",
        str(nominations / "current"),
        "--expected-platform",
        platform.system(),
        "--sdk-package-root",
        str(nominations / "sdk"),
        "--implementation-input",
        str(implementation),
        "--implementation-sha256",
        hashlib.sha256(implementation.read_bytes()).hexdigest(),
        "--mermaid-package-root",
        str(nominations / "mermaid"),
        "--mermaid-dependency-root",
        str(nominations / "mermaid-dependencies"),
        "--mermaid-node-executable",
        str(nominations / "node"),
        "--mermaid-chrome-executable",
        str(nominations / "chrome"),
        "--pdfium-site",
        str(nominations / "pdfium-site"),
        "--pdfium-wheel",
        str(nominations / "pdfium.whl"),
    )
    result = run_bounded_subprocess(
        command,
        cwd=REPO,
        env=native_environment(REPO, Path(sys.executable), tmp_path / "output/readiness/oversized"),
        timeout=30,
    )
    assert result.returncode == result.original_returncode == 2
    assert "cannot be represented" in result.stderr and "Traceback" not in result.stderr
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("exit_code", [7, 130])
def test_actual_child_outcome_survives_confined_persistence_refusal(tmp_path: Path, exit_code: int) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    command = [sys.executable, "-I", "-c", f"raise SystemExit({exit_code})"]
    result = run_bounded_subprocess(
        command,
        cwd=root,
        env=native_environment(REPO, Path(sys.executable), root / "output/readiness/attempt"),
        timeout=30,
    )
    assert result.returncode == result.original_returncode == exit_code
    outside = tmp_path / "outside"
    outside.mkdir()
    parent = root / "output/readiness"
    parent.mkdir(parents=True)
    (parent / "refused").symlink_to(outside, target_is_directory=True)
    observed = {
        "exit_code": result.returncode,
        "original_exit_code": result.original_returncode,
        "timed_out": result.timed_out,
        "command": command,
    }
    state = {
        "root": root,
        "directory": parent / "refused",
        "run_id": "a" * 32,
        "before": "b" * 64,
        "fingerprint": "c" * 64,
        "platform_version": "4.0.1",
        "selected": (SCOPE,),
        "deadline": time.monotonic() + 30,
        "admitted": [{"scope": SCOPE, "observation": observed, "process": None, "raw_binding": None}],
    }
    failure = _executed_failure_result(state, ValueError("actual post-launch evidence custody refusal"))
    assert failure["exit_code"] == (130 if exit_code == 130 else 1) and failure["receipt"] is None
    assert failure["native_formats"]["results"][0]["observation"] == observed
    assert list(outside.iterdir()) == []
    state["deadline"] = time.monotonic() - 1
    expired = _executed_failure_result(state, ValueError("post-launch finalization failed"))
    assert expired["exit_code"] == (130 if exit_code == 130 else 124)
