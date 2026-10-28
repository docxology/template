"""Mirror public exemplars from the monorepo into their standalone repositories.

The monorepo is the render source of truth; each public exemplar also has a
standalone GitHub repository that serves as its publication mirror (see
``docs/guides/publication-runbook.md``). This module keeps those mirrors current.

Two properties are load-bearing, and both were learned by nearly getting them
wrong on 2026-07-28:

**Retained evidence.** Destination-only files and immutable publication evidence
survive synchronization. Previously managed obsolete source files require an
exact destination-bound removal plan and its explicitly reviewed hash. Without
that authority, synchronization reports the stale files and refuses a push.
Approved removals go to retained local quarantine, with verified rollback;
publication history is never cleared. See ``publication-removals.md``.

**Symlinks are dereferenced.** Some exemplars share source by symlinking into a
sibling exemplar (``template_advanced_literature_review/src/analysis ->
../../template_literature_meta_analysis/src/analysis``). A standalone repository
has no sibling, so copying the link would leave it dangling — which is exactly
why that mirror was missing four entire source trees. Directory symlinks are
expanded into their tracked contents.

The file list always comes from ``git ls-files``, so untracked local noise
(``htmlcov/``, ``dist/``, ``.codegraph``, ``.venv``) can never reach a mirror.
"""

from __future__ import annotations

import hashlib
import re
import os
import stat
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.pipeline.fingerprint_files import observation
from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES as PUBLIC_FOND_NAMES
from infrastructure.project.copy_exemplar import (
    _declared_resource_dependencies,
    _is_clean_resource_path,
    _is_clean_source_path,
)
from infrastructure.project.public_reference_git import GitReference, inventory
from infrastructure.publishing._standalone_export import canonical_snapshot_export
from infrastructure.publishing._standalone_git import (
    _GIT_LOCAL_ENVIRONMENT as _GIT_LOCAL_ENVIRONMENT,
    _PUBLIC_ROOTS as _PUBLIC_ROOTS,
    _git as _git,
    _git_clean_source_inventory as _git_clean_source_inventory,
    _git_destination_inventory as _git_destination_inventory,
    _git_environment as _git_environment,
    _git_source_inventory as _git_source_inventory,
)
from infrastructure.publishing._standalone_mirror_source import (
    _bound_source,
    _committed_files,
    _project_root,
    _public_source,
    _tracked_paths,
    _verify_committed,
    clean_source_revision,
    declared_repository,
)
from infrastructure.publishing._standalone_mirror_verify import (
    _assert_source_current,
    _classify,
    validate_publication_commit,
)
from infrastructure.rules.public_scope import PUBLIC_RULE_NAMES as PUBLIC_RULE_NAMES
from infrastructure.tools.public_scope import PUBLIC_TOOL_NAMES as PUBLIC_TOOL_NAMES
from infrastructure.publishing.publication_tree import (
    PublicationTarget,
    _Budget,
    publication_export_sha256,
    review_plan_sha256,
    update_publication_tree,
    validate_publication_update,
)

if TYPE_CHECKING:
    from infrastructure.publishing.standalone_install_projection import GitInstallProvider


@dataclass(frozen=True)
class MirrorResult:
    """Outcome of syncing one exemplar into its standalone repository."""

    exemplar: str
    repository: str
    status: str
    added: int = 0
    modified: int = 0
    deleted: int = 0
    commit: str = ""
    managed_export_parity: bool = False
    preserved_files: tuple[str, ...] = ()
    removal_plan: dict[str, Any] | None = None
    removal_plan_sha256: str = ""
    source_commit: str = ""
    export_kind: str = "source"
    source_export_sha256: str = ""
    install_projection_sha256: str = ""

    @property
    def changed(self) -> int:
        """Total number of files the sync would write."""
        return self.added + self.modified + self.deleted


