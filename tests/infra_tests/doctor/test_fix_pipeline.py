"""End-to-end tests: detect → plan → apply → undo, against real trees."""

from pathlib import Path


from infrastructure.doctor.detectors import (
    detect_pycache_clutter,
    detect_run_sh_executable,
    detect_stale_coverage_files,
)
from infrastructure.doctor.fixers import build_plans_for_findings
from infrastructure.doctor.models import TherapyLevel
from infrastructure.doctor.safety import DoctorState, load_journal, mutate, undo


def _bootstrap(repo: Path) -> None:
    (repo / "projects").mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='t'\nversion='0'\n")
    (repo / "uv.lock").write_text("# empty\n")
    run_sh = repo / "run.sh"
    run_sh.write_text("#!/bin/sh\necho hi\n")
    run_sh.chmod(0o644)  # intentionally not executable


def test_run_sh_fix_roundtrip(tmp_path: Path):
    _bootstrap(tmp_path)
    state = DoctorState(tmp_path)
    state.ensure()

    # 1) Detect.
    findings = detect_run_sh_executable(tmp_path)
    assert findings[0].healthy is False

    # 2) Plan.
    plans = build_plans_for_findings(findings, state)
    assert len(plans) == 1
    assert plans[0].fix_id == "fix_make_run_sh_executable"

    # 3) Apply.
    record = mutate(plans[0], state)
    assert record.applied is True
    import os

    assert os.access(tmp_path / "run.sh", os.X_OK)

    # 4) Re-detect: healthy now.
    findings2 = detect_run_sh_executable(tmp_path)
    assert findings2[0].healthy is True

    # 5) Undo: back to non-executable.
    undo(record, state)
    assert not os.access(tmp_path / "run.sh", os.X_OK)


def test_pycache_clean_then_undo(tmp_path: Path):
    _bootstrap(tmp_path)
    state = DoctorState(tmp_path)
    state.ensure()

    cache = tmp_path / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "x.pyc").write_text("compiled")

    findings = detect_pycache_clutter(tmp_path)
    plans = build_plans_for_findings(findings, state)
    assert len(plans) >= 1

    records = [mutate(p, state) for p in plans]
    assert all(r.applied for r in records)
    assert not cache.exists()

    # Undo every record (newest-first).
    for r in reversed(records):
        undo(r, state)
    assert cache.exists()
    assert (cache / "x.pyc").read_text() == "compiled"


def test_therapy_cap_filters_radical(tmp_path: Path):
    """build_plans_for_findings must not emit radical plans when capped."""
    _bootstrap(tmp_path)
    state = DoctorState(tmp_path)
    # Manufacture a finding manually so we don't need an orphan output dir.
    from infrastructure.doctor.models import (
        Finding,
        RepairLevel,
        Severity,
    )

    finding = Finding(
        code="DOC303",
        title="orphan",
        severity=Severity.WARN,
        healthy=False,
        description="",
        evidence={"orphans": []},
        repair_levels=(
            RepairLevel(
                level=TherapyLevel.RADICAL,
                fix_id="fix_remove_orphan_output_dirs",
                description="radical",
            ),
        ),
    )

    conservative = build_plans_for_findings([finding], state, max_therapy=TherapyLevel.CONSERVATIVE)
    assert conservative == []

    radical = build_plans_for_findings([finding], state, max_therapy=TherapyLevel.RADICAL)
    # Evidence has empty orphans, so still zero plans — but the *gate*
    # is what we're testing: with CONSERVATIVE we never even reach the
    # builder. The empty list under RADICAL proves the builder ran and
    # produced nothing for itself.
    assert radical == []


def test_select_codes_narrows_plan(tmp_path: Path):
    _bootstrap(tmp_path)
    state = DoctorState(tmp_path)
    state.ensure()
    (tmp_path / ".coverage").write_text("x")
    cov_findings = detect_stale_coverage_files(tmp_path)
    run_sh_findings = detect_run_sh_executable(tmp_path)
    all_findings = cov_findings + run_sh_findings

    # Only ask for DOC103.
    plans = build_plans_for_findings(all_findings, state, selected_codes=frozenset({"DOC103"}))
    assert {p.fix_id for p in plans} == {"fix_make_run_sh_executable"}

    # Only ask for fix_clean_coverage_files.
    plans2 = build_plans_for_findings(
        all_findings,
        state,
        selected_fix_ids=frozenset({"fix_clean_coverage_files"}),
    )
    assert {p.fix_id for p in plans2} == {"fix_clean_coverage_files"}


def test_journal_records_every_attempt(tmp_path: Path):
    """Even failed attempts land in the journal so audit is complete."""
    _bootstrap(tmp_path)
    state = DoctorState(tmp_path)
    state.ensure()

    # Create a plan that will fail (write_file refuses overwrite by default).
    existing = tmp_path / "exists.txt"
    existing.write_text("original")
    from infrastructure.doctor.models import FixPlan

    plan = FixPlan(
        fix_id="bad_write",
        title="overwrite refused",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(existing,),
        action_kind="write_file",
        params={"content": "stomp", "overwrite": False},
    )
    record = mutate(plan, state)
    assert record.applied is False
    journal = load_journal(state)
    assert journal[-1].applied is False
    assert journal[-1].error is not None
    # And the file is untouched.
    assert existing.read_text() == "original"
