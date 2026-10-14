#!/usr/bin/env python3
"""Tests for infrastructure/core/analysis_pipeline.py.

Real subprocess execution and tmp_path fixtures only — no mocks. The
runner is invoked end-to-end with on-disk Python scripts.
"""

from __future__ import annotations

import textwrap
import hashlib
import json
import time
from pathlib import Path
import pytest

from infrastructure.core.analysis_pipeline import (
    run_analysis_pipeline,
    run_analysis_script,
    run_analysis_script_outcome,
)
from infrastructure.core.exceptions import ScriptExecutionError
from infrastructure.core.analysis_launch import analysis_receipt_path, analysis_stage_key
from infrastructure.core.analysis_evidence import AnalysisRunEvidence
from infrastructure.core.pipeline.fingerprints import source_fingerprint
from infrastructure.core.pipeline.outcomes import StageStatus

pytestmark = pytest.mark.timeout(120)


def _make_project(repo_root: Path, name: str = "p") -> Path:
    """Create a minimal project with src/scripts dirs."""
    project = repo_root / "projects" / name
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "scripts").mkdir(parents=True, exist_ok=True)
    return project


def _write_script(scripts_dir: Path, name: str, body: str) -> Path:
    path = scripts_dir / name
    path.write_text(textwrap.dedent(body))
    return path


def test_run_analysis_pipeline_no_scripts_returns_zero(tmp_path: Path) -> None:
    _make_project(tmp_path)
    assert run_analysis_pipeline([], tmp_path, "p") == 0