def validate_git_destination(
    admitted: str, git: Callable[[list[str]], subprocess.CompletedProcess[str]], *, require_origin: bool = True
) -> None:
    """Resolve actual Git URL rewriting and refuse mutable-origin redirection."""
    if not admitted or any(character in admitted for character in "\r\n\0"):
        raise ValueError("publication transport must have one exact admitted destination")
    probe = f"template-admission-{uuid.uuid4().hex}"
    # get-url requires a repository-configured remote. The verbose inventory
    # resolves command-owned fetch and push URLs without editing local config.
    inventory = git(["-c", f"remote.{probe}.url={admitted}", "remote", "-v"]).stdout.splitlines()
    _validate_destination_inventory(admitted, probe, inventory)
    if require_origin and git(["remote", "get-url", "--push", "--all", "origin"]).stdout.splitlines() != [admitted]:
        raise ValueError("Git origin push destination differs from the admitted publication target")


def _validate_destination_inventory(admitted: str, probe: str, inventory: list[str]) -> None:
    effective = [line for line in inventory if line.startswith(probe + "\t")]
    expected = [f"{probe}\t{admitted} (fetch)", f"{probe}\t{admitted} (push)"]
    if sorted(effective) != sorted(expected):
        raise ValueError("Git rewrites the admitted publication destination; promotion refused")


def _validate_git_destination_current(admitted: str, cwd: Path) -> None:
    """Keep the same routing predicates in a fresh adjacent-read guardian cohort."""
    if not admitted or any(character in admitted for character in "\r\n\0"):
        raise ValueError("publication transport must have one exact admitted destination")
    probe = f"template-admission-{uuid.uuid4().hex}"
    inventory, origin = _git_destination_inventory(cwd, admitted, probe)
    _validate_destination_inventory(admitted, probe, inventory.splitlines())
    if origin is None:
        raise ValueError("native Git admission observer refused otherwise valid destination routing")
    if origin.splitlines() != [admitted]:
        raise ValueError("Git origin push destination differs from the admitted publication target")


