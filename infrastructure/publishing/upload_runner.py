"""Reusable multi-platform upload dispatch for a publishable project.

This houses the per-platform upload helpers and the batch orchestrator that
were previously inlined in ``scripts/publish/upload_gold_refinement.py``. Keeping
them here (tested, importable) leaves the script a thin CLI and lets any project
drive real uploads through one call.

Every uploader is dry-run by default and returns a plain ``dict`` receipt; a
failure in one platform is captured, never raised, so a batch always completes.
Credentials are read from the provided ``env`` mapping (default ``os.environ``).
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# A single uploader: (targets, commit, env) -> receipt dict.
Uploader = Callable[["UploadTargets", bool, Mapping[str, str]], dict[str, Any]]


@dataclass(frozen=True)
class UploadTargets:
    """Per-project inputs shared across platform uploaders."""

    project_root: Path
    pdf: Path
    web_dir: Path
    hf_repo_id: str
    github_repo: str
    osf_title: str
    site_id: str = "project-site"
    # When set, OSF deposits reuse this existing node instead of creating a new
    # one on every ``--commit`` run (idempotency). Left None → create-new.
    osf_node_id: str | None = None
    # Publication safety context. Production CLIs must provide both values;
    # unit callers that exercise provider behavior in isolation may omit them.
    repo_root: Path | None = None
    project_name: str | None = None


def upload_pinata(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload pinata to the remote service."""
    from infrastructure.publishing.archival.providers import IPFSPinataProvider

    receipt = IPFSPinataProvider(jwt=env.get("PINATA_JWT")).deposit(targets.pdf, dry_run=not commit)
    return {"status": receipt.status, "cid": receipt.identifier, "url": receipt.url, "error": receipt.error}


