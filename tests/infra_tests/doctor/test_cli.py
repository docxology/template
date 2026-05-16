"""CLI smoke tests — exercise the argparse surface against a tmp repo."""


import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


from infrastructure.doctor.cli import main
from infrastructure.doctor.reporter import EXIT_HEALTHY, EXIT_USAGE, EXIT_WARN


def _bootstrap(repo: Path) -> None:
    (repo / "projects").mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='t'\nversion='0'\n")
    (repo / "uv.lock").write_text("# empty\n")
    run = repo / "run.sh"
    run.write_text("#!/bin/sh\necho hi\n")
    run.chmod(0o755)


def _capture(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def test_capabilities_emits_valid_json(tmp_path: Path):
    _bootstrap(tmp_path)
    code, stdout, _ = _capture(["--repo-root", str(tmp_path), "capabilities"])
    assert code == 0
    payload = json.loads(stdout)
    assert "detectors" in payload
    assert "fixers" in payload
    assert "exit_codes" in payload
    fix_ids = {f["fix_id"] for f in payload["fixers"]}
    assert "fix_make_run_sh_executable" in fix_ids


def test_robot_docs_emits_stable_text(tmp_path: Path):
    code, stdout, _ = _capture(["--repo-root", str(tmp_path), "robot-docs"])
    assert code == 0
    assert "infrastructure.doctor" in stdout
    assert "EXIT CODES" in stdout
    assert "CONTRACT" in stdout


def test_diagnose_on_clean_tmp_repo(tmp_path: Path):
    _bootstrap(tmp_path)
    code, stdout, _ = _capture(["--repo-root", str(tmp_path), "diagnose"])
    # No CRITICAL or ERROR findings expected — at worst a couple of WARNs
    # for optional services. Exit code is 0 or 1.
    assert code in (EXIT_HEALTHY, EXIT_WARN)
    assert "score" in stdout


def test_diagnose_json(tmp_path: Path):
    _bootstrap(tmp_path)
    code, stdout, _ = _capture(
        ["--repo-root", str(tmp_path), "--json", "diagnose"]
    )
    payload = json.loads(stdout)
    assert payload["exit_code"] == code
    assert isinstance(payload["findings"], list)
    assert "overall_score" in payload


def test_fix_plan_does_not_mutate(tmp_path: Path):
    """``--plan`` must not change anything on disk."""
    _bootstrap(tmp_path)
    # Force a fixable finding: drop the executable bit.
    (tmp_path / "run.sh").chmod(0o644)

    code, stdout, _ = _capture(
        ["--repo-root", str(tmp_path), "fix", "--plan"]
    )
    # Still not executable.
    assert not os.access(tmp_path / "run.sh", os.X_OK)
    # The "Skipped" section should mention the planned fix.
    assert "fix_make_run_sh_executable" in stdout


def test_fix_apply_then_undo_last(tmp_path: Path):
    _bootstrap(tmp_path)
    (tmp_path / "run.sh").chmod(0o644)

    code, _, _ = _capture(
        ["--repo-root", str(tmp_path), "fix", "--apply"]
    )
    assert os.access(tmp_path / "run.sh", os.X_OK)

    code, _, _ = _capture(
        ["--repo-root", str(tmp_path), "undo", "--last"]
    )
    assert code == 0
    assert not os.access(tmp_path / "run.sh", os.X_OK)


def test_undo_with_no_target_returns_usage_error(tmp_path: Path):
    _bootstrap(tmp_path)
    code, _, err = _capture(["--repo-root", str(tmp_path), "undo"])
    assert code == EXIT_USAGE
    assert "Specify" in err


def test_history_lists_actions(tmp_path: Path):
    _bootstrap(tmp_path)
    (tmp_path / "run.sh").chmod(0o644)
    _capture(["--repo-root", str(tmp_path), "fix", "--apply"])
    code, stdout, _ = _capture(["--repo-root", str(tmp_path), "history"])
    assert code == 0
    assert "fix_make_run_sh_executable" in stdout
