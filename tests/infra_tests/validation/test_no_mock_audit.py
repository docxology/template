"""Real-file and subprocess tests for the shared mock-policy audit CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from infrastructure.validation.output.no_mock_audit import (
    collect_lexical_audit,
    collect_standin_inventory,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPERS = (
    REPO_ROOT / "scripts" / "verify_no_mocks.py",
    REPO_ROOT / "scripts" / "audit" / "verify_no_mocks.py",
)


def _make_repo(tmp_path: Path, source: str) -> Path:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_policy.py").write_text(source, encoding="utf-8")
    return tmp_path


def test_lexical_success_claims_only_what_was_scanned(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = _make_repo(
        tmp_path,
        "def test_real(monkeypatch):\n    monkeypatch.setattr('package.value', 1)\n",
    )

    exit_code = main([], repo_root=repo_root)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PASS: no prohibited mock-framework imports or calls detected." in output
    assert "does not evaluate pytest.monkeypatch dependency replacement" in output
    assert "Real data and computations used throughout" not in output
    assert collect_lexical_audit(repo_root).status == "pass"


def test_lexical_violation_has_deterministic_failure_report(
    tmp_path: Path,
    capsys,
) -> None:
    constructor = "Magic" + "Mock"
    repo_root = _make_repo(
        tmp_path,
        f"from unittest.mock import {constructor}\n\ndef test_bad():\n    assert {constructor}()\n",
    )

    first_exit = main(["--json"], repo_root=repo_root)
    first_output = capsys.readouterr().out
    second_exit = main(["--json"], repo_root=repo_root)
    second_output = capsys.readouterr().out

    assert first_exit == second_exit == 1
    assert first_output == second_output
    report = json.loads(first_output)
    assert report["mode"] == "lexical_mock_framework_gate"
    assert report["status"] == "fail"
    assert report["exit_code"] == 1
    assert len(report["violations"]) == 2


def test_inventory_is_advisory_until_strict_mode_is_requested(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = _make_repo(
        tmp_path,
        """\
def test_uses(monkeypatch, tmp_path):
    monkeypatch.setenv("KEY", "value")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("package.value", 1)
    monkeypatch.setitem({}, "key", "value")
""",
    )

    advisory_exit = main(["--inventory", "--json"], repo_root=repo_root)
    advisory = json.loads(capsys.readouterr().out)
    strict_exit = main(
        ["--inventory", "--fail-on-dependency-replacement", "--json"],
        repo_root=repo_root,
    )
    strict = json.loads(capsys.readouterr().out)

    assert advisory_exit == 0
    assert advisory["status"] == "advisory_debt"
    assert advisory["exit_code"] == 0
    assert advisory["enforced"] is False
    assert advisory["counts"] == {
        "dependency_replacement": 2,
        "environment_isolation": 2,
        "import_path_isolation": 0,
        "other": 0,
        "total": 4,
    }
    assert strict_exit == 1
    assert strict["status"] == "fail"
    assert strict["exit_code"] == 1
    assert strict["enforced"] is True
    assert collect_standin_inventory(repo_root).exit_code == 0


def test_missing_required_tests_directory_fails_closed(tmp_path: Path) -> None:
    lexical = collect_lexical_audit(tmp_path)
    inventory = collect_standin_inventory(tmp_path)

    assert lexical.status == "scan_error"
    assert lexical.exit_code == 1
    assert inventory.status == "scan_error"
    assert inventory.exit_code == 1


def test_both_script_paths_delegate_to_identical_infrastructure_cli(
    tmp_path: Path,
) -> None:
    repo_root = _make_repo(
        tmp_path,
        "def test_env(monkeypatch):\n    monkeypatch.setenv('KEY', 'value')\n",
    )
    results = [
        subprocess.run(
            [
                sys.executable,
                str(wrapper),
                "--inventory",
                "--json",
                "--repo-root",
                str(repo_root),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        for wrapper in WRAPPERS
    ]

    assert [result.returncode for result in results] == [0, 0]
    assert results[0].stdout == results[1].stdout
    assert results[0].stderr == results[1].stderr == ""
    report = json.loads(results[0].stdout)
    assert report["counts"]["environment_isolation"] == 1
