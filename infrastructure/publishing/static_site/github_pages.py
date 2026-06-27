"""GitHub Pages deployment via git push to gh-pages branch."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .models import SiteDeployConfig, SiteDeployResult

logger = get_logger(__name__)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class GitHubPagesAdapter:
    name: str = "github_pages"

    def __init__(self, config: SiteDeployConfig) -> None:
        self.config = config

    def deploy(self, *, dry_run: bool = True) -> SiteDeployResult:
        site_dir = Path(self.config.site_dir)
        if not site_dir.exists():
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error=f"Site directory does not exist: {site_dir}",
                timestamp_utc=_now_utc(),
            )

        repo = self.config.repo or "owner/repo"
        branch = self.config.branch or "gh-pages"
        url = (
            f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[-1]}/"
            if "/" in repo
            else None
        )

        if dry_run:
            return SiteDeployResult(
                hosting=self.name,
                status="dry-run",
                url=url,
                timestamp_utc=_now_utc(),
                extra={
                    "would_push_to": f"{repo}:{branch}",
                    "site_dir": str(site_dir),
                },
            )

        if not self.config.token:
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error="Missing GitHub token for gh-pages push",
                timestamp_utc=_now_utc(),
            )

        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                pages_dir = tmp_path / "pages"

                clone_result = subprocess.run(
                    [
                        "git",
                        "clone",
                        "--branch",
                        branch,
                        "--depth",
                        "1",
                        f"https://x-access-token:{self.config.token}@github.com/{repo}.git",
                        str(pages_dir),
                    ],
                    capture_output=True,
                    text=True,
                )

                if clone_result.returncode != 0:
                    # Branch does not exist yet — initialise a fresh orphan branch.
                    pages_dir.mkdir(parents=True, exist_ok=True)
                    subprocess.run(
                        ["git", "init"],
                        cwd=pages_dir,
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "checkout", "-b", branch],
                        cwd=pages_dir,
                        check=True,
                        capture_output=True,
                    )

                # Clear existing content (keep .git).
                for item in pages_dir.iterdir():
                    if item.name != ".git":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()

                shutil.copytree(site_dir, pages_dir, dirs_exist_ok=True)

                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=pages_dir,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", "Deploy static site [skip ci]"],
                    cwd=pages_dir,
                    check=True,
                    capture_output=True,
                )

                push_result = subprocess.run(
                    [
                        "git",
                        "push",
                        "--force",
                        f"https://x-access-token:{self.config.token}@github.com/{repo}.git",
                        f"HEAD:{branch}",
                    ],
                    cwd=pages_dir,
                    capture_output=True,
                    text=True,
                )
                if push_result.returncode != 0:
                    return SiteDeployResult(
                        hosting=self.name,
                        status="error",
                        error=f"git push failed: {push_result.stderr}",
                        timestamp_utc=_now_utc(),
                    )

            logger.info("GitHub Pages deployed to %s:%s", repo, branch)
            return SiteDeployResult(
                hosting=self.name,
                status="ok",
                url=url,
                timestamp_utc=_now_utc(),
                extra={"repo": repo, "branch": branch},
            )

        except subprocess.CalledProcessError as exc:
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error=f"GitHub Pages deploy error: {exc}",
                timestamp_utc=_now_utc(),
            )