def push_admitted_commit(
    destination: Path, admitted: str, revision: str, branch: str, *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Push exact verified objects through fresh routing configuration and scoped credentials."""
    PublicationTarget("https://github.com/example/identity-check", branch).payload()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("publication push requires its verified full commit identity")
    credentials: list[tuple[str, str]] = []
    if env is None:
        configured = _git(["config", "--null", "--get-urlmatch", "credential", admitted], cwd=destination, check=False)
        if configured.returncode not in {0, 1}:
            raise ValueError("publication credential configuration could not be admitted")
        for entry in configured.stdout.split("\0"):
            if entry:
                key, value = entry.split("\n", 1)
                if not key.casefold().startswith("credential."):
                    raise ValueError("publication credential snapshot contains an unrelated setting")
                credentials.append((key, value))
    process_env = dict(env) if env is not None else build_bounded_env()
    for name in tuple(process_env):
        if name in _GIT_LOCAL_ENVIRONMENT or name.startswith(("GIT_TRACE", "GIT_CONFIG")):
            process_env.pop(name)
    process_env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    )
    credentials.insert(0, ("credential.helper", ""))
    process_env["GIT_CONFIG_COUNT"] = str(len(credentials))
    for index, (key, value) in enumerate(credentials):
        process_env[f"GIT_CONFIG_KEY_{index}"] = key
        process_env[f"GIT_CONFIG_VALUE_{index}"] = value
    git_dir = destination / ".git"
    if (
        git_dir.resolve(strict=True) != git_dir.absolute()
        or not (git_dir / "objects").is_dir()
        or (git_dir / "objects").resolve(strict=True) != (git_dir / "objects").absolute()
    ):
        raise ValueError("publication object store must be the real owned checkout")

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        result = run_bounded_subprocess(
            ["git", "--no-replace-objects", *args], cwd=destination, env=process_env, timeout=60
        )
        return subprocess.CompletedProcess(
            args, result.returncode, result.stdout, result.stderr or result.command_error
        )

    with tempfile.TemporaryDirectory(prefix="publication-push-") as temporary:
        private = Path(temporary).resolve(strict=True)
        initialized = run(
            [
                "-c",
                "init.templateDir=",
                "init",
                "--bare",
                f"--object-format={'sha256' if len(revision) == 64 else 'sha1'}",
                str(private),
            ]
        )
        if initialized.returncode != 0:
            raise ValueError("publication push could not create its private Git configuration")
        shallow = git_dir / "shallow"
        if shallow.exists() or shallow.is_symlink():
            content = read_bytes_confined(git_dir, shallow, max_bytes=1024 * 1024)
            if any(not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", line) for line in content.splitlines()):
                raise ValueError("publication shallow boundary contains invalid commit identities")
            atomic_write_bytes_confined(private, private / "shallow", content)
        process_env["GIT_OBJECT_DIRECTORY"] = str(git_dir / "objects")
        return run([f"--git-dir={private}", "push", "--", admitted, f"{revision}:refs/heads/{branch}"])


def populate_mirror_tree(
    repo_root: Path, project_rel: str, destination: Path, *, source_revision: str | None = None
) -> int:
    """Copy the complete canonical export, including declared public resources.

    Returns the number of files written. Existing files in *destination* that the
    canonical export does not contain are left untouched. The default is an explicitly
    unbound local export; publication supplies an admitted commit and verifies
    every consumed provider byte/mode and link against its actual Git tree.
    """
    budget = _Budget()
    repo_root = repo_root.resolve()
    project_root = _project_root(repo_root, project_rel)
    destination = destination.absolute()
    listed = None
    if source_revision is None:
        tracked_paths = _tracked_paths(repo_root, ".")
    else:
        source_revision, tracked_paths, listed = _git_clean_source_inventory(repo_root, source_revision)
    tracked = frozenset(tracked_paths)
    if len(tracked) > budget.limits.max_files:
        raise ValueError("tracked mirror input exceeds its finite entry limit")
    root_stat = repo_root.stat()
    root_identity = (root_stat.st_dev, root_stat.st_ino)
    pinned: list[GitReference] = []
    committed = (
        _committed_files(repo_root, source_revision, budget, listed=listed, pinned=pinned)
        if source_revision is not None
        else None
    )
    if pinned:
        tracked = tracked | frozenset(committed or {})
        if len(tracked) > budget.limits.max_files:
            raise ValueError("expanded tracked mirror input exceeds its finite entry limit")
    resource_inventories: dict[str, tuple[Path, ...]] = {}
    held_providers: dict[Path, tuple[Path, tuple[int, ...], tuple[int, ...], str, int, tuple[Path, ...]]] = {}
    held_directories: dict[Path, tuple[int, int]] = {repo_root: root_identity} if pinned else {}
    copied_files = 0

    def hold_directories(path: Path) -> None:
        for directory in path.parents:
            budget.check()
            current = directory.lstat()
            identity = current.st_dev, current.st_ino
            if not stat.S_ISDIR(current.st_mode) or held_directories.setdefault(directory, identity) != identity:
                raise ValueError("pinned mirror provider directory changed during admission")
            if directory == repo_root:
                return
        raise ValueError("pinned mirror provider has no admitted source root")

    def copy_source(
        source: Path,
        target: Path,
        snapshot: Path,
        depth: int = 0,
        *,
        provider_roots: tuple[Path, ...] = _PUBLIC_ROOTS,
        resource: str | None = None,
    ) -> int:
        nonlocal copied_files
        budget.check()
        if depth > 16 or any(part.casefold() == ".git" for part in target.relative_to(snapshot).parts):
            raise ValueError("Mirror refuses recursive links or Git control files")
        initial = source.lstat()
        resolved = (
            _bound_source(repo_root, source, committed, budget, provider_roots)
            if committed is not None
            else _public_source(repo_root, source, provider_roots)
        )
        relative = resolved.relative_to(repo_root)
        if resolved.is_dir():
            if not stat.S_ISLNK(initial.st_mode):
                raise ValueError("Tracked mirror directories must be declared symbolic providers")
            children = sorted(path for path in tracked if Path(path).is_relative_to(relative))
            if not children:
                raise ValueError("Mirror provider has no tracked public contents")
            count = 0
            for path in children:
                target_child = target / Path(path).relative_to(relative)
                selected = (
                    _is_clean_resource_path(target_child.relative_to(snapshot / resource), resource)
                    if resource is not None
                    else _is_clean_source_path(target_child.relative_to(snapshot / project_rel))
                )
                if selected:
                    count += copy_source(
                        repo_root / path,
                        target_child,
                        snapshot,
                        depth + 1,
                        provider_roots=provider_roots,
                        resource=resource,
                    )
        else:
            if relative.as_posix() not in tracked:
                raise ValueError("Mirror provider file is not git-tracked")
            copied_files += 1
            if copied_files > budget.limits.max_files:
                raise ValueError("materialized mirror input exceeds its finite entry limit")
            resolved_initial = observation(resolved.lstat()) if pinned else ()
            if pinned:
                hold_directories(resolved)
            content = read_bytes_confined(
                repo_root, resolved, max_bytes=64 * 1024 * 1024, expected_root_identity=root_identity
            )
            budget.check(len(content))
            # Reads use the resolved public file's held, no-follow ancestor chain.
            # Recheck the declared provider link before accepting those bytes.
            if (
                observation(source.lstat()) != observation(initial)
                or _public_source(repo_root, source, provider_roots) != resolved
            ):
                raise ValueError("Mirror source changed during confined read")
            mode = 0o755 if os.stat(resolved).st_mode & 0o111 else 0o644
            if committed is not None:
                _verify_committed(relative.as_posix(), content, "100755" if mode == 0o755 else "100644", committed)
            if pinned:
                if observation(resolved.lstat()) != resolved_initial:
                    raise ValueError("pinned mirror provider changed during initial admission")
                held_providers[source] = (
                    resolved,
                    observation(initial),
                    resolved_initial,
                    hashlib.sha256(content).hexdigest(),
                    mode,
                    provider_roots,
                )
            atomic_write_bytes_confined(snapshot, target, content, mode=mode)
            count = 1
        if (
            observation(source.lstat()) != observation(initial)
            or _public_source(repo_root, source, provider_roots) != resolved
        ):
            raise ValueError("Mirror provider changed during export")
        return count

    with tempfile.TemporaryDirectory(prefix="mirror-source-") as temporary:
        scratch = Path(temporary).resolve(strict=True)
        snapshot = scratch / "source"
        snapshot.mkdir()
        snapshot_project = snapshot / project_rel
        snapshot_project.mkdir(parents=True)
        _project_root(repo_root, project_rel)
        prefix = f"{project_rel}/"
        for relative in (path[len(prefix) :] for path in tracked_paths if path.startswith(prefix)):
            if _is_clean_source_path(Path(relative)):
                copy_source(project_root / relative, snapshot_project / relative, snapshot)
        dependencies = _declared_resource_dependencies(snapshot_project)
        for dependency in dependencies:
            resource_root = repo_root / dependency
            if resource_root.resolve(strict=True) != resource_root.absolute() or not resource_root.is_dir():
                raise ValueError("declared public resource root must be a real confined directory")
            provider_roots = _PUBLIC_ROOTS + ((Path("infrastructure"),) if dependency == "infrastructure" else ())
            if pinned and dependency == "infrastructure":
                from infrastructure.reporting.readiness_receipts import public_resource_source_paths

                paths = public_resource_source_paths(repo_root, dependency)
                resource_inventories[dependency] = paths
                entries = [path.relative_to(repo_root).as_posix() for path in paths]
                for prefix, nested in pinned[0].submodules:
                    expected = {prefix + "/" + row.path for row in nested.files}
                    observed = {path for path in entries if path.startswith(prefix + "/")}
                    if observed != expected:
                        raise ValueError("public mirror resource inventory differs from its complete pinned source")
            else:
                entries = [path for path in tracked if Path(path).is_relative_to(dependency)]
            if not entries:
                raise ValueError("declared resource dependency has no tracked public contents")
            for entry in sorted(entries):
                if not any(Path(entry).is_relative_to(public) for public in provider_roots):
                    raise ValueError("declared resource dependency contains a nonpublic tracked path")
                resource_relative = Path(entry).relative_to(dependency)
                if _is_clean_resource_path(resource_relative, dependency):
                    copy_source(
                        repo_root / entry,
                        snapshot / entry,
                        snapshot,
                        provider_roots=provider_roots,
                        resource=dependency,
                    )
        metadata = repo_root / "pyproject.toml"
        if metadata.exists() or metadata.is_symlink():
            initial = metadata.lstat()
            content = read_bytes_confined(
                repo_root, metadata, max_bytes=64 * 1024 * 1024, expected_root_identity=root_identity
            )
            budget.check(len(content))
            if committed is not None:
                metadata_mode = "100755" if initial.st_mode & 0o111 else "100644"
                _verify_committed("pyproject.toml", content, metadata_mode, committed)
            if observation(metadata.lstat()) != observation(initial):
                raise ValueError("platform export metadata changed during confined read")
            if pinned:
                held_providers[metadata] = (
                    metadata,
                    observation(initial),
                    observation(initial),
                    hashlib.sha256(content).hexdigest(),
                    0o755 if initial.st_mode & 0o111 else 0o644,
                    (Path("pyproject.toml"),),
                )
            atomic_write_bytes_confined(snapshot, snapshot / "pyproject.toml", content)
        exported = scratch / project_root.name
        canonical_snapshot_export(snapshot, project_rel, exported, source_revision, budget)
        for dependency, paths in resource_inventories.items():
            if public_resource_source_paths(repo_root, dependency) != paths:
                raise ValueError("public mirror resource inventory changed during export")
        for reference in pinned:
            if inventory(repo_root, reference.commit, budget.deadline) != reference:
                raise ValueError("pinned mirror native reference custody changed during export")
        if pinned:
            current_root = repo_root.lstat()
            if not stat.S_ISDIR(current_root.st_mode) or (current_root.st_dev, current_root.st_ino) != root_identity:
                raise ValueError("pinned mirror source root changed during export")
            for directory, identity in held_directories.items():
                budget.check()
                current = directory.lstat()
                if not stat.S_ISDIR(current.st_mode) or (current.st_dev, current.st_ino) != identity:
                    raise ValueError("pinned mirror provider directory changed during export")
            assert committed is not None
            for source, held in held_providers.items():
                budget.check()
                resolved, source_observed, provider_observed, digest, mode, provider_roots = held
                if (
                    observation(source.lstat()) != source_observed
                    or _bound_source(repo_root, source, committed, budget, provider_roots) != resolved
                    or observation(resolved.lstat()) != provider_observed
                ):
                    raise ValueError("pinned mirror physical provider changed during export")
                closing = read_bytes_confined(
                    repo_root, resolved, max_bytes=64 * 1024 * 1024, expected_root_identity=root_identity
                )
                budget.check(len(closing))
                actual_mode = 0o755 if resolved.lstat().st_mode & 0o111 else 0o644
                if (
                    hashlib.sha256(closing).hexdigest() != digest
                    or actual_mode != mode
                    or observation(source.lstat()) != source_observed
                    or observation(resolved.lstat()) != provider_observed
                ):
                    raise ValueError("pinned mirror physical bytes or mode changed during closing admission")
                _verify_committed(
                    resolved.relative_to(repo_root).as_posix(),
                    closing,
                    "100755" if actual_mode == 0o755 else "100644",
                    committed,
                )
            for directory, identity in held_directories.items():
                budget.check()
                current = directory.lstat()
                if not stat.S_ISDIR(current.st_mode) or (current.st_dev, current.st_ino) != identity:
                    raise ValueError("pinned mirror provider directory changed during closing admission")
        if source_revision is not None:
            clean_source_revision(repo_root, source_revision)
        budget.check()
        destination.mkdir(parents=True, exist_ok=True)
        count = 0
        for path in sorted(exported.rglob("*")):
            budget.check()
            if not path.is_file():
                continue
            content = read_bytes_confined(exported, path, max_bytes=64 * 1024 * 1024)
            budget.check(len(content))
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            atomic_write_bytes_confined(destination, destination / path.relative_to(exported), content, mode=mode)
            count += 1
            if count > budget.limits.max_files:
                raise ValueError("canonical mirror export exceeds its finite entry limit")
        budget.check()
        return count


def sync_exemplar(
    repo_root: Path,
    exemplar: str,
    *,
    commit: bool,
    source_revision: str,
    project_rel: str | None = None,
    removal_plan: dict[str, Any] | None = None,
    reviewed_plan_sha256: str | None = None,
    quarantine_root: Path | None = None,
    install_projection: bool = False,
    meta_provider: GitInstallProvider | None = None,
) -> MirrorResult:
    """Sync one exemplar into its standalone repository.

    With ``commit=False`` this reports what would change without cloning side
    effects persisting, which is the intended way to review a sync before it
    touches a public repository. Supplied removal authority additionally requires
    caller-retained quarantine; no remote update occurs until ``commit=True``.
    """
    if type(install_projection) is not bool or meta_provider is not None and not install_projection:
        raise ValueError("Meta installation providers require explicit installation projection")
    project_rel = project_rel or f"projects/templates/{exemplar}"
    repo_root = repo_root.resolve()
    revision = clean_source_revision(repo_root, source_revision)
    project_root = _project_root(repo_root, project_rel)
    repository = declared_repository(project_root)
    if not repository:
        return MirrorResult(exemplar, "", "SKIP: no repository-code declared")

    with tempfile.TemporaryDirectory(prefix=f"mirror_{exemplar}_") as tmp:
        scratch = Path(tmp).resolve(strict=True)
        export = scratch / "export"
        export.mkdir()
        populate_mirror_tree(repo_root, project_rel, export, source_revision=revision)
        source_export_sha256 = publication_export_sha256(export)
        projection_sha256 = ""
        if install_projection:
            from infrastructure.publishing.standalone_install_projection import (
                PROJECTION_NAME,
                GitInstallProvider,
                project_standalone_installation,
            )

            projected = scratch / "install-projection"
            project_standalone_installation(
                export, projected, root_provider=GitInstallProvider(repo_root, revision), meta_provider=meta_provider
            )
            export = projected
            projection_sha256 = hashlib.sha256(
                read_bytes_confined(export, export / PROJECTION_NAME, max_bytes=64 * 1024 * 1024)
            ).hexdigest()
        export_sha256 = publication_export_sha256(export)
        _assert_source_current(
            repo_root,
            project_rel,
            revision,
            export_sha256,
            scratch,
            install_projection=install_projection,
            meta_provider=meta_provider,
        )
        if declared_repository(export) != repository:
            raise ValueError("standalone destination declaration differs from the admitted source export")
        work = scratch / "repo"
        admitted = f"{repository}.git"
        validate_git_destination(admitted, lambda args: _git(args, cwd=repo_root), require_origin=False)
        clone = _git(["clone", "--quiet", "--", admitted, str(work)], cwd=repo_root, check=False)
        if clone.returncode != 0:
            return MirrorResult(exemplar, repository, "SKIP: clone failed")

        branch = _git(["symbolic-ref", "--short", "HEAD"], cwd=work).stdout.strip()
        destination_revision = _git(["rev-parse", "--verify", "HEAD^{commit}"], cwd=work).stdout.strip()
        target = PublicationTarget(repository, branch)
        _validate_git_destination_current(admitted, work)
        update = update_publication_tree(
            export,
            work,
            target,
            removal_plan=removal_plan,
            reviewed_plan_sha256=reviewed_plan_sha256,
            quarantine_root=quarantine_root,
        )
        evidence: dict[str, Any] = {
            "managed_export_parity": update.managed_export_parity,
            "preserved_files": update.preserved,
            "removal_plan": update.plan,
            "removal_plan_sha256": review_plan_sha256(update.plan),
            "source_commit": revision,
            "export_kind": "install-projection" if install_projection else "source",
            "source_export_sha256": source_export_sha256,
            "install_projection_sha256": projection_sha256,
        }
        _git(["add", "-A"], cwd=work)
        added, modified, deleted = _classify(_git(["status", "--porcelain"], cwd=work).stdout)
        if update.stale_managed:
            return MirrorResult(
                exemplar, repository, "REVIEW REQUIRED: stale managed files", added, modified, deleted, **evidence
            )
        _assert_source_current(
            repo_root,
            project_rel,
            revision,
            export_sha256,
            scratch,
            install_projection=install_projection,
            meta_provider=meta_provider,
        )
        validate_publication_update(work, target, update)
        if _git(["rev-parse", "--verify", "HEAD^{commit}"], cwd=work).stdout.strip() != destination_revision:
            raise ValueError("standalone destination HEAD changed during synchronization")
        if added + modified + deleted == 0:
            validate_publication_commit(work, update, destination_revision)
            _validate_git_destination_current(admitted, work)
            return MirrorResult(exemplar, repository, "up to date", **evidence)
        if not commit:
            return MirrorResult(exemplar, repository, "WOULD SYNC", added, modified, deleted, **evidence)

        message = (
            f"Sync from template monorepo\n\n"
            f"Source: {revision}\n"
            f"Source-Export-SHA256: {source_export_sha256}\n"
            + (f"Install-Projection-SHA256: {projection_sha256}\n" if install_projection else "")
            + f"Export-SHA256: {export_sha256}\n"
            f"Mirrors the canonical public export from {project_rel}/, including declared resources, per "
            "docs/guides/publication-runbook.md. Destination-only publication "
            "evidence is preserved; source removals require an exact reviewed manifest."
        )
        _git(["commit", "--quiet", "-m", message], cwd=work)
        destination_revision = _git(["rev-parse", "--verify", "HEAD^{commit}"], cwd=work).stdout.strip()
        _assert_source_current(
            repo_root,
            project_rel,
            revision,
            export_sha256,
            scratch,
            install_projection=install_projection,
            meta_provider=meta_provider,
        )
        validate_publication_update(work, target, update)
        validate_publication_commit(work, update, destination_revision)
        if _git(["symbolic-ref", "--short", "HEAD"], cwd=work).stdout.strip() != branch:
            raise ValueError("standalone destination branch changed before push")
        _validate_git_destination_current(admitted, work)
        push = push_admitted_commit(work, admitted, destination_revision, branch)
        if push.returncode != 0:
            return MirrorResult(exemplar, repository, "PUSH FAILED", added, modified, deleted, **evidence)
        sha = _git(["rev-parse", "--short", "HEAD"], cwd=work).stdout.strip()
        return MirrorResult(exemplar, repository, "SYNCED", added, modified, deleted, sha, **evidence)


__all__ = [
    "MirrorResult",
    "populate_mirror_tree",
    "sync_exemplar",
    "validate_git_destination",
    "push_admitted_commit",
]
