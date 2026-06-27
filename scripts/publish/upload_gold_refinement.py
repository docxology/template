#!/usr/bin/env python3
"""Turnkey real-upload runner for template_gold_refinement.

Thin CLI over :mod:`infrastructure.publishing.upload_runner`. Runs the actual
publishing uploads for the gold_refinement exemplar against every credentialed
platform whose token is present in the repo-root ``.env``.

All per-platform dispatch and batch orchestration live in the infrastructure
module (tested); this script only wires CLI flags, loads ``.env``, and writes a
receipt. Credentials authenticate live — verify first with::

    uv run python -m infrastructure.publishing.credential_check --env-file .env

USAGE (from the repo root, on a machine with network)::

    uv run python scripts/publish/upload_gold_refinement.py            # safe: dry-run everything
    uv run python scripts/publish/upload_gold_refinement.py --commit   # REAL uploads
    uv run python scripts/publish/upload_gold_refinement.py --commit --only pinata huggingface osf testpypi
    uv run python scripts/publish/upload_gold_refinement.py --commit --include-github --include-static

Flags:
    --commit           Perform real uploads (default is dry-run).
    --only NAMES       Restrict to a subset (pinata huggingface osf testpypi github netlify cloudflare).
    --include-github   Include a GitHub release (off by default — creates a real release/tag).
    --include-static   Include Netlify + Cloudflare static-site deploys (need netlify/wrangler CLIs).

A JSON receipt is written to output/templates/template_gold_refinement/upload_receipts.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from infrastructure.publishing.upload_runner import (  # noqa: E402
    UploadTargets,
    run_uploads,
    select_jobs,
)

PROJECT = REPO / "projects/templates/template_gold_refinement"
TARGETS = UploadTargets(
    project_root=PROJECT,
    pdf=PROJECT / "output/pdf/template_gold_refinement_combined.pdf",
    web_dir=PROJECT / "output/web",
    hf_repo_id="docxology/template_gold_refinement",
    github_repo="docxology/template_gold_refinement",
    osf_title="Refinement of Gold: A Metallurgical Analogy for Scientific Manuscript Composition",
    site_id="template-gold-refinement",
)


def _load_dotenv() -> None:
    try:
        from infrastructure.core.config.dotenv import ensure_dotenv_loaded

        ensure_dotenv_loaded()
        return
    except Exception:
        pass
    env = REPO / ".env"
    if not env.exists():
        return
    import os

    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="perform REAL uploads")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--include-github", action="store_true")
    parser.add_argument("--include-static", action="store_true")
    args = parser.parse_args()

    _load_dotenv()
    if not TARGETS.pdf.exists():
        print(
            f"ERROR: missing rendered PDF: {TARGETS.pdf}\n"
            "Run: ./run.sh --project templates/template_gold_refinement --pipeline --core-only"
        )
        return 1

    jobs = select_jobs(only=args.only, include_github=args.include_github, include_static=args.include_static)
    run = run_uploads(TARGETS, jobs=jobs, commit=args.commit)

    print(f"\n=== template_gold_refinement uploads — {run.mode} ===\n")
    for name, res in run.results.items():
        status = str(res.get("status") or "")
        flag = {"ok": "✅", "dry-run": "🔎", "error": "❌"}.get(status, "•")
        detail = res.get("url") or res.get("cid") or res.get("error") or ""
        print(f"  {flag} {name:12} {status:8} {detail}")

    out = REPO / "output/templates/template_gold_refinement/upload_receipts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": run.mode,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": run.results,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"\nReceipts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
