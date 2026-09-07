"""Real subprocess contracts for the full-backup/restore shell pair."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKUP_SCRIPT = REPO_ROOT / "scripts/shell/backup-full.sh"
RESTORE_SCRIPT = REPO_ROOT / "scripts/shell/restore-test.sh"
RSYNC_AVAILABLE = shutil.which("rsync") is not None
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
PORTABLE_TEST_PATH = SYSTEM_PATH if shutil.which("rsync", path=SYSTEM_PATH) else os.environ.get("PATH", "")


def _subprocess_env(home: Path | str) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = PORTABLE_TEST_PATH
    return env


def _tree_state(root: Path) -> list[tuple[str, str, int, str]]:
    state: list[tuple[str, str, int, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: str(item.relative_to(root))):
        relative = str(path.relative_to(root))
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            state.append((relative, "symlink", mode, os.readlink(path)))
        elif path.is_file():
            state.append((relative, "file", mode, hashlib.sha256(path.read_bytes()).hexdigest()))
        else:
            state.append((relative, "directory", mode, ""))
    return state


def _run(
    script: Path,
    *args: str,
    cwd: Path,
    home: Path | str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=cwd,
        env=_subprocess_env(home),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _disposable_scripts_and_sources(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Copy the real entry points so their repository-relative sources are disposable."""
    repo = tmp_path / "disposable repo"
    shell_dir = repo / "scripts/shell"
    shell_dir.mkdir(parents=True)
    backup_script = shell_dir / BACKUP_SCRIPT.name
    restore_script = shell_dir / RESTORE_SCRIPT.name
    shutil.copy2(BACKUP_SCRIPT, backup_script)
    shutil.copy2(RESTORE_SCRIPT, restore_script)

    home = tmp_path / "operator home"
    hermes_config = home / ".hermes/config/config.yaml"
    hermes_config.parent.mkdir(parents=True)
    hermes_config.write_text("profile: test\n", encoding="utf-8")

    cache_file = repo / ".cache/search cache/index.db"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_bytes(b"cache-bytes\x00\x01")

    output_file = repo / "output/final results/result.txt"
    output_file.parent.mkdir(parents=True)
    output_file.write_text("source-bound result\n", encoding="utf-8")
    output_file.chmod(0o640)
    (output_file.parent / "latest").symlink_to("result.txt")

    outside = tmp_path / "outside cwd"
    outside.mkdir()
    return backup_script, restore_script, home, outside


