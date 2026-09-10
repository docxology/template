"""Receipt and output-isolation tests for the per-project pytest matrix.

Covers ``PublicMatrixReceipt`` writing and validation on green and failing
runs, output-tree digest semantics (runtime-cache exclusions, declared
artifacts), and kill/reject behavior for detached or parent-owned output
writers.
"""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.testing.test_runner import (
    DEFAULT_COVERAGE_FILE,
    _output_tree_digest,
    run_per_project_pytest,
)
from infrastructure.core.testing.test_runner_outputs import declared_output_relpaths
from ._test_runner_helpers import _write_project

pytestmark = pytest.mark.timeout(120)


def test_empty_matrix_still_writes_an_explicit_failure_receipt(synthetic_repo: Path) -> None:
    receipt_path = synthetic_repo / "empty-matrix-receipt.json"
    assert run_per_project_pytest(synthetic_repo, projects=[], receipt_path=receipt_path) == 1
    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    assert receipt.overall_exit == 1
    assert receipt.skip_reasons["<no-runnable-projects>"].startswith("error:")


def test_receipt_is_written_and_validates_for_green_run(synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A passing matrix writes a deterministic receipt with per-lane facts."""
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    _write_project(synthetic_repo, "beta", fail=False, extra_module="mod_beta")

    receipt_path = synthetic_repo / "public-matrix-receipt.json"
    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "beta"],
        fail_under=1,
        timeout=60,
        receipt_path=receipt_path,
    )
    assert rc == 0
    assert receipt_path.is_file()

    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    lane_names = {lane.project_name for lane in receipt.lanes}
    assert lane_names == {"alpha", "beta"}
    assert receipt.roster_revision in {"unknown", "abc123"} or len(receipt.roster_revision) == 40
    assert receipt.profile == "quick"
    # Deterministic: repeated runs produce the same content digest.
    first_digest = receipt.digest()
    receipt.write(receipt_path)
    assert PublicMatrixReceipt.read(receipt_path).digest() == first_digest


def test_receipt_captures_failure_and_is_written_on_error(
    synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing lane must still produce a receipt recording the failure."""
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    _write_project(synthetic_repo, "beta", fail=True, extra_module="mod_beta")

    receipt_path = synthetic_repo / "public-matrix-receipt.json"
    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "beta"],
        fail_under=1,
        timeout=60,
        receipt_path=receipt_path,
    )
    assert rc != 0
    assert receipt_path.is_file(), "receipt must be written even when the matrix fails"

    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    by_name = {lane.project_name: lane for lane in receipt.lanes}
    assert by_name["beta"].exit_code != 0
    assert receipt.overall_exit != 0
    errors = receipt.validate(["alpha", "beta"])
    assert any("EXIT-STATUS" in error and "beta" in error for error in errors)


