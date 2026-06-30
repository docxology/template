#!/usr/bin/env python3
"""Turnkey real-upload runner for any projects/templates/<name> exemplar.

Generalizes ``upload_gold_refinement.py`` (which stays as the original,
hand-tuned reference) to any exemplar that already has a published Zenodo
record and standalone GitHub repository. Project metadata (title, GitHub repo)
is read live from ``manuscript/config.yaml`` via
:mod:`infrastructure.publishing.status_report`, so no per-project Python file
is needed.

All per-platform dispatch and batch orchestration live in
:mod:`infrastructure.publishing.upload_runner` (tested); this script only
resolves project-specific targets, loads ``.env``, and writes a receipt.
Credentials authenticate live — verify first with::

    uv run python -m infrastructure.publishing.credential_check --env-file .env

USAGE (from the repo root, on a machine with network)::

    uv run python scripts/publish/upload_template_project.py --project template_active_inference
    uv run python scripts/publish/upload_template_project.py --project template_active_inference --commit
    uv run python scripts/publish/upload_template_project.py --project template_active_inference --commit --only pinata huggingface osf testpypi
    uv run python scripts/publish/upload_template_project.py --project template_active_inference --commit --include-static

Flags:
    --project NAME      Exemplar name under projects/templates/.
    --commit            Perform real uploads (default is dry-run).
    --only NAMES        Restrict to a subset (pinata huggingface osf testpypi github netlify cloudflare).
    --include-github    Include a GitHub release (off by default -- upload_runner's github job
                         uses a fixed smoke-test tag, not a real versioned release; prefer
                         scripts/publish_project_release.py for an actual release).
    --include-static    Include Netlify + Cloudflare static-site deploys.

A JSON receipt is written to output/templates/<name>/upload_receipts.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from infrastructure.publishing.status_report import compile_publishing_status  # noqa: E402
from infrastructure.publishing.upload_runner import (  # noqa: E402
    UploadTargets,
    run_uploads,
    select_jobs,
)


def _load_dotenv() -> None:
    try:
        from infrastructure.core.config.dotenv import ensure_dotenv_loaded

        ensure_dotenv_loaded()
        return
    except Exception as exc:
        del exc
    env = REPO / ".env"
    if not env.exists():
        return
    import os

    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _resolve_targets(name: str) -> UploadTargets:
    project_root = REPO / "projects" / "templates" / name
    status = compile_publishing_status(project_root)
    github_repo = status.github_repo or f"docxology/{name}"
    return UploadTargets(
        project_root=project_root,
        pdf=project_root / "output" / "pdf" / f"{name}_combined.pdf",
        web_dir=project_root / "output" / "web",
        hf_repo_id=f"ActiveInference/{name}",
        github_repo=github_repo,
        osf_title=status.title or name,
        site_id=name.replace("_", "-"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Exemplar name under projects/templates/")
    parser.add_argument("--commit", action="store_true", help="perform REAL uploads")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--include-github", action="store_true")
    parser.add_argument("--include-static", action="store_true")
    args = parser.parse_args()

    _load_dotenv()
    targets = _resolve_targets(args.project)
    if not targets.pdf.exists():
        print(
            f"ERROR: missing rendered PDF: {targets.pdf}\n"
            f"Run: ./run.sh --project templates/{args.project} --pipeline --core-only"
        )
        return 1

    jobs = select_jobs(only=args.only, include_github=args.include_github, include_static=args.include_static)
    # Force GITHUB_REPO to this project's resolved repo -- a stale single-project
    # GITHUB_REPO left in .env from a prior session must never silently redirect
    # a github/github_pages upload to a different project's repository.
    import os

    env = {**os.environ, "GITHUB_REPO": targets.github_repo}
    run = run_uploads(targets, jobs=jobs, commit=args.commit, env=env)

    print(f"\n=== {args.project} uploads — {run.mode} ===\n")
    for job_name, res in run.results.items():
        status_val = str(res.get("status") or "")
        flag = {"ok": "✅", "dry-run": "🔎", "error": "❌"}.get(status_val, "•")
        detail = res.get("url") or res.get("cid") or res.get("error") or ""
        print(f"  {flag} {job_name:12} {status_val:8} {detail}")

    out = REPO / "output" / "templates" / args.project / "upload_receipts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": args.project,
        "mode": run.mode,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": run.results,
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"\nReceipts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