@pytest.mark.parametrize("script", [BACKUP_SCRIPT, RESTORE_SCRIPT])
def test_backup_restore_shell_syntax_is_valid(script: Path) -> None:
    result = subprocess.run(
        ["bash", "-n", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync is required by the entry points")
def test_local_full_backup_and_restore_are_layout_and_checksum_consistent(tmp_path: Path) -> None:
    backup_script, restore_script, home, outside = _disposable_scripts_and_sources(tmp_path)
    local_root = tmp_path / "backup target/full"
    scratch_parent = tmp_path / "restore scratch"
    scratch_parent.mkdir()
    snapshot = "2026-08-14-contract"

    backup = _run(
        backup_script,
        "--local-root",
        str(local_root),
        snapshot,
        cwd=outside,
        home=home,
    )

    assert backup.returncode == 0, backup.stderr
    snapshot_root = local_root / snapshot
    assert (snapshot_root / ".hermes/config/config.yaml").read_text(encoding="utf-8") == "profile: test\n"
    assert (snapshot_root / ".cache/search cache/index.db").read_bytes() == b"cache-bytes\x00\x01"
    assert (snapshot_root / "output/final results/result.txt").read_text(encoding="utf-8") == "source-bound result\n"
    assert not (snapshot_root / str(home).removeprefix("/") / ".hermes").exists()
    assert (snapshot_root / ".template-full-backup").read_text(encoding="utf-8") == (
        "format=template-full-backup-v1\n"
        f"snapshot={snapshot}\n"
        "repository_revision=unavailable\n"
        "directory=.hermes\n"
        "directory=.cache\n"
        "directory=output\n"
    )

    first_restore = _run(
        restore_script,
        "--local-root",
        str(local_root),
        "--scratch-parent",
        str(scratch_parent),
        snapshot,
        cwd=outside,
        home=home,
    )

    assert first_restore.returncode == 0, first_restore.stderr
    target_line = next(line for line in first_restore.stdout.splitlines() if line.startswith("Target   : "))
    restored = Path(target_line.removeprefix("Target   : "))
    assert restored.parent.parent == scratch_parent
    assert (restored / ".hermes/config/config.yaml").read_text(encoding="utf-8") == "profile: test\n"
    assert (restored / ".cache/search cache/index.db").read_bytes() == b"cache-bytes\x00\x01"
    restored_output = restored / "output/final results/result.txt"
    assert restored_output.read_text(encoding="utf-8") == "source-bound result\n"
    assert stat.S_IMODE(restored_output.stat().st_mode) == 0o640
    assert (restored_output.parent / "latest").is_symlink()
    assert os.readlink(restored_output.parent / "latest") == "result.txt"
    receipt_line = next(line for line in first_restore.stdout.splitlines() if line.startswith("Receipt  : "))
    receipt = Path(receipt_line.removeprefix("Receipt  : "))
    assert "verification=rsync-checksum-clean" in receipt.read_text(encoding="utf-8")
    assert "exit_status=0" in receipt.read_text(encoding="utf-8")
    control = receipt.parent
    assert stat.S_IMODE(control.stat().st_mode) == 0o700
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    verify_output = control / "rsync-verify.txt"
    assert stat.S_IMODE(verify_output.stat().st_mode) == 0o600
    assert verify_output.read_text(encoding="utf-8") == ""
    assert not Path(f"{restored}.receipt.txt").exists()
    assert not Path(f"{restored}.rsync-verify.txt").exists()

    second_restore = _run(
        restore_script,
        "--local-root",
        str(local_root),
        "--scratch-parent",
        str(scratch_parent),
        snapshot,
        cwd=outside,
        home=home,
    )
    assert second_restore.returncode == 0, second_restore.stderr
    second_target_line = next(line for line in second_restore.stdout.splitlines() if line.startswith("Target   : "))
    second_restored = Path(second_target_line.removeprefix("Target   : "))
    assert second_restored != restored
    assert restored.exists(), "a later restore must not delete or reuse the earlier scratch tree"


@pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync is required by the entry points")
def test_backup_refuses_to_overwrite_an_existing_snapshot(tmp_path: Path) -> None:
    backup_script, _, home, outside = _disposable_scripts_and_sources(tmp_path)
    local_root = tmp_path / "backups/full"
    snapshot = "immutable-snapshot"

    first = _run(backup_script, "--local-root", str(local_root), snapshot, cwd=outside, home=home)
    assert first.returncode == 0, first.stderr
    backed_up_file = local_root / snapshot / "output/final results/result.txt"
    original_bytes = backed_up_file.read_bytes()

    disposable_repo = backup_script.parents[2]
    (disposable_repo / "output/final results/result.txt").write_text("new bytes\n", encoding="utf-8")
    second = _run(backup_script, "--local-root", str(local_root), snapshot, cwd=outside, home=home)

    assert second.returncode != 0
    assert "refusing to overwrite" in second.stderr
    assert backed_up_file.read_bytes() == original_bytes


@pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync is required by the entry points")
def test_restore_list_is_read_only_and_metadata_mismatch_fails_closed(tmp_path: Path) -> None:
    backup_script, restore_script, home, outside = _disposable_scripts_and_sources(tmp_path)
    local_root = tmp_path / "backups/full"
    scratch_parent = tmp_path / "scratch"
    scratch_parent.mkdir()
    snapshot = "listed-snapshot"
    backup = _run(backup_script, "--local-root", str(local_root), snapshot, cwd=outside, home=home)
    assert backup.returncode == 0, backup.stderr

    listing = _run(
        restore_script,
        "--list",
        "--local-root",
        str(local_root),
        "--scratch-parent",
        str(scratch_parent),
        snapshot,
        cwd=outside,
        home=home,
    )
    assert listing.returncode == 0, listing.stderr
    assert ".template-full-backup" in listing.stdout
    assert list(scratch_parent.iterdir()) == []

    metadata = local_root / snapshot / ".template-full-backup"
    metadata.write_text(
        "format=template-full-backup-v1\n"
        "snapshot=different-snapshot\n"
        "repository_revision=unavailable\n"
        "directory=output\n",
        encoding="utf-8",
    )
    rejected = _run(
        restore_script,
        "--local-root",
        str(local_root),
        "--scratch-parent",
        str(scratch_parent),
        snapshot,
        cwd=outside,
        home=home,
    )
    assert rejected.returncode != 0
    assert "mismatched record" in rejected.stderr
    assert list(scratch_parent.iterdir()) == []


@pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync is required by the entry points")
def test_missing_optional_sources_are_declared_in_snapshot_and_receipt(tmp_path: Path) -> None:
    backup_script, restore_script, home, outside = _disposable_scripts_and_sources(tmp_path)
    shutil.rmtree(home / ".hermes")
    shutil.rmtree(backup_script.parents[2] / ".cache")
    local_root = tmp_path / "backups/full"
    scratch_parent = tmp_path / "scratch"
    scratch_parent.mkdir()
    snapshot = "partial-source-set"

    backup = _run(backup_script, "--local-root", str(local_root), snapshot, cwd=outside, home=home)
    assert backup.returncode == 0, backup.stderr
    metadata = (local_root / snapshot / ".template-full-backup").read_text(encoding="utf-8")
    assert "directory=output\n" in metadata
    assert "missing=.hermes\n" in metadata
    assert "missing=.cache\n" in metadata

    restored = _run(
        restore_script,
        "--local-root",
        str(local_root),
        "--scratch-parent",
        str(scratch_parent),
        snapshot,
        cwd=outside,
        home=home,
    )
    assert restored.returncode == 0, restored.stderr
    target_line = next(line for line in restored.stdout.splitlines() if line.startswith("Target   : "))
    target = Path(target_line.removeprefix("Target   : "))
    assert (target / "output/final results/result.txt").is_file()
    assert not (target / ".hermes").exists()
    assert not (target / ".cache").exists()
    receipt_line = next(line for line in restored.stdout.splitlines() if line.startswith("Receipt  : "))
    receipt = Path(receipt_line.removeprefix("Receipt  : ")).read_text(encoding="utf-8")
    assert "missing=.hermes\n" in receipt
    assert "missing=.cache\n" in receipt


@pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync is required by the entry points")
def test_restore_rejects_scratch_inside_backup_namespace_without_mutation(tmp_path: Path) -> None:
    backup_script, restore_script, home, outside = _disposable_scripts_and_sources(tmp_path)
    local_root = tmp_path / "backups/full"
    snapshot = "overlap-guard"
    backup = _run(backup_script, "--local-root", str(local_root), snapshot, cwd=outside, home=home)
    assert backup.returncode == 0, backup.stderr
    snapshot_root = local_root / snapshot
    before = _tree_state(snapshot_root)

    rejected = _run(
        restore_script,
        "--local-root",
        str(local_root),
        "--scratch-parent",
        str(snapshot_root),
        snapshot,
        cwd=outside,
        home=home,
    )

    assert rejected.returncode == 2
    assert "must be outside the local backup root" in rejected.stderr
    assert _tree_state(snapshot_root) == before


@pytest.mark.skipif(not RSYNC_AVAILABLE, reason="rsync is required by the entry points")
def test_concurrent_same_name_backups_have_one_writer_and_no_nested_partial(tmp_path: Path) -> None:
    backup_script, _, home, outside = _disposable_scripts_and_sources(tmp_path)
    large_source = backup_script.parents[2] / "output/large.bin"
    large_source.write_bytes(b"x" * (16 * 1024 * 1024))
    local_root = tmp_path / "backups/full"
    snapshot = "concurrent-writers"
    command = ["bash", str(backup_script), "--local-root", str(local_root), snapshot]
    process_one = subprocess.Popen(
        command,
        cwd=outside,
        env=_subprocess_env(home),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    process_two = subprocess.Popen(
        command,
        cwd=outside,
        env=_subprocess_env(home),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout_one, stderr_one = process_one.communicate(timeout=30)
    stdout_two, stderr_two = process_two.communicate(timeout=30)

    results = [
        (process_one.returncode, stdout_one, stderr_one),
        (process_two.returncode, stdout_two, stderr_two),
    ]
    assert sum(returncode == 0 for returncode, _, _ in results) == 1, results
    loser = next(result for result in results if result[0] != 0)
    assert "locked by another writer" in loser[2] or "refusing to overwrite" in loser[2]
    final_root = local_root / snapshot
    assert (final_root / "output/large.bin").stat().st_size == 16 * 1024 * 1024
    assert not any(path.name.startswith(f".{snapshot}.partial") for path in final_root.rglob("*"))
    assert not (local_root / f".{snapshot}.lock").exists()


@pytest.mark.parametrize(
    "hostile_home",
    ["relative-home", "host:path", "/tmp/absolute:colon", "/tmp/line\nbreak", "/"],
)
def test_backup_rejects_ambiguous_or_broad_home(tmp_path: Path, hostile_home: str) -> None:
    backup_script, _, _, outside = _disposable_scripts_and_sources(tmp_path)
    (outside / "host:path/.hermes").mkdir(parents=True)
    result = _run(
        backup_script,
        "--dry-run",
        "research-backup",
        "safe-snapshot",
        cwd=outside,
        home=hostile_home,
    )
    assert result.returncode == 2
    assert "HOME must be an absolute directory" in result.stderr


def test_remote_dry_run_separates_ssh_path_from_rsync_address_and_rejects_injection(tmp_path: Path) -> None:
    backup_script, _, home, outside = _disposable_scripts_and_sources(tmp_path)

    planned = _run(
        backup_script,
        "--dry-run",
        "research-backup",
        "safe-snapshot",
        cwd=outside,
        home=home,
    )
    assert planned.returncode == 0, planned.stderr
    assert "Remote filesystem path: backups/full/safe-snapshot" in planned.stdout
    assert "Remote filesystem path: research-backup:" not in planned.stdout
    assert "Rsync target          : research-backup:backups/full/safe-snapshot" in planned.stdout
    assert "no SSH or rsync command was run" in planned.stdout

    hostile_remote = _run(
        backup_script,
        "--dry-run",
        "backup -oProxyCommand=bad",
        "safe-snapshot",
        cwd=outside,
        home=home,
    )
    assert hostile_remote.returncode == 2
    assert "Invalid remote host" in hostile_remote.stderr

    traversal = _run(
        backup_script,
        "--dry-run",
        "research-backup",
        "../escape",
        cwd=outside,
        home=home,
    )
    assert traversal.returncode == 2
    assert "Invalid snapshot name" in traversal.stderr
