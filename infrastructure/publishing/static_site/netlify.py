"""Netlify deployment via netlify CLI."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .models import SiteDeployConfig, SiteDeployResult

logger = get_logger(__name__)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class NetlifyAdapter:
    name: str = "netlify"

    def __init__(self, config: SiteDeployConfig) -> None:
        self.config = config

    def deploy(self, *, dry_run: bool = True) -> SiteDeployResult:
        site_dir = Path(self.config.site_dir)
        site_id = self.config.site_id

        if dry_run:
            prod_flag = "--prod" if self.config.production else ""
            return SiteDeployResult(
                hosting=self.name,
                status="dry-run",
                url=None,
                timestamp_utc=_now_utc(),
                extra={"would_run": f"netlify deploy --dir {site_dir} {prod_flag}".strip()},
            )

        token = self.config.token or os.environ.get("NETLIFY_AUTH_TOKEN")
        if not token:
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error="Missing NETLIFY_AUTH_TOKEN",
                timestamp_utc=_now_utc(),
            )

        env = {**os.environ, "NETLIFY_AUTH_TOKEN": token}
        if site_id:
            env["NETLIFY_SITE_ID"] = site_id

        cmd = ["netlify", "deploy", "--dir", str(site_dir), "--json"]
        if self.config.production:
            cmd.append("--prod")

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            return SiteDeployResult(
                hosting=self.name,
                status="error",
                error=f"netlify deploy failed: {result.stderr}",
                timestamp_utc=_now_utc(),
            )

        url: str | None = None
        deploy_id: str | None = None
        try:
            data = json.loads(result.stdout)
            url = data.get("deploy_url") or data.get("url")
            deploy_id = data.get("deploy_id")
        except json.JSONDecodeError:
            pass

        logger.info("Netlify deployed: %s", url)
        return SiteDeployResult(
            hosting=self.name,
            status="ok",
            url=url,
            deploy_id=deploy_id,
            timestamp_utc=_now_utc(),
        )
