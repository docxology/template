"""Committed-publication and receipt parity checks for standalone mirrors.

These predicates verify an actual destination commit against the reviewed
publication update, and re-derive the whole export before promotion. They own
no materialization; ``standalone_mirror`` supplies the export under check.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.publishing._standalone_git import _git, _git_head_status
from infrastructure.publishing._standalone_mirror_source import (
    _verify_committed,
    clean_source_revision,
)
from infrastructure.publishing.publication_tree import (
    INVENTORY_NAME,
    PublicationUpdate,
    _Budget,
    publication_export_sha256,
)

if TYPE_CHECKING:
    from infrastructure.publishing.standalone_install_projection import GitInstallProvider


def _assert_source_current(
    repo_root: Path,
    project_rel: str,
    revision: str,
    export_sha256: str,
    scratch: Path,
    *,
    install_projection: bool = False,
    meta_provider: GitInstallProvider | None = None,
) -> None:
    from infrastructure.publishing.standalone_mirror import populate_mirror_tree

    with tempfile.TemporaryDirectory(prefix="source-recheck-", dir=scratch) as temporary:
        private = Path(temporary).resolve(strict=True)
        verification = private / "canonical" if install_projection else private
        populate_mirror_tree(repo_root, project_rel, verification, source_revision=revision)
        if install_projection:
            from infrastructure.publishing.standalone_install_projection import (
                GitInstallProvider,
                project_standalone_installation,
            )

            projected = private / "projected"
            project_standalone_installation(
                verification,
                projected,
                root_provider=GitInstallProvider(repo_root, revision),
                meta_provider=meta_provider,
            )
            verification = projected
        if publication_export_sha256(verification) != export_sha256:
            raise ValueError("whole standalone export changed before promotion")
    clean_source_revision(repo_root, revision)


def validate_publication_commit(destination: Path, update: PublicationUpdate, revision: str) -> None:
    """Verify actual committed managed bytes and names, including ignored-file failures."""
    budget = _Budget()
    tree = _git(["ls-tree", "-r", "-z", revision, "--"], cwd=destination).stdout
    committed: dict[str, tuple[str, str]] = {}
    for entry in tree.split("\0"):
        if entry:
            budget.check()
            header, path = entry.split("\t", 1)
            mode, kind, identity = header.split(" ")
            if kind != "blob" or len(committed) >= budget.limits.max_files:
                raise ValueError("publication commit contains an unsupported or excessive tree")
            committed[path] = mode, identity
    managed = {
        name
        for name, record in update.plan["observed_managed_files"].items()
        if record is not None and name not in update.removed
    } | update.plan["desired_export_files"].keys()
    if committed.keys() != managed | set(update.plan["destination_only"]) | {INVENTORY_NAME}:
        raise ValueError("publication commit names differ from the reviewed destination export")
    root_metadata = destination.stat()
    root_identity = root_metadata.st_dev, root_metadata.st_ino
    for relative in sorted(managed | {INVENTORY_NAME}):
        content = read_bytes_confined(
            destination, destination / relative, max_bytes=64 * 1024 * 1024, expected_root_identity=root_identity
        )
        budget.check(len(content))
        mode = "100755" if (destination / relative).stat().st_mode & 0o111 else "100644"
        _verify_committed(relative, content, mode, committed)
    head, _, status = _git_head_status(destination)
    if head != revision:
        raise ValueError("publication destination HEAD changed before push")
    if status.strip():
        raise ValueError("publication destination changed after its commit")


def _classify(status_output: str) -> tuple[int, int, int]:
    added = modified = deleted = 0
    for line in status_output.splitlines():
        if not line.strip():
            continue
        code = line[:2]
        if code.startswith("A") or code.startswith("?"):
            added += 1
        elif code.startswith("D"):
            deleted += 1
        else:
            modified += 1
    return added, modified, deleted
