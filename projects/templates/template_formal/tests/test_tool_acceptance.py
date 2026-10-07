"""Actual pinned formal tools and real descendant deadline controls."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

from template_formal._tool_execution import build_bounded_env, run_bounded_subprocess
from template_formal.tool_acceptance import (
    TLC_SHA256,
    _acquire_jar,
    _jar_snapshot,
    _run,
    _selected_jar,
    _sources,
    main,
    run_formal_tools,
)

PROJECT = Path(__file__).resolve().parents[1]


def _process_running(pid: int) -> bool:
    """True while ``pid`` exists and is not a terminated, unreaped zombie.

    Containers whose PID 1 does not reap orphans keep killed descendants as
    zombies; a zombie executes nothing, so it is not a surviving descendant.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            return stat.read_text().rsplit(")", 1)[1].split()[0] != "Z"
        except (OSError, IndexError):
            return True
    return True


def _copy(root: Path) -> Path:
    """Copy the exact declared specs and admitted jar into a disposable project."""
    shutil.copytree(PROJECT / "formal", root / "formal", ignore=shutil.ignore_patterns(".lake", "states", "*TTrace*"))
    jar = root / "formal/tla/tla2tools.jar"
    if not jar.exists() and (provider := os.environ.get("TEMPLATE_FORMAL_TLC_JAR")):
        content = _jar_snapshot(Path(provider))
        assert hashlib.sha256(content).hexdigest() == TLC_SHA256
        jar.write_bytes(content)
    return root


@pytest.mark.timeout(360)
def test_actual_tools_check_all_models_and_expected_invariant_violation(tmp_path: Path) -> None:
    receipt = run_formal_tools(_copy(tmp_path), timeout=300)
    assert receipt["status"] == "passed", receipt
    assert receipt["source_unchanged"] is True
    checks = {check["name"]: check for check in receipt["checks"]}
    assert checks["lean-build"]["exit_code"] == 0
    assert checks["tlc-AntProtocol"]["exit_code"] == 0
    assert checks["tlc-AntProtocolFaulty"]["exit_code"] == 0
    negative = checks["tlc-AntProtocolFaultyNegControl"]
    assert negative["exit_code"] == 12
    assert all(
        check["consumed_tlc_sha256"] == TLC_SHA256
        for name, check in checks.items()
        if name.startswith("tlc-AntProtocol")
    )
    assert "Invariant NoFalseEstablishment is violated" in negative["stdout"]
    assert not list((tmp_path / "formal" / "tla").glob("*TTrace*"))


@pytest.mark.timeout(360)
def test_mutating_cached_jar_cannot_change_frozen_model_execution(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    jar = root / "formal/tla/tla2tools.jar"
    project_id = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:12]
    changed = threading.Event()
    stopped = threading.Event()

    def corrupt_after_snapshot() -> None:
        while not stopped.wait(0.01):
            if any(
                (directory / "tla2tools.jar").is_file()
                for directory in Path(tempfile.gettempdir()).glob(f"template-tlc-verified-{project_id}-*")
            ):
                jar.write_bytes(b"concurrent cache mutation")
                changed.set()
                return

    observer = threading.Thread(target=corrupt_after_snapshot)
    observer.start()
    try:
        receipt = run_formal_tools(root, timeout=300)
    finally:
        stopped.set()
        observer.join(timeout=5)
    assert not observer.is_alive() and changed.is_set(), receipt
    models = [check for check in receipt["checks"] if check["name"].startswith("tlc-AntProtocol")]
    assert len(models) == 3 and all(check["status"] == "passed" for check in models), receipt
    assert all(check["consumed_tlc_sha256"] == TLC_SHA256 for check in models)
    assert receipt["status"] == "failed" and receipt["source_unchanged"] is False


def test_jar_snapshot_refuses_nonregular_and_linked_cache(tmp_path: Path) -> None:
    (tmp_path / "directory.jar").mkdir()
    with pytest.raises((OSError, ValueError)):
        _jar_snapshot(tmp_path / "directory.jar")
    fifo = tmp_path / "fifo.jar"
    os.mkfifo(fifo)
    with pytest.raises(ValueError, match="regular"):
        _jar_snapshot(fifo)
    regular = tmp_path / "regular.jar"
    regular.write_bytes(b"regular admitted input")
    link = tmp_path / "linked.jar"
    link.symlink_to(regular)
    with pytest.raises(ValueError, match="regular"):
        _jar_snapshot(link)
    assert _jar_snapshot(regular) == regular.read_bytes()


