"""GitHub Pages deployment with scoped credentials and ordinary Git updates."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from typing import Any

from infrastructure.core.determinism import now_utc_iso as _now_utc
from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.publication_tree import (
    PublicationTarget,
    PublicationUpdate,
    copy_publication_source,
    update_publication_tree,
    validate_publication_update,
)
from infrastructure.publishing.standalone_mirror import (
    push_admitted_commit,
    validate_git_destination,
    validate_publication_commit,
)

from .models import SiteDeployConfig, SiteDeployResult

logger = get_logger(__name__)
_REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")
_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
_TOKEN_ENV = "TEMPLATE_PAGES_AUTH_TOKEN"
_GIT_TIMEOUT = 60.0
_GIT_LOCAL_ENVIRONMENT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_GRAFT_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_REPLACE_REF_BASE",
        "GIT_PREFIX",
        "GIT_INTERNAL_SUPER_PREFIX",
        "GIT_SHALLOW_FILE",
        "GIT_NAMESPACE",
        "GIT_TEMPLATE_DIR",
        "GIT_EXEC_PATH",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
        "GIT_PROXY_COMMAND",
        "GIT_SSL_NO_VERIFY",
    }
)


def _validate_target(repo: str, branch: str) -> None:
    if not _REPOSITORY.fullmatch(repo):
        raise ValueError("GitHub repository must be a plain owner/repo slug")
    if (
        not _BRANCH.fullmatch(branch)
        or any(part.startswith(".") or part.endswith(".lock") for part in branch.split("/"))
        or ".." in branch
        or "//" in branch
        or branch.endswith(("/", "."))
    ):
        raise ValueError("GitHub Pages branch must be a valid branch name")


@contextmanager
def _credential_environment(token: str, directory: Path) -> Iterator[dict[str, str]]:
    """Supply credentials only to exact GitHub HTTPS prompts, never to argv."""
    if not token or any(char in token for char in "\r\n\0"):
        raise ValueError("GitHub token must be a nonempty single-line value")
    askpass = directory / "askpass"
    askpass.write_text(
        '#!/bin/sh\ncase "$1" in\n'
        "  \"Username for 'https://github.com': \" ) printf '%s\\n' x-access-token ;;\n"
        "  \"Password for 'https://x-access-token@github.com': \" ) "
        "printf '%s\\n' \"$TEMPLATE_PAGES_AUTH_TOKEN\" ;;\n"
        "  * ) exit 1 ;;\nesac\n",
        encoding="utf-8",
    )
    askpass.chmod(0o700)
    env = build_bounded_env()
    # Git tracing and inherited configuration can expose HTTP credentials or
    # redirect a reviewed destination. The deploy uses its own fixed settings.
    for name in tuple(env):
        if name.startswith(("GIT_TRACE", "GIT_CONFIG")) or name in _GIT_LOCAL_ENVIRONMENT | {
            "GIT_CURL_VERBOSE",
            "SSH_ASKPASS",
        }:
            env.pop(name)
    env.update(
        {
            "GIT_ASKPASS": str(askpass),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            _TOKEN_ENV: token,
        }
    )
    try:
        yield env
    finally:
        env.pop(_TOKEN_ENV, None)
        askpass.unlink(missing_ok=True)


def _git(args: list[str], *, cwd: Path, env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess[str]:
    process_env = {name: value for name, value in env.items() if name not in _GIT_LOCAL_ENVIRONMENT}
    result = run_bounded_subprocess(
        [
            "git",
            "-c",
            "credential.helper=",
            "-c",
            "credential.useHttpPath=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=cwd,
        env=process_env,
        timeout=_GIT_TIMEOUT,
    )
    secret = env.get(_TOKEN_ENV, "")
    stdout = result.stdout.replace(secret, "[redacted]") if secret else result.stdout
    stderr = result.stderr or result.command_error
    stderr = stderr.replace(secret, "[redacted]") if secret else stderr
    process = subprocess.CompletedProcess(args, result.returncode, stdout, stderr)
    if check and process.returncode != 0:
        raise RuntimeError(f"GitHub Pages git {args[0]} failed (exit {process.returncode}): {process.stderr}")
    return process


def _copy_site(site_dir: Path, pages_dir: Path) -> None:
    """Update confined regular files, preserving published files absent locally."""
    copy_publication_source(site_dir, pages_dir)


def _publish_tree(
    site_dir: Path,
    remote: str,
    branch: str,
    work: Path,
    env: dict[str, str],
    *,
    target: PublicationTarget | None = None,
    removal_plan: dict[str, Any] | None = None,
    reviewed_plan_sha256: str | None = None,
    quarantine_root: Path | None = None,
) -> PublicationUpdate:
    """Perform ordinary Git updates; local bare remotes exercise this contract."""
    if target is not None and (
        target.branch != branch
        or remote.startswith("https://github.com/")
        and remote.removesuffix(".git") != target.repository
    ):
        raise ValueError("reviewed publication target differs from the actual GitHub Pages destination")
    pages = work / "pages"
    admission = work / "destination-admission.git"
    _git(["-c", "init.templateDir=", "init", "--bare", str(admission)], cwd=work, env=env)
    validate_git_destination(remote, lambda args: _git(args, cwd=admission, env=env), require_origin=False)
    found = _git(
        ["ls-remote", "--exit-code", "--heads", remote, f"refs/heads/{branch}"], cwd=work, env=env, check=False
    )
    if found.returncode == 0:
        _git(
            ["clone", "--single-branch", "--branch", branch, "--depth", "1", "--", remote, str(pages)],
            cwd=work,
            env=env,
        )
    elif found.returncode == 2:
        pages.mkdir()
        _git(["init", "-b", branch], cwd=pages, env=env)
        _git(["remote", "add", "origin", remote], cwd=pages, env=env)
    else:
        raise RuntimeError(f"GitHub Pages branch discovery failed (exit {found.returncode}): {found.stderr}")
    export = work / "export"
    validate_git_destination(remote, lambda args: _git(args, cwd=pages, env=env))
    export.mkdir()
    _copy_site(site_dir, export)
    target = target or PublicationTarget(remote.removesuffix(".git"), branch)
    update = update_publication_tree(
        export,
        pages,
        target,
        removal_plan=removal_plan,
        reviewed_plan_sha256=reviewed_plan_sha256,
        quarantine_root=quarantine_root,
    )
    if update.stale_managed:
        raise ValueError(
            "GitHub Pages has stale managed files; an exact reviewed removal manifest is required before push"
        )
    _git(["add", "-A"], cwd=pages, env=env)
    validate_publication_update(pages, target, update)
    changed = _git(["diff", "--cached", "--quiet"], cwd=pages, env=env, check=False)
    if changed.returncode == 0:
        revision = _git(["rev-parse", "--verify", "HEAD^{commit}"], cwd=pages, env=env).stdout.strip()
        validate_publication_commit(pages, update, revision)
        validate_git_destination(remote, lambda args: _git(args, cwd=pages, env=env))
        return update
    if changed.returncode != 1:
        raise RuntimeError("GitHub Pages failed to inspect staged changes")
    _git(
        [
            "-c",
            "user.name=template publisher",
            "-c",
            "user.email=publisher@users.noreply.github.com",
            "commit",
            "-m",
            "Deploy static site [skip ci]",
        ],
        cwd=pages,
        env=env,
    )
    validate_publication_update(pages, target, update)
    revision = _git(["rev-parse", "--verify", "HEAD^{commit}"], cwd=pages, env=env).stdout.strip()
    validate_publication_commit(pages, update, revision)
    _push_branch(pages, branch, env, remote=remote, revision=revision)
    return update


def _push_branch(pages: Path, branch: str, env: dict[str, str], *, remote: str, revision: str) -> None:
    """Refuse divergent publication instead of replacing remote history."""
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("GitHub Pages push requires its verified full commit identity")
    validate_git_destination(remote, lambda args: _git(args, cwd=pages, env=env))
    pushed = push_admitted_commit(pages, remote, revision, branch, env=env)
    if pushed.returncode != 0:
        secret = env.get(_TOKEN_ENV, "")
        diagnostic = pushed.stderr.replace(secret, "[redacted]") if secret else pushed.stderr
        raise RuntimeError(f"GitHub Pages git push failed (exit {pushed.returncode}): {diagnostic}")


class GitHubPagesAdapter:
    """Deploy a site using explicit credentials and a validated destination."""

    name: str = "github_pages"

    def __init__(self, config: SiteDeployConfig) -> None:
        self.config = config

    def deploy(self, *, dry_run: bool = True) -> SiteDeployResult:
        """Deploy the static site to the hosting provider."""
        site_dir = Path(self.config.site_dir)
        repo = self.config.repo or "owner/repo"
        branch = self.config.branch or "gh-pages"
        try:
            if not site_dir.exists():
                raise ValueError(f"Site directory does not exist: {site_dir}")
            if site_dir.is_symlink() or not site_dir.is_dir():
                raise ValueError("Site directory must be a real directory")
            _validate_target(repo, branch)
            url = f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/"
            if dry_run:
                return SiteDeployResult(
                    hosting=self.name,
                    status="dry-run",
                    url=url,
                    timestamp_utc=_now_utc(),
                    extra={"would_push_to": f"{repo}:{branch}", "site_dir": str(site_dir)},
                )
            if not self.config.token:
                raise ValueError("Missing GitHub token for gh-pages push")
            with tempfile.TemporaryDirectory(prefix="template_pages_") as tmp:
                work = Path(tmp).resolve()
                with _credential_environment(self.config.token, work) as env:
                    update = _publish_tree(
                        site_dir,
                        f"https://github.com/{repo}.git",
                        branch,
                        work,
                        env,
                        target=PublicationTarget(f"https://github.com/{repo}", branch),
                        removal_plan=self.config.removal_plan,
                        reviewed_plan_sha256=self.config.reviewed_plan_sha256,
                        quarantine_root=Path(self.config.removal_quarantine_dir)
                        if self.config.removal_quarantine_dir
                        else None,
                    )
            logger.info("GitHub Pages deployed to %s:%s", repo, branch)
            return SiteDeployResult(
                hosting=self.name,
                status="ok",
                url=url,
                timestamp_utc=_now_utc(),
                extra={
                    "repo": repo,
                    "branch": branch,
                    "managed_export_parity": str(update.managed_export_parity).lower(),
                    "preserved_files": str(len(update.preserved)),
                },
            )
        except (OSError, RuntimeError, ValueError) as exc:
            error = str(exc)
            if self.config.token:
                error = error.replace(self.config.token, "[redacted]")
            return SiteDeployResult(hosting=self.name, status="error", error=error, timestamp_utc=_now_utc())