def test_receipt_rejects_test_generated_output_drift(synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A green pytest lane cannot hide a mutation of its real output tree."""
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    project_root = synthetic_repo / "projects" / "alpha"
    output_file = project_root / "output" / "result.txt"
    output_file.parent.mkdir()
    output_file.write_text("baseline\n", encoding="utf-8")
    (project_root / "tests" / "test_output_drift.py").write_text(
        dedent(
            """
            from pathlib import Path


            def test_changes_real_output_tree() -> None:
                output = Path(__file__).parent.parent / "output" / "result.txt"
                output.write_text("mutated by test\\n", encoding="utf-8")
            """
        ).lstrip(),
        encoding="utf-8",
    )

    receipt_path = synthetic_repo / "public-matrix-receipt.json"
    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha"],
        fail_under=1,
        timeout=60,
        receipt_path=receipt_path,
    )

    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    assert rc == 1
    assert receipt.overall_exit == 1
    assert receipt.lanes[0].exit_code == 0
    assert receipt.lanes[0].output_isolation_ok is False
    assert receipt.validate(["alpha"]) == [
        "OVERALL-EXIT: receipt overall_exit=1",
        "OUTPUT-ISOLATION: project 'alpha' changed output/",
    ]


def test_output_digest_ignores_ignored_runtime_files_but_tracks_visible_files(tmp_path: Path) -> None:
    """Fresh-checkout runtime caches do not mask visible output mutations."""
    project_root = tmp_path / "projects" / "alpha"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True)
    (tmp_path / ".gitignore").write_text("projects/alpha/output/runtime.log\n", encoding="utf-8")
    tracked = output_dir / "result.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)  # noqa: S603

    before = _output_tree_digest(project_root)
    (output_dir / "runtime.log").write_text("local cache\n", encoding="utf-8")
    assert _output_tree_digest(project_root) == before

    (output_dir / "new-visible.txt").write_text("must be reported\n", encoding="utf-8")
    assert _output_tree_digest(project_root) != before

    (output_dir / "new-visible.txt").unlink()
    tracked.write_text("mutated\n", encoding="utf-8")
    assert _output_tree_digest(project_root) != before


def test_detached_project_writer_is_killed_before_receipt_finalization(
    synthetic_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful project lane cannot leave a detached output writer alive."""
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    project_root = synthetic_repo / "projects" / "alpha"
    output_file = project_root / "output" / "result.txt"
    output_file.parent.mkdir()
    output_file.write_text("baseline\n", encoding="utf-8")
    combined_coverage_file = synthetic_repo / DEFAULT_COVERAGE_FILE
    child_code = dedent(
        f"""
        import time
        from pathlib import Path

        trigger = Path({str(combined_coverage_file)!r})
        deadline = time.monotonic() + 10
        while not trigger.exists():
            if time.monotonic() >= deadline:
                raise SystemExit(2)
            time.sleep(0.005)
        Path({str(output_file)!r}).write_text("late drift\\n", encoding="utf-8")
        """
    ).lstrip()
    (project_root / "tests" / "test_late_output_drift.py").write_text(
        dedent(
            f"""
            import subprocess
            import sys


            def test_starts_detached_output_writer() -> None:
                subprocess.Popen(
                    [sys.executable, "-c", {child_code!r}],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            """
        ).lstrip(),
        encoding="utf-8",
    )

    receipt_path = synthetic_repo / "public-matrix-receipt.json"
    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha"],
        fail_under=1,
        timeout=60,
        receipt_path=receipt_path,
    )

    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    assert output_file.read_text(encoding="utf-8") == "baseline\n"
    assert rc == 0
    assert receipt.overall_exit == 0
    assert receipt.lanes[0].output_isolation_ok is True
    assert receipt.validate(["alpha"]) == []


def test_receipt_rejects_parent_output_drift_after_project_process_exits(
    synthetic_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A parent-owned mutation after the project matrix still fails closed."""
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    project_root = synthetic_repo / "projects" / "alpha"
    output_file = project_root / "output" / "result.txt"
    output_file.parent.mkdir()
    output_file.write_text("baseline\n", encoding="utf-8")
    combined_coverage_file = synthetic_repo / DEFAULT_COVERAGE_FILE
    mutation_errors: list[BaseException] = []

    def mutate_after_project_matrix() -> None:
        try:
            # The combined file is created only after the bounded project matrix
            # returns, leaving the coverage gate before receipt finalization.
            deadline = time.monotonic() + 10
            while not combined_coverage_file.exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError("combined coverage file was not created")
                time.sleep(0.005)
            output_file.write_text("late drift\n", encoding="utf-8")
        except BaseException as exc:  # noqa: BLE001 - propagate thread failure in the test process
            mutation_errors.append(exc)

    writer = threading.Thread(target=mutate_after_project_matrix, daemon=True)
    writer.start()
    receipt_path = synthetic_repo / "public-matrix-receipt.json"
    try:
        rc = run_per_project_pytest(
            synthetic_repo,
            projects=["alpha"],
            fail_under=1,
            timeout=60,
            receipt_path=receipt_path,
        )
    finally:
        writer.join(timeout=15)

    assert not writer.is_alive()
    assert mutation_errors == []
    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    assert output_file.read_text(encoding="utf-8") == "late drift\n"
    assert rc == 1
    assert receipt.overall_exit == 1
    assert receipt.lanes[0].output_isolation_ok is False
    assert receipt.validate(["alpha"]) == [
        "OVERALL-EXIT: receipt overall_exit=1",
        "OUTPUT-ISOLATION: project 'alpha' changed output/",
    ]


def test_output_digest_exclude_skips_declared_outputs(tmp_path: Path) -> None:
    """The exclusion set removes a project's declared artifacts from the digest."""
    project_root = tmp_path / "projects" / "alpha"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True)
    declared = output_dir / "result.txt"
    declared.write_text("regenerated per run\n", encoding="utf-8")
    undeclared = output_dir / "side.txt"
    undeclared.write_text("baseline\n", encoding="utf-8")
    exclude = frozenset({"output/result.txt"})

    before_excluding = _output_tree_digest(project_root, exclude=exclude)
    declared.write_text("refreshed with a new commit pin\n", encoding="utf-8")
    assert _output_tree_digest(project_root, exclude=exclude) == before_excluding

    undeclared.write_text("mutated\n", encoding="utf-8")
    assert _output_tree_digest(project_root, exclude=exclude) != before_excluding


