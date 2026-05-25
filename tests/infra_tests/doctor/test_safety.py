"""Tests for the mutate() chokepoint and undo()."""

import hashlib
from pathlib import Path

import pytest

from infrastructure.doctor.models import FixPlan, TherapyLevel
from infrastructure.doctor.safety import (
    ABSENT_SENTINEL,
    DoctorSafetyError,
    DoctorState,
    load_journal,
    mutate,
    undo,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    """A throwaway repo tree we can mutate freely."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file.txt").write_text("hello\n")
    (tmp_path / "another.txt").write_text("world\n")
    return tmp_path


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


def test_mutate_refuses_paths_outside_repo(fake_repo: Path, tmp_path_factory):
    state = DoctorState(fake_repo)
    outside = tmp_path_factory.mktemp("outside") / "evil.txt"
    outside.write_text("nope")
    plan = FixPlan(
        fix_id="test",
        title="should refuse",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(outside,),
        action_kind="delete_paths",
    )
    with pytest.raises(DoctorSafetyError, match="escapes repo root"):
        mutate(plan, state)


def test_mutate_refuses_self_modification(fake_repo: Path):
    """A fix may not target paths inside .doctor/."""
    state = DoctorState(fake_repo)
    state.ensure()
    target = state.root / "evil"
    plan = FixPlan(
        fix_id="test",
        title="should refuse",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(target,),
        action_kind="delete_paths",
    )
    with pytest.raises(DoctorSafetyError, match="inside doctor state directory"):
        mutate(plan, state)


# ---------------------------------------------------------------------------
# Backup + delete roundtrip
# ---------------------------------------------------------------------------


def test_delete_paths_backs_up_and_can_be_undone(fake_repo: Path):
    state = DoctorState(fake_repo)
    target = fake_repo / "subdir" / "file.txt"
    pre_hash = _sha(target)

    plan = FixPlan(
        fix_id="delete_one",
        title="delete file",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(target,),
        action_kind="delete_paths",
    )
    record = mutate(plan, state)

    # File is gone, journal has the action, backup has the file.
    assert record.applied is True
    assert not target.exists()
    assert record.pre_hashes[str(target.resolve())] == pre_hash
    assert record.post_hashes[str(target.resolve())] == ABSENT_SENTINEL

    backup_file = Path(record.backup_dir) / "subdir" / "file.txt"
    assert backup_file.exists()
    assert _sha(backup_file) == pre_hash

    # Journal has exactly one record.
    journal = load_journal(state)
    assert len(journal) == 1
    assert journal[0].action_id == record.action_id

    # Undo restores byte-for-byte.
    undo_record = undo(record, state)
    assert undo_record.applied is True
    assert target.exists()
    assert _sha(target) == pre_hash

    # Now the journal has two records (action + undo).
    journal2 = load_journal(state)
    assert len(journal2) == 2
    assert journal2[1].fix_id == "undo:delete_one"
    assert journal2[1].reversible is False


def test_chmod_handler_adds_execute_bit(fake_repo: Path):
    state = DoctorState(fake_repo)
    target = fake_repo / "another.txt"
    target.chmod(0o644)
    plan = FixPlan(
        fix_id="exec",
        title="chmod +x",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(target,),
        action_kind="chmod",
        params={"mode": 0o111},
    )
    record = mutate(plan, state)
    assert record.applied
    new_mode = target.stat().st_mode & 0o777
    assert new_mode & 0o111 == 0o111  # executable bits set
    assert new_mode & 0o644 == 0o644  # original bits preserved


def test_write_file_creates_new_file(fake_repo: Path):
    state = DoctorState(fake_repo)
    target = fake_repo / "newdir" / "newfile.sh"
    plan = FixPlan(
        fix_id="writeit",
        title="write file",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(target,),
        action_kind="write_file",
        params={"content": "#!/bin/sh\necho hi\n", "overwrite": False},
    )
    record = mutate(plan, state)
    assert record.applied
    assert target.read_text().startswith("#!/bin/sh")
    # Undo restores absence.
    undo(record, state)
    assert not target.exists()


def test_write_file_refuses_overwrite_by_default(fake_repo: Path):
    state = DoctorState(fake_repo)
    target = fake_repo / "another.txt"
    plan = FixPlan(
        fix_id="writeit",
        title="should refuse overwrite",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(target,),
        action_kind="write_file",
        params={"content": "stomp", "overwrite": False},
    )
    record = mutate(plan, state)
    # The handler raised, so applied=False and the journal records the error,
    # but the file is unchanged.
    assert record.applied is False
    assert record.error and "Refusing to overwrite" in record.error
    assert target.read_text() == "world\n"


def test_unknown_action_kind_is_a_programmer_error(fake_repo: Path):
    state = DoctorState(fake_repo)
    plan = FixPlan(
        fix_id="x",
        title="bad",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(fake_repo / "another.txt",),
        action_kind="this_kind_does_not_exist",
    )
    with pytest.raises(DoctorSafetyError, match="No handler registered"):
        mutate(plan, state)


def test_undo_refuses_non_reversible_action(fake_repo: Path):
    state = DoctorState(fake_repo)
    state.ensure()
    target = fake_repo / "subdir" / "file.txt"
    plan = FixPlan(
        fix_id="delete_one",
        title="delete file",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(target,),
        action_kind="delete_paths",
        reversible=False,
    )
    record = mutate(plan, state)
    assert record.reversible is False
    with pytest.raises(DoctorSafetyError, match="not reversible"):
        undo(record, state)


def test_directory_backup_and_undo_roundtrips(fake_repo: Path):
    state = DoctorState(fake_repo)
    # Create a nested tree to delete and restore.
    nested = fake_repo / "to_delete"
    nested.mkdir()
    (nested / "a.txt").write_text("A")
    (nested / "sub").mkdir()
    (nested / "sub" / "b.txt").write_text("B" * 1000)
    pre_a = _sha(nested / "a.txt")
    pre_b = _sha(nested / "sub" / "b.txt")

    plan = FixPlan(
        fix_id="rmdir",
        title="delete dir",
        therapy=TherapyLevel.RADICAL,
        finding_code="DOC999",
        affected_paths=(nested,),
        action_kind="delete_paths",
    )
    record = mutate(plan, state)
    assert record.applied
    assert not nested.exists()

    undo(record, state)
    assert (nested / "a.txt").exists()
    assert (nested / "sub" / "b.txt").exists()
    assert _sha(nested / "a.txt") == pre_a
    assert _sha(nested / "sub" / "b.txt") == pre_b


def test_journal_is_append_only_and_parseable(fake_repo: Path):
    state = DoctorState(fake_repo)
    for name in ("subdir/file.txt", "another.txt"):
        target = fake_repo / name
        if not target.exists():
            continue
        plan = FixPlan(
            fix_id="seq",
            title=f"delete {name}",
            therapy=TherapyLevel.CONSERVATIVE,
            finding_code="DOC999",
            affected_paths=(target,),
            action_kind="delete_paths",
        )
        mutate(plan, state)
    journal = load_journal(state)
    assert [r.applied for r in journal] == [True, True]
    # Two distinct action ids — the journal is append-only.
    assert journal[0].action_id != journal[1].action_id
    # And the timestamp on the second is >= the first (clock can tie).
    assert journal[0].timestamp_utc <= journal[1].timestamp_utc


def test_idempotent_delete_records_absent_pre_hash(fake_repo: Path):
    """Deleting an already-absent path is a journalled noop with ABSENT pre-hash."""
    state = DoctorState(fake_repo)
    ghost = fake_repo / "does_not_exist.txt"
    plan = FixPlan(
        fix_id="ghost",
        title="delete nothing",
        therapy=TherapyLevel.CONSERVATIVE,
        finding_code="DOC999",
        affected_paths=(ghost,),
        action_kind="delete_paths",
    )
    record = mutate(plan, state)
    assert record.applied is True
    assert record.pre_hashes[str(ghost.resolve())] == ABSENT_SENTINEL
    assert record.post_hashes[str(ghost.resolve())] == ABSENT_SENTINEL
