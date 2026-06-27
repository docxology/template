"""Cloudflare Pages deployment via Wrangler CLI."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .models import SiteDeployConfig, SiteDeployResult

logger = get_logger(__name__)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class CloudflarePagesAdapter:
    name: str = "cloudflare_pages"

    def __init__(self, config: SiteDeployConfig) -> None:
        self.config = config

    def deploy(self, *, dry_run: bool = True) -> SiteDeployResult:
        site_dir = Path(self.config.site_dir)
        project = self.config.site_id or "my-project"

        if dry_run:
            return SiteDeployResult(
                hosting=self.name,
                status="dry-run",
                url=f"https://{project}.pages.dev",
                timestamp_utc=_now_utc(),
                extra={"would_run": (f"wrangler pages deploy {site_dir} --project-name {project}")},
            )

        token = self.config.token or os.environ.get("CLOUDFLARE_API_TOKEN")
        if not token:
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error="Missing CLOUDFLARE_API_TOKEN",
                timestamp_utc=_now_utc(),
            )

        env = {**os.environ, "CLOUDFLARE_API_TOKEN": token}
        cmd = [
            "wrangler",
            "pages",
            "deploy",
            str(site_dir),
            "--project-name",
            project,
        ]
        if not self.config.production:
            cmd.append("--branch=preview")

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error=f"wrangler failed: {result.stderr}",
                timestamp_utc=_now_utc(),
            )

        url_line = next(
            (ln for ln in result.stdout.splitlines() if "pages.dev" in ln),
            None,
        )
        url = url_line.strip() if url_line else f"https://{project}.pages.dev"

        logger.info("Cloudflare Pages deployed: %s", url)
        return SiteDeployResult(
            hosting=self.name,
            status="ok",
            url=url,
            timestamp_utc=_now_utc(),
            extra={"project": project},
        )
