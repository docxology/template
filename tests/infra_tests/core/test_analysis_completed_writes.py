"""Actual Source API output writes, repeated consumption and confinement."""

import hashlib
import time
from pathlib import Path

import pytest

from infrastructure.core.analysis_read_custody import observe_stage_analysis_reads
from infrastructure.core.analysis_write_custody import observe_stage_analysis_writes, write_analysis_bytes


def test_actual_completed_write_and_repeated_returned_reads_share_body_identity(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects/templates/template_code_project"
    script = project / "scripts/probe.py"
    script.parent.mkdir(parents=True)
    body = (
        "from infrastructure.core.analysis_write_custody import write_analysis_bytes\n"
        "from infrastructure.core.analysis_read_custody import read_analysis_bytes\n"
        "target = project / 'output/data/probe.csv'\n"
        "write_analysis_bytes(project, target, b'value\\n1\\n')\n"
        "first = read_analysis_bytes(project, target)\n"
        "second = read_analysis_bytes(project, target)\n"
    )
    script.write_text(body)
    with observe_stage_analysis_reads(
        repo,
        project,
        run_id="actual-api-unit-run",
        stage_key="analysis:scripts/probe.py",
        nonce="a" * 32,
        request_digest="b" * 64,
        incoming={"run_id": "actual-api-unit-run", "stage_key": "analysis:scripts/probe.py", "records": []},
        deadline=time.monotonic() + 30,
    ) as reads:
        with observe_stage_analysis_writes(reads):
            actual = {"project": project}
            exec(compile(body, str(script), "exec"), actual)  # nosec B102 — fixed test Source script
            assert actual["first"] == actual["second"] == b"value\n1\n"
            observed = reads.data()
    written = observed["completed_writes"]["records"]
    consumed = observed["records"]
    assert len(written) == 1 and len(consumed) == 2
    assert written[0]["sha256"] == hashlib.sha256(b"value\n1\n").hexdigest()
    assert written[0]["prior_registered_read_count"] == 0
    assert [row["origin"] for row in consumed] == ["actual-completed-Source-write:1"] * 2
    assert all(row["native_identity"] == written[0]["native_identity"] for row in consumed)
    assert [row["ordinal"] for row in consumed] == [1, 2]
    assert written[0]["producer"]["source"] == script.relative_to(repo).as_posix()
    assert written[0]["prior_observed"] is None
    assert written[0]["prior_observation_authority"] == "prior-path-observation-only; not-compare-and-swap-history"


def test_live_write_scope_rejects_source_replacement_before_io(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects/templates/template_code_project"
    project.mkdir(parents=True)
    source = project / "manuscript/config.yaml"
    source.parent.mkdir()
    source.write_bytes(b"authored: true\n")
    with observe_stage_analysis_reads(
        repo,
        project,
        run_id="actual-api-unit-run",
        stage_key="analysis:scripts/probe.py",
        nonce="a" * 32,
        request_digest="b" * 64,
        incoming={"run_id": "actual-api-unit-run", "stage_key": "analysis:scripts/probe.py", "records": []},
        deadline=time.monotonic() + 30,
    ) as reads:
        with observe_stage_analysis_writes(reads):
            with pytest.raises(ValueError, match="output/event/body policy"):
                write_analysis_bytes(project, source, b"replaced: true\n")
    assert source.read_bytes() == b"authored: true\n"


def test_serialized_read_packet_cannot_begin_actual_write_scope() -> None:
    with pytest.raises(ValueError, match="real active worker read capture"):
        with observe_stage_analysis_writes({"status": "pass"}):  # type: ignore[arg-type]
            raise AssertionError("serialized packet unexpectedly admitted a write owner")


def test_secure_observed_writer_returns_actual_published_inode_and_keeps_ordinary_return(tmp_path: Path) -> None:
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined, atomic_write_bytes_confined_observed

    target = tmp_path / "nested/body.bin"
    assert atomic_write_bytes_confined(tmp_path, target, b"first") is None
    old = target.stat()
    held = atomic_write_bytes_confined_observed(tmp_path, target, b"second")
    actual = target.stat()
    assert held == (actual.st_dev, actual.st_ino, actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns)
    assert (actual.st_dev, actual.st_ino) != (old.st_dev, old.st_ino)
    assert target.read_bytes() == b"second"
    # An independent identical-byte replacement really has a different inode;
    # it cannot be retrospectively attributed to the earlier Source write.
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(b"second")
    replacement.replace(target)
    replaced = target.stat()
    assert (replaced.st_dev, replaced.st_ino) != held[:2]
    assert target.read_bytes() == b"second"