def test_declared_output_relpaths_tolerates_missing_or_malformed_manifest(tmp_path: Path) -> None:
    """A missing or malformed manifest yields an empty set (strict isolation)."""
    project_root = tmp_path / "projects" / "alpha"
    (project_root / "output" / "reports").mkdir(parents=True)
    assert declared_output_relpaths(project_root) == frozenset()

    manifest = project_root / "output" / "reports" / "artifact_manifest.json"
    manifest.write_text("{not json", encoding="utf-8")
    assert declared_output_relpaths(project_root) == frozenset()

    manifest.write_text(
        '{"entries": [{"path": "output/reports/test_results.json"}, {"bogus": true}, "junk"]}',
        encoding="utf-8",
    )
    assert declared_output_relpaths(project_root) == frozenset({"output/reports/test_results.json"})


def test_receipt_allows_declared_output_artifact_regeneration(
    synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lane regenerating its *declared* output artifacts stays green.

    Exemplars declare their regenerated outputs in
    ``output/reports/artifact_manifest.json``; a fresh clone at a newer
    commit would otherwise deterministically fail isolation when the
    declared Stage-01 verifier refreshes e.g. the provenance commit pin —
    the silent all-green-then-exit-1 rehearsal failure this exemption fixes.
    """
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    project_root = synthetic_repo / "projects" / "alpha"
    output_file = project_root / "output" / "result.txt"
    output_file.parent.mkdir()
    output_file.write_text("stale commit pin\n", encoding="utf-8")
    reports_dir = project_root / "output" / "reports"
    reports_dir.mkdir()
    (reports_dir / "artifact_manifest.json").write_text(
        '{"entries": [{"path": "output/result.txt"}]}', encoding="utf-8"
    )
    (project_root / "tests" / "test_declared_regeneration.py").write_text(
        dedent(
            """
            from pathlib import Path


            def test_refreshes_declared_output_artifact() -> None:
                output = Path(__file__).parent.parent / "output" / "result.txt"
                output.write_text("current commit pin\\n", encoding="utf-8")
            """
        ).lstrip(),
        encoding="utf-8",
    )

    receipt_path = synthetic_repo / "public-matrix-receipt.json"
    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha"],
        fail_under=1,
        timeout=60,
        receipt_path=receipt_path,
    )

    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt

    receipt = PublicMatrixReceipt.read(receipt_path)
    assert rc == 0
    assert receipt.overall_exit == 0
    assert receipt.lanes[0].exit_code == 0
    assert receipt.lanes[0].output_isolation_ok is True
    assert receipt.validate(["alpha"]) == []
    assert output_file.read_text(encoding="utf-8") == "current commit pin\n"
