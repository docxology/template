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

# A single uploader: (targets, commit, env) -> receipt dict.
Uploader = Callable[["UploadTargets", bool, Mapping[str, str]], dict]


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


def upload_pinata(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
    """Upload pinata to the remote service."""
    from infrastructure.publishing.archival.providers import IPFSPinataProvider

    receipt = IPFSPinataProvider(jwt=env.get("PINATA_JWT")).deposit(targets.pdf, dry_run=not commit)
    return {"status": receipt.status, "cid": receipt.identifier, "url": receipt.url, "error": receipt.error}


def upload_huggingface(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
    """Upload huggingface to the remote service."""
    from infrastructure.publishing.huggingface import HuggingFaceConfig, HuggingFaceHubAdapter

    adapter = HuggingFaceHubAdapter(HuggingFaceConfig(repo_id=targets.hf_repo_id))
    receipt = adapter.publish(targets.pdf, dry_run=not commit)
    return {"status": receipt.status, "url": receipt.url, "commit_url": receipt.commit_url, "error": receipt.error}


def upload_osf(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
    """Upload osf to the remote service."""
    from infrastructure.publishing.osf import OSFAdapter, OSFConfig

    adapter = OSFAdapter(OSFConfig(title=targets.osf_title, node_id=targets.osf_node_id))
    receipt = adapter.publish(targets.pdf, dry_run=not commit)
    return {"status": receipt.status, "node_id": receipt.node_id, "url": receipt.url, "error": receipt.error}


def upload_testpypi(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
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


def upload_github(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
    """Upload github to the remote service."""
    from infrastructure.publishing.github import create_github_release

    repo = env.get("GITHUB_REPO", targets.github_repo)
    tag = "v0.1.0-upload-test"
    if not commit:
        return {"status": "dry-run", "would_release": tag, "repo": repo}
    url = create_github_release(
        tag_name=tag,
        release_name=f"Upload test {tag}",
        description="Automated upload-pipeline verification release.",
        assets=[targets.pdf],
        token=env.get("GITHUB_TOKEN"),
        repo=repo,
    )
    return {"status": "ok", "url": url, "repo": repo, "tag": tag}


def _deploy_static(targets: UploadTargets, hosting: str, commit: bool) -> dict:
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


def upload_netlify(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
    """Upload netlify to the remote service."""
    return _deploy_static(targets, "netlify", commit)


def upload_cloudflare(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
    """Upload cloudflare to the remote service."""
    return _deploy_static(targets, "cloudflare", commit)


def upload_github_pages(targets: UploadTargets, commit: bool, env: Mapping[str, str]) -> dict:
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
    results: dict[str, dict] = field(default_factory=dict)

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
    run = UploadRun(mode="REAL UPLOAD" if commit else "DRY-RUN")
    for name, fn in jobs.items():
        try:
            run.results[name] = fn(targets, commit, environ)
        except Exception as exc:  # noqa: BLE001 — report, never abort the batch
            run.results[name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return run