def upload_huggingface(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload huggingface to the remote service."""
    from infrastructure.publishing.huggingface import HuggingFaceConfig, HuggingFaceHubAdapter

    adapter = HuggingFaceHubAdapter(HuggingFaceConfig(repo_id=targets.hf_repo_id))
    receipt = adapter.publish(targets.pdf, dry_run=not commit)
    return {"status": receipt.status, "url": receipt.url, "commit_url": receipt.commit_url, "error": receipt.error}


def upload_osf(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload osf to the remote service."""
    from infrastructure.publishing.osf import OSFAdapter, OSFConfig

    adapter = OSFAdapter(OSFConfig(title=targets.osf_title, node_id=targets.osf_node_id))
    receipt = adapter.publish(targets.pdf, dry_run=not commit)
    return {"status": receipt.status, "node_id": receipt.node_id, "url": receipt.url, "error": receipt.error}


def upload_testpypi(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload testpypi to the remote service."""
    from infrastructure.publishing.pypi import run_pypi_release

    receipt = run_pypi_release(targets.project_root, test=True, dry_run=not commit)
    return {
        "status": receipt.status,
        "package": receipt.package_name,
        "version": receipt.version,
        "url": getattr(receipt, "url", None),
        "error": receipt.error,
    }


def upload_github(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload github to the remote service."""
    from infrastructure.publishing.github import create_github_release

    repo = env.get("GITHUB_REPO", targets.github_repo)
    tag = "v0.1.0-upload-test"
    if not commit:
        return {"status": "dry-run", "would_release": tag, "repo": repo}
    token = env.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is required when commit=True")
    url = create_github_release(
        tag_name=tag,
        release_name=f"Upload test {tag}",
        description="Automated upload-pipeline verification release.",
        assets=[targets.pdf],
        token=token,
        repo=repo,
    )
    return {"status": "ok", "url": url, "repo": repo, "tag": tag}


def _deploy_static(targets: UploadTargets, hosting: str, commit: bool) -> dict[str, Any]:
    from infrastructure.publishing.static_site import (
        CloudflarePagesAdapter,
        NetlifyAdapter,
        SiteDeployConfig,
        SiteHosting,
    )

    if hosting == "netlify":
        config = SiteDeployConfig(hosting=SiteHosting.NETLIFY, site_dir=str(targets.web_dir), production=True)
        receipt = NetlifyAdapter(config).deploy(dry_run=not commit)
    else:
        config = SiteDeployConfig(
            hosting=SiteHosting.CLOUDFLARE_PAGES,
            site_dir=str(targets.web_dir),
            site_id=targets.site_id,
            production=True,
        )
        receipt = CloudflarePagesAdapter(config).deploy(dry_run=not commit)
    return {"status": receipt.status, "url": receipt.url, "error": receipt.error}


def upload_netlify(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload netlify to the remote service."""
    return _deploy_static(targets, "netlify", commit)


def upload_cloudflare(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload cloudflare to the remote service."""
    return _deploy_static(targets, "cloudflare", commit)


def upload_github_pages(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict[str, Any]:
    """Upload github pages to the remote service."""
    from infrastructure.publishing.static_site import GitHubPagesAdapter, SiteDeployConfig, SiteHosting

    config = SiteDeployConfig(
        hosting=SiteHosting.GITHUB_PAGES,
        site_dir=str(targets.web_dir),
        repo=env.get("GITHUB_REPO", targets.github_repo),
        token=env.get("GITHUB_TOKEN"),
    )
    receipt = GitHubPagesAdapter(config).deploy(dry_run=not commit)
    return {"status": receipt.status, "url": receipt.url, "error": receipt.error}


# Core uploaders run by default; github/static are opt-in (real release / CLI deps).
CORE_UPLOADERS: dict[str, Uploader] = {
    "pinata": upload_pinata,
    "huggingface": upload_huggingface,
    "osf": upload_osf,
    "testpypi": upload_testpypi,
}
OPTIONAL_UPLOADERS: dict[str, Uploader] = {
    "github": upload_github,
    "netlify": upload_netlify,
    "cloudflare": upload_cloudflare,
    "github_pages": upload_github_pages,
}


def select_jobs(
    *,
    only: list[str] | None = None,
    include_github: bool = False,
    include_static: bool = False,
) -> dict[str, Uploader]:
    """Resolve the ordered uploader set for a run."""
    jobs: dict[str, Uploader] = dict(CORE_UPLOADERS)
    if include_github:
        jobs["github"] = OPTIONAL_UPLOADERS["github"]
    if include_static:
        jobs["netlify"] = OPTIONAL_UPLOADERS["netlify"]
        jobs["cloudflare"] = OPTIONAL_UPLOADERS["cloudflare"]
        jobs["github_pages"] = OPTIONAL_UPLOADERS["github_pages"]
    if only is not None:
        jobs = {name: fn for name, fn in jobs.items() if name in only}
    return jobs


@dataclass
class UploadRun:
    """Result of a batch upload run."""

    mode: str
    results: dict[str, dict[str, Any]] = field(default_factory=dict)
    preflight: dict[str, object] | None = None

    @property
    def ok(self) -> bool:
        """Return True if the result is successful."""
        return all(r.get("status") != "error" for r in self.results.values())


def run_uploads(
    targets: UploadTargets,
    *,
    jobs: Mapping[str, Uploader],
    commit: bool,
    env: Mapping[str, str] | None = None,
) -> UploadRun:
    """Run each uploader, capturing per-platform errors without aborting the batch."""
    environ = env if env is not None else os.environ
    provider_env = dict(environ)
    run = UploadRun(mode="REAL UPLOAD" if commit else "DRY-RUN")
    if (targets.repo_root is None) != (targets.project_name is None):
        raise ValueError("upload safety context requires both repo_root and project_name")
    if commit and targets.repo_root is None:
        raise ValueError("real uploads require repo_root and project_name safety context")
    if targets.repo_root is not None and targets.project_name is not None:
        from infrastructure.publishing.preflight import publishing_preflight

        payload_paths = [targets.pdf]
        static_jobs = {"netlify", "cloudflare", "github_pages"}
        if static_jobs.intersection(jobs):
            if not targets.web_dir.is_dir():
                raise ValueError(f"publishing web payload directory does not exist: {targets.web_dir}")
            payload_paths.extend(path for path in sorted(targets.web_dir.rglob("*")) if path.is_file())

        credential_keys = {
            "github": "GITHUB_TOKEN",
            "cloudflare": "CLOUDFLARE_API_TOKEN",
            "huggingface": "HF_TOKEN",
            "netlify": "NETLIFY_AUTH_TOKEN",
            "osf": "OSF_TOKEN",
            "pinata": "PINATA_JWT",
            "testpypi": "TESTPYPI_TOKEN",
        }
        credential_sources: dict[str, str] = {}
        for job_name in sorted(jobs):
            credential_name = "github" if job_name == "github_pages" else job_name
            credential_key = credential_keys.get(credential_name)
            if credential_key is not None:
                credential_sources[credential_name] = "environment" if environ.get(credential_key) else "missing"
        github_jobs = {"github", "github_pages"}
        effective_github_repository = (
            environ.get("GITHUB_REPO", targets.github_repo) if github_jobs.intersection(jobs) else None
        )
        run.preflight = publishing_preflight(
            targets.repo_root,
            targets.project_name,
            payload_paths,
            credential_sources,
            github_repository=effective_github_repository,
        )
        preflight_targets = run.preflight.get("targets")
        if isinstance(preflight_targets, Mapping) and isinstance(preflight_targets.get("github"), str):
            provider_env["GITHUB_REPO"] = preflight_targets["github"]
    for name, fn in jobs.items():
        try:
            run.results[name] = fn(targets, commit, provider_env)
        except Exception as exc:  # noqa: BLE001 — report, never abort the batch
            message = str(exc)
            for secret in set(provider_env.values()):
                if secret and len(secret) >= 4:
                    message = message.replace(secret, "[REDACTED]")
            run.results[name] = {"status": "error", "error": f"{type(exc).__name__}: {message}"}
    return run
