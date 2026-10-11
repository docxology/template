"""Actual retained publication files, reviewed removals and bare-Git parity."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.publishing.publication_tree import (
    INVENTORY_NAME,
    PublicationLimits,
    PublicationTarget,
    prepare_removal_plan,
    restore_publication_quarantine,
    review_plan_sha256,
    update_publication_tree,
    validate_publication_update,
)
from infrastructure.publishing.static_site.github_pages import _credential_environment, _publish_tree

pytestmark = pytest.mark.timeout(120)
TARGET = PublicationTarget("https://github.com/example/owned-publication-fixture", "gh-pages")


def _trees(tmp_path: Path) -> tuple[Path, Path, Path]:
    source, destination, quarantine = (tmp_path / name for name in ("source", "destination", "retained-quarantine"))
    for path in (source, destination, quarantine):
        path.mkdir()
    (source / "src").mkdir()
    (source / "README.md").write_text("current public example\n")
    (source / "src/retired.py").write_text("ORIGINAL_PUBLIC_BYTES = 17\n")
    (source / "src/retired.py").chmod(0o755)
    update_publication_tree(source, destination, TARGET)
    (source / "src/retired.py").unlink()
    return source, destination, quarantine


def _backup(quarantine: Path) -> Path:
    journals = tuple(quarantine.glob("*.json"))
    assert len(journals) == 1
    journal = json.loads(journals[0].read_text())
    return quarantine / journal["quarantine"]


def test_unreviewed_stale_files_refuse_parity_and_keep_ownership(tmp_path: Path) -> None:
    source, destination, quarantine = _trees(tmp_path)
    observed = update_publication_tree(source, destination, TARGET)
    assert observed.stale_managed == ("src/retired.py",)
    assert not observed.managed_export_parity and not observed.exact_tree_parity
    assert (destination / "src/retired.py").read_text() == "ORIGINAL_PUBLIC_BYTES = 17\n"
    assert "src/retired.py" in json.loads((destination / INVENTORY_NAME).read_text())["files"]
    assert not tuple(quarantine.iterdir())


def test_reviewed_removal_has_exact_export_parity_and_verified_rollback(tmp_path: Path) -> None:
    source, destination, quarantine = _trees(tmp_path)
    plan = prepare_removal_plan(source, destination, TARGET)
    digest = review_plan_sha256(plan)
    observed = update_publication_tree(
        source, destination, TARGET, removal_plan=plan, reviewed_plan_sha256=digest, quarantine_root=quarantine
    )
    assert observed.removed == ("src/retired.py",)
    assert observed.managed_export_parity and observed.exact_tree_parity
    assert not (destination / "src/retired.py").exists()
    backup = _backup(quarantine)
    assert (backup / "src/retired.py").read_text() == "ORIGINAL_PUBLIC_BYTES = 17\n"
    assert (backup / "src/retired.py").stat().st_mode & 0o111
    assert restore_publication_quarantine(destination, backup, TARGET, plan, digest) == ("src/retired.py",)
    assert (destination / "src/retired.py").read_bytes() == (backup / "src/retired.py").read_bytes()
    assert (destination / "src/retired.py").stat().st_ino != (backup / "src/retired.py").stat().st_ino
    (destination / "src/retired.py").write_text("later in-place destination edit\n")
    assert (backup / "src/retired.py").read_text() == "ORIGINAL_PUBLIC_BYTES = 17\n"


@pytest.mark.parametrize("location", ["source", "destination", "inventory"])
def test_casefold_inventory_aliases_refuse_before_mutation(tmp_path: Path, location: str) -> None:
    source, destination, quarantine = _trees(tmp_path)
    original = (destination / "README.md").read_bytes()
    alias = INVENTORY_NAME.upper()
    if location == "inventory":
        payload = json.loads((destination / INVENTORY_NAME).read_text())
        payload["files"][alias] = {"sha256": "0" * 64, "mode": 0o644}
        (destination / INVENTORY_NAME).write_text(json.dumps(payload))
    else:
        root = source if location == "source" else destination
        if location == "destination":
            # Renaming works on both case-sensitive and case-insensitive hosts.
            (root / INVENTORY_NAME).rename(root / alias)
        else:
            (root / alias).write_bytes(b"untrusted sidecar alias\n")
    inventory_before = {path.name: path.read_bytes() for path in destination.glob("*.json")}
    with pytest.raises(ValueError, match="canonical public|aliases are reserved"):
        update_publication_tree(source, destination, TARGET)
    assert (destination / "README.md").read_bytes() == original
    assert {path.name: path.read_bytes() for path in destination.glob("*.json")} == inventory_before
    assert not tuple(quarantine.iterdir())


@pytest.mark.parametrize("fault", ["added", "managed-bytes", "ownership"])
def test_actual_child_destination_drift_refuses_promotion(tmp_path: Path, fault: str) -> None:
    source, destination, _ = _trees(tmp_path)
    observed = update_publication_tree(source, destination, TARGET)
    path = (
        destination / {"added": "concurrent-record", "managed-bytes": "README.md", "ownership": INVENTORY_NAME}[fault]
    )
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(b'child change\\n')",
            str(path),
        ],
        check=True,
        timeout=10,
    )
    with pytest.raises((ValueError, json.JSONDecodeError)):
        validate_publication_update(destination, TARGET, observed)
    assert path.read_bytes() == b"child change\n"


def test_completed_removal_changes_state_and_refuses_approval_replay(tmp_path: Path) -> None:
    source, destination, quarantine = _trees(tmp_path)
    plan = prepare_removal_plan(source, destination, TARGET)
    digest = review_plan_sha256(plan)
    update_publication_tree(
        source, destination, TARGET, removal_plan=plan, reviewed_plan_sha256=digest, quarantine_root=quarantine
    )
    with pytest.raises(ValueError, match="exact current plan"):
        update_publication_tree(
            source, destination, TARGET, removal_plan=plan, reviewed_plan_sha256=digest, quarantine_root=quarantine
        )
    assert not (destination / "src/retired.py").exists()
    assert (_backup(quarantine) / "src/retired.py").read_text() == "ORIGINAL_PUBLIC_BYTES = 17\n"


@pytest.mark.parametrize(
    "fault",
    ["missing-sha", "wrong-sha", "wrong-destination", "changed-source", "changed-destination", "invented-removal"],
)
def test_invalid_or_stale_review_cannot_remove_real_files(tmp_path: Path, fault: str) -> None:
    source, destination, quarantine = _trees(tmp_path)
    plan = prepare_removal_plan(source, destination, TARGET)
    digest = review_plan_sha256(plan)
    if fault == "missing-sha":
        digest = None
    elif fault == "wrong-sha":
        digest = "0" * 64
    elif fault == "wrong-destination":
        plan["destination"]["branch"] = "another-reviewed-branch"
        digest = review_plan_sha256(plan)
    elif fault == "changed-source":
        (source / "README.md").write_text("different desired export\n")
    elif fault == "changed-destination":
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                "import pathlib,sys;pathlib.Path(sys.argv[1]).write_text('actual child replacement\\n')",
                str(destination / "src/retired.py"),
            ],
            check=True,
            timeout=10,
        )
    else:
        (destination / "unrelated-record.json").write_text("preserve this unrelated evidence\n")
        plan["removals"]["unrelated-record.json"] = copy.deepcopy(plan["removals"]["src/retired.py"])
        digest = review_plan_sha256(plan)
    preserved = (destination / "src/retired.py").read_bytes()
    with pytest.raises(ValueError):
        update_publication_tree(
            source, destination, TARGET, removal_plan=plan, reviewed_plan_sha256=digest, quarantine_root=quarantine
        )
    assert (destination / "src/retired.py").read_bytes() == preserved
    assert not tuple(quarantine.iterdir())


@pytest.mark.parametrize(
    "relative",
    [
        "output/data/frozen.json",
        "history/release.json",
        "deposits/version.json",
        "registrations/old.json",
        "frozen_record.json",
        "published.pdf",
    ],
)
def test_previously_owned_immutable_publication_evidence_is_retained(tmp_path: Path, relative: str) -> None:
    source, destination, quarantine = _trees(tmp_path)
    original = source / relative
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_bytes(b"invented immutable public receipt\n")
    update_publication_tree(source, destination, TARGET)
    original.unlink()
    plan = prepare_removal_plan(source, destination, TARGET)
    assert relative in plan["retained_immutable"]
    assert relative not in plan["removals"]
    observed = update_publication_tree(
        source,
        destination,
        TARGET,
        removal_plan=plan,
        reviewed_plan_sha256=review_plan_sha256(plan),
        quarantine_root=quarantine,
    )
    assert (destination / relative).read_bytes() == b"invented immutable public receipt\n"
    assert relative in observed.preserved and not observed.exact_tree_parity


@pytest.mark.skipif(os.name == "nt", reason="POSIX FIFO proves unknown evidence bytes are never opened")
def test_destination_only_fifo_and_symlink_are_preserved_without_reading(tmp_path: Path) -> None:
    source, destination, _ = _trees(tmp_path)
    fifo = destination / "unrelated-public-record"
    os.mkfifo(fifo)
    outside = tmp_path / "invented-outside-evidence"
    outside.write_bytes(b"untouched unrelated bytes\n")
    (destination / "unrelated-link").symlink_to(outside)
    observed = update_publication_tree(source, destination, TARGET)
    assert {"unrelated-public-record", "unrelated-link"} <= set(observed.preserved)
    assert fifo.exists() and (destination / "unrelated-link").is_symlink()
    assert outside.read_bytes() == b"untouched unrelated bytes\n"


def test_rollback_refuses_concurrent_target_and_tampered_backup(tmp_path: Path) -> None:
    source, destination, quarantine = _trees(tmp_path)
    plan = prepare_removal_plan(source, destination, TARGET)
    digest = review_plan_sha256(plan)
    update_publication_tree(
        source, destination, TARGET, removal_plan=plan, reviewed_plan_sha256=digest, quarantine_root=quarantine
    )
    backup = _backup(quarantine)
    target = destination / "src/retired.py"
    target.write_text("concurrent independent public edit\n")
    with pytest.raises(ValueError, match="occupied target"):
        restore_publication_quarantine(destination, backup, TARGET, plan, digest)
    assert target.read_text() == "concurrent independent public edit\n"
    assert (backup / "src/retired.py").read_text() == "ORIGINAL_PUBLIC_BYTES = 17\n"
    (backup / "src/retired.py").write_text("changed rollback bytes\n")
    with pytest.raises(ValueError, match="rollback bytes"):
        restore_publication_quarantine(destination, backup, TARGET, plan, digest)
    assert target.read_text() == "concurrent independent public edit\n"


@pytest.mark.parametrize(
    "relative", ["history/release.json", "deposits/version.json", "registration/frozen.json", "frozen_record.json"]
)
def test_changed_desired_frozen_history_cannot_overwrite_published_bytes(tmp_path: Path, relative: str) -> None:
    source, destination, _ = _trees(tmp_path)
    source_record = source / relative
    source_record.parent.mkdir(parents=True, exist_ok=True)
    source_record.write_text("original immutable receipt\n")
    update_publication_tree(source, destination, TARGET)
    source_record.write_text("different proposed frozen bytes\n")
    with pytest.raises(ValueError, match="cannot be overwritten"):
        update_publication_tree(source, destination, TARGET)
    assert (destination / relative).read_text() == "original immutable receipt\n"


def test_current_renderer_output_updates_without_removing_prior_publications(tmp_path: Path) -> None:
    source, destination, _ = _trees(tmp_path)
    output = source / "output/current.pdf"
    output.parent.mkdir()
    output.write_bytes(b"old current render\n")
    update_publication_tree(source, destination, TARGET)
    output.write_bytes(b"new current render\n")
    update_publication_tree(source, destination, TARGET)
    assert (destination / "output/current.pdf").read_bytes() == b"new current render\n"


@pytest.mark.parametrize(
    "limits",
    [
        PublicationLimits(timeout_seconds=0),
        PublicationLimits(timeout_seconds=1e-12),
        PublicationLimits(max_files=1),
        PublicationLimits(max_depth=1),
        PublicationLimits(max_total_bytes=1),
    ],
)
def test_actual_tree_limits_refuse_work_before_source_changes(tmp_path: Path, limits: PublicationLimits) -> None:
    source, destination, _ = _trees(tmp_path)
    (source / "deep/nested").mkdir(parents=True)
    (source / "deep/nested/fixture.txt").write_text("bounded public bytes\n")
    original = (destination / "README.md").read_bytes()
    with pytest.raises(ValueError, match="finite|limit|budget"):
        update_publication_tree(source, destination, TARGET, limits=limits)
    assert (destination / "README.md").read_bytes() == original
    assert not (destination / "deep/nested/fixture.txt").exists()


@pytest.mark.parametrize("fault", ["inventory-link", "managed-parent-link", "private-inventory", "git-inventory"])
def test_unsafe_ownership_or_ancestors_never_follow_outside_bytes(tmp_path: Path, fault: str) -> None:
    source, destination, _ = _trees(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "retired.py").write_text("unrelated outside bytes\n")
    if fault == "inventory-link":
        (outside / "inventory.json").write_text("unrelated JSON\n")
        (destination / INVENTORY_NAME).unlink()
        (destination / INVENTORY_NAME).symlink_to(outside / "inventory.json")
    elif fault == "managed-parent-link":
        (destination / "src/retired.py").unlink()
        (destination / "src").rmdir()
        (destination / "src").symlink_to(outside, target_is_directory=True)
    else:
        inventory = json.loads((destination / INVENTORY_NAME).read_text())
        relative = ".env" if fault == "private-inventory" else ".GIT/config"
        inventory["files"][relative] = {"sha256": "0" * 64, "mode": 0o644}
        (destination / INVENTORY_NAME).write_text(json.dumps(inventory))
    with pytest.raises((OSError, ValueError)):
        prepare_removal_plan(source, destination, TARGET)
    assert (outside / "retired.py").read_text() == "unrelated outside bytes\n"


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=20
    ).stdout.strip()


def test_real_pages_rejects_unreviewed_stale_source_then_preserves_history_on_removal(tmp_path: Path) -> None:
    source, _, quarantine = _trees(tmp_path)
    (source / "retired.html").write_text("prior public page\n")
    bare = tmp_path / "owned-remote.git"
    _git(["init", "--bare", str(bare)], tmp_path)
    _git(["config", "receive.denyNonFastForwards", "true"], bare)
    first = tmp_path / "first"
    first.mkdir()
    with _credential_environment("invented-only-test-token", first) as env:
        _publish_tree(source, str(bare), "gh-pages", first, env, target=TARGET)
    original = _git(["rev-parse", "refs/heads/gh-pages"], bare)
    (source / "retired.html").unlink()
    second = tmp_path / "second"
    second.mkdir()
    with _credential_environment("invented-only-test-token", second) as env:
        with pytest.raises(ValueError, match="reviewed removal manifest"):
            _publish_tree(source, str(bare), "gh-pages", second, env, target=TARGET)
    assert _git(["rev-parse", "refs/heads/gh-pages"], bare) == original
    plan = prepare_removal_plan(source, first / "pages", TARGET)
    final = tmp_path / "final"
    final.mkdir()
    with _credential_environment("invented-only-test-token", final) as env:
        observed = _publish_tree(
            source,
            str(bare),
            "gh-pages",
            final,
            env,
            target=TARGET,
            removal_plan=plan,
            reviewed_plan_sha256=review_plan_sha256(plan),
            quarantine_root=quarantine,
        )
    assert observed.managed_export_parity and observed.removed == ("retired.html",)
    current = _git(["rev-parse", "refs/heads/gh-pages"], bare)
    _git(["merge-base", "--is-ancestor", original, current], bare)
    assert _git(["show", f"{original}:retired.html"], bare) == "prior public page"
    assert "retired.html" not in _git(["ls-tree", "-r", "--name-only", current], bare).splitlines()
    assert (_backup(quarantine) / "retired.html").read_text() == "prior public page\n"


def test_real_pages_post_commit_pushurl_change_cannot_publish_unreviewed_remote(tmp_path: Path) -> None:
    source, _, _ = _trees(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    admitted, other = tmp_path / "admitted.git", tmp_path / "unreviewed.git"
    _git(["init", "--bare", str(admitted)], tmp_path)
    with _credential_environment("invented-owned-test-token", first) as env:
        _publish_tree(source, str(admitted), "gh-pages", first, env, target=TARGET)
    original = _git(["rev-parse", "refs/heads/gh-pages"], admitted)
    _git(["clone", "--bare", str(admitted), str(other)], tmp_path)
    native = shutil.which("git")
    assert native is not None
    tools = tmp_path / "native-transport"
    tools.mkdir()
    marker = tools / "actual-commit"
    shim = tools / "git"
    shim.write_text(
        f"#!{sys.executable}\nimport pathlib,os,subprocess,sys\n"
        f"native={native!r}\nargs=sys.argv[1:]\n"
        "if 'commit' in args:\n"
        "    completed=subprocess.run([native,*args],check=False,timeout=20)\n"
        "    if completed.returncode==0:\n"
        f"        pathlib.Path({str(marker)!r}).write_text('actual native commit\\n')\n"
        f"        subprocess.run([native,'config','remote.origin.pushurl',{str(other)!r}],check=True,timeout=20)\n"
        "    raise SystemExit(completed.returncode)\n"
        "os.execv(native,[native,*args])\n"
    )
    shim.chmod(0o755)
    (source / "README.md").write_text("new admitted public source\n")
    with _credential_environment("invented-owned-test-token", second) as env:
        env["PATH"] = str(tools) + os.pathsep + env.get("PATH", "")
        with pytest.raises(ValueError, match="origin push destination differs"):
            _publish_tree(source, str(admitted), "gh-pages", second, env, target=TARGET)
    assert marker.read_text() == "actual native commit\n"
    assert _git(["rev-parse", "refs/heads/gh-pages"], admitted) == original
    assert _git(["rev-parse", "refs/heads/gh-pages"], other) == original