@pytest.mark.timeout(360)
def test_removed_invariant_cannot_make_proof_of_detection_pass(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    config = root / "formal" / "tla" / "AntProtocolFaultyNegControl.cfg"
    content = config.read_text()
    assert "  NoFalseEstablishment\n" in content
    config.write_text(content.replace("  NoFalseEstablishment\n", ""))
    receipt = run_formal_tools(root, timeout=300)
    checks = {check["name"]: check for check in receipt["checks"]}
    assert checks["tlc-AntProtocolFaultyNegControl"]["status"] == "failed", receipt
    assert checks["tlc-AntProtocolFaultyNegControl"]["exit_code"] == 0
    assert receipt["status"] == "failed"


def test_missing_tool_and_corrupt_cache_are_distinct_blocked_and_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    monkeypatch.delenv("FORMAL_JAVA_BIN", raising=False)
    receipt = run_formal_tools(root, timeout=2)
    assert receipt["status"] == "blocked"
    (root / "formal" / "tla" / "tla2tools.jar").write_bytes(b"untrusted jar")
    receipt = run_formal_tools(root, timeout=2)
    assert receipt["status"] == "failed"


def test_real_timeout_kills_detached_descendant(tmp_path: Path) -> None:
    pid_file = tmp_path / "descendant.json"
    program = (
        "import subprocess,sys,time,json; from pathlib import Path; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True); "
        "Path(sys.argv[1]).write_text(json.dumps(p.pid)); time.sleep(60)"
    )
    result = run_bounded_subprocess(
        [sys.executable, "-c", program, str(pid_file)], cwd=tmp_path, env=build_bounded_env(), timeout=1
    )
    assert result.returncode == 124 and result.timed_out
    pid = json.loads(pid_file.read_text())
    for _ in range(20):
        if not _process_running(pid):
            break
        time.sleep(0.05)
    else:
        pytest.fail(f"timed-out detached descendant{pid} survived")


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), 601, True])
def test_invalid_deadline_cannot_launch_tools(tmp_path: Path, timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout"):
        run_formal_tools(tmp_path, timeout=timeout)


@pytest.mark.parametrize("mutation", ["toolchain", "packages", "name", "missing", "symlink"])
def test_invalid_pin_and_source_custody_refuse_before_execution(tmp_path: Path, mutation: str) -> None:
    root = _copy(tmp_path)
    lean = root / "formal/lean"
    if mutation == "toolchain":
        (lean / "lean-toolchain").write_text("leanprover/lean4:v4.27.0\n")
    elif mutation == "missing":
        (lean / "lake-manifest.json").unlink()
    elif mutation == "symlink":
        (lean / "injected.lean").symlink_to(lean / "AntProtocol.lean")
    else:
        manifest = json.loads((lean / "lake-manifest.json").read_text())
        manifest[mutation] = ["unlocked"] if mutation == "packages" else "different"
        (lean / "lake-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises((ValueError, FileNotFoundError)):
        run_formal_tools(root, timeout=2)


def test_named_states_and_extra_jar_are_bound_source_inputs(tmp_path: Path) -> None:
    (tmp_path / "states").mkdir()
    state = tmp_path / "states/model.py"
    state.write_text("state = 1\n")
    archive = tmp_path / "declared.jar"
    archive.write_bytes(b"declared source input")
    before = _sources(tmp_path)
    assert set(before) == {"states/model.py", "declared.jar"}
    state.write_text("state = 2\n")
    assert before != _sources(tmp_path)
    archive.write_bytes(b"changed source input")
    assert before["declared.jar"] != _sources(tmp_path)["declared.jar"]


@pytest.mark.parametrize("relative", ["formal/lean/Declared.lean", "formal/tla/Declared.cfg"])
def test_declared_fifo_is_refused_before_any_tool_launch(tmp_path: Path, relative: str) -> None:
    root = _copy(tmp_path / "project")
    fifo = root / relative
    os.mkfifo(fifo)
    start = time.monotonic()
    with pytest.raises(ValueError, match="regular"):
        run_formal_tools(root, timeout=2)
    assert time.monotonic() - start < 2
    assert not (root / "formal/lean/.lake").exists()


def test_source_snapshot_bounds_regular_bytes_and_inventory(tmp_path: Path) -> None:
    from template_formal._tool_sources import snapshot_tree

    (tmp_path / "input.lean").write_bytes(b"12345")
    with pytest.raises(ValueError, match="regular"):
        snapshot_tree(tmp_path, deadline=time.monotonic() + 2, exclude=lambda _: False, max_file_bytes=4)
    with pytest.raises(ValueError, match="entry"):
        snapshot_tree(tmp_path, deadline=time.monotonic() + 2, exclude=lambda _: False, max_entries=0)
    with pytest.raises(TimeoutError, match="deadline"):
        snapshot_tree(tmp_path, deadline=time.monotonic() - 1, exclude=lambda _: False)
    with pytest.raises(ValueError, match="total byte"):
        snapshot_tree(tmp_path, deadline=time.monotonic() + 2, exclude=lambda _: False, max_total_bytes=4)
    nested = tmp_path / "nested/second/input.lean"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"declared model")
    with pytest.raises(ValueError, match="depth"):
        snapshot_tree(tmp_path, deadline=time.monotonic() + 2, exclude=lambda _: False, max_depth=1)


def test_held_source_ancestor_refuses_real_directory_rebinding(tmp_path: Path) -> None:
    from template_formal._tool_sources import _open_ancestors, _verify_chain, snapshot_file

    root = tmp_path / "project"
    root.mkdir()
    (root / "Input.lean").write_bytes(b"admitted initial model")
    held = _open_ancestors(root, time.monotonic() + 2)
    try:
        root.rename(tmp_path / "previous-project")
        root.mkdir()
        (root / "Input.lean").write_bytes(b"different rebound model")
        with pytest.raises(ValueError, match="ancestor changed"):
            _verify_chain(held)
        assert snapshot_file(root / "Input.lean", deadline=time.monotonic() + 2) == b"different rebound model"
    finally:
        for descriptor, _, _ in reversed(held):
            os.close(descriptor)


@pytest.mark.timeout(360)
def test_actual_lean_and_tlc_consume_frozen_sources_despite_original_input_aba(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy(tmp_path / "project")
    lean_source = root / "formal/lean/AntProtocol.lean"
    tla_config = root / "formal/tla/AntProtocolFaultyNegControl.cfg"
    lean_bytes, tla_bytes = lean_source.read_bytes(), tla_config.read_bytes()
    real_elan, real_java = shutil.which("elan"), shutil.which(os.environ.get("FORMAL_JAVA_BIN", "java"))
    assert real_elan and real_java, "pinned actual Lean and Java are required for this acceptance"
    shims = tmp_path / "actual-tool-adapters"
    shims.mkdir()
    observations = tmp_path / "consumed-inputs.jsonl"
    for name, executable, source, match, changed in (
        ("elan", real_elan, lean_source, "AntProtocol.lean", lean_bytes + b'\n#eval "INPUT_ABA_ACCEPTED"\n'),
        (
            "java",
            real_java,
            tla_config,
            "AntProtocolFaultyNegControl.cfg",
            tla_bytes.replace(b"  NoFalseEstablishment\n", b""),
        ),
    ):
        adapter = shims / name
        adapter.write_text(
            f"#!{sys.executable}\nimport hashlib,json,subprocess,sys\nfrom pathlib import Path\n"
            f"source=Path({str(source)!r}); original=source.read_bytes(); changed={changed!r}\n"
            f"active={match!r} in sys.argv; observed=Path({str(observations)!r})\n"
            "try:\n"
            " if active:\n"
            "  source.write_bytes(changed)\n"
            "  consumed=Path.cwd()/source.name\n"
            "  with observed.open('a') as stream: stream.write(json.dumps({'name':source.name,'cwd':str(Path.cwd()),"
            "'original_changed':source.read_bytes()!=original,'consumed_sha256':hashlib.sha256(consumed.read_bytes()).hexdigest()})+'\\n')\n"
            f" code=subprocess.run([{executable!r}]+sys.argv[1:]).returncode\n"
            "finally:\n if active: source.write_bytes(original)\nraise SystemExit(code)\n"
        )
        adapter.chmod(0o700)
    monkeypatch.setenv("PATH", str(shims) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("FORMAL_JAVA_BIN", str(shims / "java"))
    receipt = run_formal_tools(root, timeout=300)
    assert receipt["status"] == "passed" and receipt["source_unchanged"] is True, receipt
    checks = {row["name"]: row for row in receipt["checks"]}
    assert checks["lean-build"]["exit_code"] == 0
    assert "INPUT_ABA_ACCEPTED" not in checks["lean-build"]["stdout"]
    assert checks["tlc-AntProtocolFaultyNegControl"]["exit_code"] == 12
    records = [json.loads(line) for line in observations.read_text().splitlines()]
    assert {row["name"] for row in records} == {lean_source.name, tla_config.name}
    for row, content in zip(sorted(records, key=lambda row: row["name"]), (lean_bytes, tla_bytes), strict=True):
        assert row["original_changed"] and Path(row["cwd"]) not in {lean_source.parent, tla_config.parent}
        assert row["consumed_sha256"] == hashlib.sha256(content).hexdigest()
    assert lean_source.read_bytes() == lean_bytes and tla_config.read_bytes() == tla_bytes
    assert (
        checks["lean-build"]["consumed_source_sha256"]["formal/lean/AntProtocol.lean"]
        == hashlib.sha256(lean_bytes).hexdigest()
    )
    assert (
        checks["tlc-AntProtocolFaultyNegControl"]["consumed_source_sha256"][
            "formal/tla/AntProtocolFaultyNegControl.cfg"
        ]
        == hashlib.sha256(tla_bytes).hexdigest()
    )


def test_root_runtime_typing_cache_is_separate_from_authored_nested_inputs(tmp_path: Path) -> None:
    runtime = tmp_path / ".mypy_cache/type.meta.json"
    runtime.parent.mkdir()
    runtime.write_text("runtime metadata one")
    authored = tmp_path / "data/.mypy_cache/declared.json"
    authored.parent.mkdir(parents=True)
    authored.write_text("authored input one")
    before = _sources(tmp_path)
    runtime.write_text("runtime metadata two")
    assert _sources(tmp_path) == before
    authored.write_text("authored input two")
    assert _sources(tmp_path) != before


def test_nested_authored_coverage_and_lake_names_remain_bound(tmp_path: Path) -> None:
    authored = tmp_path / "data/.coverage"
    authored.parent.mkdir()
    authored.write_text("declared input one")
    lake = tmp_path / "data/.lake/Input.lean"
    lake.parent.mkdir()
    lake.write_text("declared model one")
    before = _sources(tmp_path)
    assert {"data/.coverage", "data/.lake/Input.lean"} <= before.keys()
    authored.write_text("declared input two")
    assert _sources(tmp_path) != before


def test_cache_symlink_never_grants_reuse_or_acquisition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _copy(tmp_path)
    jar = root / "formal/tla/tla2tools.jar"
    # A fresh checkout may hold no admitted jar; the control starts from none.
    jar.unlink(missing_ok=True)
    outside = tmp_path / "outside.jar"
    outside.write_bytes(b"outside source")
    jar.symlink_to(outside)
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    monkeypatch.delenv("FORMAL_JAVA_BIN", raising=False)
    assert run_formal_tools(root, timeout=2, acquire=True)["status"] == "failed"
    assert _acquire_jar(root, time.monotonic() + 2).status == "failed"
    assert outside.read_bytes() == b"outside source"


def test_explicit_acquisition_without_transfer_tool_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _copy(tmp_path)
    (root / "formal/tla/tla2tools.jar").unlink(missing_ok=True)
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    monkeypatch.delenv("FORMAL_JAVA_BIN", raising=False)
    monkeypatch.delenv("TEMPLATE_FORMAL_TLC_JAR", raising=False)
    receipt = run_formal_tools(root, timeout=2, acquire=True)
    assert receipt["status"] == "blocked"
    checks = {check["name"]: check for check in receipt["checks"]}
    assert checks["tlc-acquire"]["status"] == "blocked"
    assert checks["tlc-acquire"]["exit_code"] is None
    assert not (root / "formal/tla/tla2tools.jar").exists()


def test_expired_deadline_launches_no_child(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    check = _run(
        "expired",
        [sys.executable, "-c", "from pathlib import Path; Path('marker').touch()"],
        tmp_path,
        time.monotonic() - 1,
    )
    assert check.status == "timed_out" and check.exit_code is None
    assert not marker.exists()


def test_real_completed_child_cannot_pass_after_total_cleanup_budget(tmp_path: Path) -> None:
    deadline = time.monotonic() + 2.0
    # The child really completes (exit 0) a few milliseconds before the shared
    # deadline (CLOCK_MONOTONIC is system-wide), so reaping and cleanup cross it.
    child = "import sys,time; time.sleep(max(0.0, float(sys.argv[1]) - time.monotonic() - 0.001))"
    check = _run("budget-control", [sys.executable, "-I", "-c", child, repr(deadline)], tmp_path, deadline)
    finished = time.monotonic()
    # Success can never be reported once the budget is spent: either cleanup
    # finished late (exit 0) or the runner killed the child at the deadline.
    assert check.status == "timed_out" and check.exit_code in {0, 124, -9}
    assert finished >= deadline - 0.05


def test_cli_blocker_receipt_and_invalid_invocation_have_distinct_exits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = _copy(tmp_path / "project")
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    monkeypatch.delenv("FORMAL_JAVA_BIN", raising=False)
    receipt_path = tmp_path / "receipts/tools.json"
    assert main(["--project-root", str(root), "--receipt", str(receipt_path)]) == 75
    assert json.loads(receipt_path.read_text())["status"] == "blocked"
    assert json.loads(capsys.readouterr().out)["source_unchanged"] is True
    assert main(["--project-root", str(root), "--timeout", "0"]) == 2
    assert "timeout" in capsys.readouterr().out


def test_real_child_environment_and_nonzero_exit_are_preserved(tmp_path: Path) -> None:
    env = build_bounded_env({"PATH": os.defpath, "API_KEY": "synthetic-control", "PUBLIC_MODE": "core"})
    result = run_bounded_subprocess(
        [
            sys.executable,
            "-c",
            "import os,sys; print(os.environ['PUBLIC_MODE']); assert 'API_KEY' not in os.environ; sys.exit(7)",
        ],
        cwd=tmp_path,
        env=env,
        timeout=5,
    )
    assert result.returncode == 7 and not result.timed_out and result.stdout.strip() == "core"
    result = run_bounded_subprocess(
        [sys.executable, "-c", "raise SystemExit(0)"], cwd=tmp_path, env=env, timeout=5, capture_output=False
    )
    assert result.returncode == 0 and result.stdout == result.stderr == ""


@pytest.mark.timeout(360)
def test_external_prepared_tlc_executes_without_source_jar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ISC-124: the actual pinned tool runs outside authored/export source."""
    root = _copy(tmp_path / "project")
    local = root / "formal/tla/tla2tools.jar"
    external = tmp_path / "prepared-tlc.jar"
    local.replace(external)
    monkeypatch.setenv("TEMPLATE_FORMAL_TLC_JAR", str(external))
    assert _selected_jar(root) == external
    receipt = run_formal_tools(root, timeout=300)
    assert receipt["status"] == "passed", receipt
    assert receipt["source_unchanged"] is True
    assert not local.exists()
    assert hashlib.sha256(external.read_bytes()).hexdigest() == TLC_SHA256
    checks = {check["name"]: check for check in receipt["checks"]}
    assert checks["tlc-AntProtocol"]["consumed_tlc_sha256"] == TLC_SHA256
    assert checks["tlc-AntProtocolFaultyNegControl"]["exit_code"] == 12


def test_external_tlc_selection_refuses_unsafe_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ISC-124: external configuration cannot bypass the existing cache guard."""
    root = _copy(tmp_path / "project")
    local = root / "formal/tla/tla2tools.jar"
    external = tmp_path / "prepared-tlc.jar"
    local.replace(external)
    monkeypatch.setenv("TEMPLATE_FORMAL_TLC_JAR", "relative.jar")
    with pytest.raises(ValueError, match="absolute"):
        _selected_jar(root)
    monkeypatch.setenv("TEMPLATE_FORMAL_TLC_JAR", str(external))
    local.write_bytes(b"corrupt local cache")
    assert _selected_jar(root) == local
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    assert run_formal_tools(root, timeout=2)["status"] == "failed"
    local.unlink()
    external.write_bytes(b"corrupt provider")
    assert run_formal_tools(root, timeout=2, acquire=True)["status"] == "failed"
    assert external.read_bytes() == b"corrupt provider" and not local.exists()
    external.unlink()
    assert run_formal_tools(root, timeout=2, acquire=True)["status"] == "blocked"
    assert not external.exists() and not local.exists()
    external.symlink_to(root / "formal/lean/AntProtocol.lean")
    assert run_formal_tools(root, timeout=2)["status"] == "failed"