def test_run_analysis_script_success(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    marker = tmp_path / "ran.txt"
    script = _write_script(
        project / "scripts",
        "01_ok.py",
        f"""
        from pathlib import Path
        Path({str(marker)!r}).write_text("yes")
        """,
    )

    assert run_analysis_script(script, tmp_path, "p") == 0
    assert marker.read_text() == "yes"


def test_run_analysis_script_resolves_wip_project_env(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "working" / "draft"
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "scripts").mkdir(parents=True, exist_ok=True)
    marker = tmp_path / "project_dir.txt"
    script = _write_script(
        project / "scripts",
        "01_env.py",
        f"""
        import os
        from pathlib import Path
        Path({str(marker)!r}).write_text(os.environ["PROJECT_DIR"])
        """,
    )

    assert run_analysis_script(script, tmp_path, "draft") == 0
    assert marker.read_text() == str(project.resolve())


def test_run_analysis_script_nonzero_exit(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    script = _write_script(
        project / "scripts",
        "02_fail.py",
        """
        import sys
        sys.exit(3)
        """,
    )
    assert run_analysis_script(script, tmp_path, "p") == 3


def test_run_analysis_pipeline_collects_results(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    out = tmp_path / "outputs.txt"
    s1 = _write_script(
        project / "scripts",
        "01_a.py",
        f"""
        from pathlib import Path
        Path({str(out)!r}).write_text("first")
        """,
    )
    s2 = _write_script(
        project / "scripts",
        "02_b.py",
        f"""
        from pathlib import Path
        p = Path({str(out)!r})
        p.write_text(p.read_text() + ',second')
        """,
    )

    rc = run_analysis_pipeline([s1, s2], tmp_path, "p")
    assert rc == 0
    assert out.read_text() == "first,second"


def test_run_analysis_pipeline_reports_failure(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    s_ok = _write_script(project / "scripts", "01_ok.py", "print('ok')")
    s_bad = _write_script(
        project / "scripts",
        "02_bad.py",
        "import sys\nsys.exit(2)",
    )
    assert run_analysis_pipeline([s_ok, s_bad], tmp_path, "p") == 1


def test_manifest_snapshot_preserves_prior_analysis_receipt(tmp_path: Path) -> None:
    """A later publication snapshot must not rewrite an admitted first leaf."""
    project = _make_project(tmp_path)
    first = _write_script(project / "scripts", "01_first.py", "print('first producer')")
    second = _write_script(
        project / "scripts",
        "02_snapshot.py",
        f"""
        from pathlib import Path
        from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest
        output = Path({str(project / "output")!r})
        output.mkdir(exist_ok=True)
        snapshot_current_artifact_manifest(output)
        """,
    )

    assert run_analysis_pipeline([first, second], tmp_path, "p") == 0
    runs = list((project / "output" / ".pipeline" / "analysis").glob("*/run.json"))
    assert len(runs) == 1
    record = json.loads(runs[0].read_text())
    assert record["complete"] is True
    for key, expected in record["leaf_sha256"].items():
        leaf = analysis_receipt_path(project, record["run_id"], key)
        assert hashlib.sha256(leaf.read_bytes()).hexdigest() == expected


def test_run_analysis_script_missing_file_returns_python_exit(tmp_path: Path) -> None:
    """A non-existent script is rejected before subprocess execution."""
    project = _make_project(tmp_path)
    bogus = project / "scripts" / "does_not_exist.py"
    rc = run_analysis_script(bogus, tmp_path, "p")
    assert rc != 0


def test_run_analysis_script_rejects_external_path(tmp_path: Path) -> None:
    """Direct callers cannot execute a script outside the project tree."""
    _make_project(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("raise SystemExit(99)")
    assert run_analysis_script(outside, tmp_path, "p") == 1


def test_script_execution_error_class_attached() -> None:
    """``ScriptExecutionError`` is the documented wrapper used by run_analysis_script."""
    err = ScriptExecutionError("wrapped", context={"script": "x"})
    assert "wrapped" in str(err)


@pytest.mark.parametrize("exit_code,expected", [(0, 0), (2, 1), (7, 1), (75, 75), (124, 124), (130, 130)])
def test_real_leaf_exit_precedence_and_stop_policy(tmp_path: Path, exit_code: int, expected: int) -> None:
    project = _make_project(tmp_path)
    leaf = _write_script(project / "scripts", "first.py", f"raise SystemExit({exit_code})\n")
    marker = tmp_path / "second-ran.txt"
    second = _write_script(
        project / "scripts", "second.py", f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
    )
    assert run_analysis_pipeline([leaf, second], tmp_path, "p") == expected
    assert marker.exists() is (exit_code not in {75, 124, 130})


def test_original_leaf_failure_remains_in_typed_outcome(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    leaf = _write_script(project / "scripts", "failure.py", "raise SystemExit(7)\n")
    outcome = run_analysis_script_outcome(leaf, tmp_path, "p")
    assert outcome.stage_key == "analysis:scripts/failure.py"
    assert outcome.status is StageStatus.FAILED
    assert outcome.child_exit_code == 7
    assert outcome.attempt_exit_codes == (7,)


def test_missing_nominated_runtime_blocks_without_running_script(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    (project / ".venv").mkdir()
    marker = tmp_path / "must-not-run.txt"
    leaf = _write_script(
        project / "scripts", "leaf.py", f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
    )
    outcome = run_analysis_script_outcome(leaf, tmp_path, "p")
    assert outcome.status is StageStatus.BLOCKED
    assert outcome.child_exit_code is None
    assert run_analysis_pipeline([leaf], tmp_path, "p") == 75
    assert not marker.exists()


def test_expired_analysis_supervision_stops_following_producer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _make_project(tmp_path)
    marker = tmp_path / "must-not-run.txt"
    leaf = _write_script(project / "scripts", "sleep.py", "import time\ntime.sleep(30)\n")
    second = _write_script(
        project / "scripts", "second.py", f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
    )
    monkeypatch.setenv("ANALYSIS_SCRIPT_TIMEOUT_SEC", "0.01")
    assert run_analysis_pipeline([leaf, second], tmp_path, "p") == 124
    assert not marker.exists()


def test_aggregate_retains_actual_originals_and_exact_leaf_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    monkeypatch.setenv("PIPELINE_RUN_ID", "aggregate-originals")
    monkeypatch.setenv("PIPELINE_PLAN_DIGEST", "exact-parent-plan")
    first = _write_script(project / "scripts", "first.py", "raise SystemExit(7)\n")
    second = _write_script(project / "scripts", "second.py", "print('actual second producer')\n")
    assert run_analysis_pipeline([first, second], tmp_path, "p") == 1
    report = analysis_receipt_path(project, "aggregate-originals", "aggregate").with_name("run.json")
    record = json.loads(report.read_bytes())
    assert record["schema"] == "template-analysis-run/3"
    assert record["complete"] is False and record["exit_code"] == 1
    assert record["plan_digest"] == "exact-parent-plan"
    assert [leaf["child_exit_code"] for leaf in record["outcomes"]] == [7, 0]
    assert [leaf["attempt_exit_codes"] for leaf in record["outcomes"]] == [[7], [0]]
    for key, digest in record["leaf_sha256"].items():
        assert (
            digest
            == hashlib.sha256(analysis_receipt_path(project, "aggregate-originals", key).read_bytes()).hexdigest()
        )
    assert report.stat().st_mode & 0o777 == 0o600


def test_later_actual_producer_cannot_rewrite_previously_admitted_leaf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    monkeypatch.setenv("PIPELINE_RUN_ID", "aggregate-tamper")
    first = _write_script(project / "scripts", "first.py", "print('actual first producer')\n")
    target = analysis_receipt_path(project, "aggregate-tamper", analysis_stage_key(first, project))
    second = _write_script(
        project / "scripts",
        "second.py",
        f"from pathlib import Path\nPath({str(target)!r}).write_text('forged prior leaf')\n",
    )
    assert run_analysis_pipeline([first, second], tmp_path, "p") == 75
    record = json.loads(
        analysis_receipt_path(project, "aggregate-tamper", "aggregate").with_name("run.json").read_bytes()
    )
    assert record["complete"] is False
    assert [leaf["child_exit_code"] for leaf in record["outcomes"][:2]] == [0, 0]
    assert any("changed after admission" in leaf["diagnostic"] for leaf in record["outcomes"])


def test_actual_report_link_refuses_promotion_and_preserves_outside_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    monkeypatch.setenv("PIPELINE_RUN_ID", "aggregate-link")
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"private unchanged evidence")
    target = analysis_receipt_path(project, "aggregate-link", "aggregate").with_name("run.json")
    leaf = _write_script(
        project / "scripts",
        "link.py",
        f"from pathlib import Path\np=Path({str(target)!r})\np.parent.mkdir(parents=True,exist_ok=True)\n"
        f"p.symlink_to({str(outside)!r})\n",
    )
    assert run_analysis_pipeline([leaf], tmp_path, "p") == 75
    assert outside.read_bytes() == b"private unchanged evidence"


def test_actual_leaf_runtime_evidence_cannot_be_forged_for_aggregate_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    monkeypatch.setenv("PIPELINE_RUN_ID", "runtime-forgery")
    monkeypatch.setenv("PIPELINE_PLAN_DIGEST", "actual-plan")
    leaf = _write_script(project / "scripts", "actual.py", "print('actual admitted runtime')\n")
    source = source_fingerprint(tmp_path, project)
    outcome = run_analysis_script_outcome(leaf, tmp_path, "p")
    assert outcome.complete
    target = analysis_receipt_path(project, "runtime-forgery", outcome.stage_key)
    original = json.loads(target.read_bytes())
    evidence = AnalysisRunEvidence(
        tmp_path, project, "runtime-forgery", "actual-plan", (outcome.stage_key,), source, time.monotonic() + 90, {}
    )
    evidence.admit_leaf(outcome)
    for field, forged in (
        ("schema", "template-python-stage/2"),
        ("source_content_digest", "0" * 64),
        ("runtime_digest", "0" * 64),
        ("actual_runtime", {"executable": "invented-runtime"}),
    ):
        record = json.loads(json.dumps(original))
        record["worker"]["completion"][field] = forged
        target.write_text(json.dumps(record))
        with pytest.raises(ValueError, match="worker completion"):
            evidence.admit_leaf(outcome)
    record = json.loads(json.dumps(original))
    record["dependency_proof"] = "invented-complete-member-proof"
    target.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="does not match"):
        evidence.admit_leaf(outcome)
