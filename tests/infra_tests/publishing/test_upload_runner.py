#!/usr/bin/env python3
"""Tests for infrastructure.publishing.upload_runner.

No mocks: the orchestrator is exercised with real injected callables, and the
real platform uploaders are run in dry-run mode (no network) against a temp PDF.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.publishing.upload_runner import (
    CORE_UPLOADERS,
    UploadTargets,
    run_uploads,
    select_jobs,
    upload_github,
    upload_github_pages,
    upload_huggingface,
    upload_osf,
    upload_pinata,
)


def _targets(tmp_path: Path) -> UploadTargets:
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 minimal")
    return UploadTargets(
        project_root=tmp_path,
        pdf=pdf,
        web_dir=tmp_path / "web",
        hf_repo_id="owner/repo",
        github_repo="owner/repo",
        osf_title="Title",
    )


def test_upload_osf_threads_node_id_for_idempotency(tmp_path: Path) -> None:
    # With osf_node_id set, the dry-run deposit targets that existing node
    # (idempotent re-run) rather than proposing to create a new one.
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 minimal")
    reuse = UploadTargets(
        project_root=tmp_path,
        pdf=pdf,
        web_dir=tmp_path / "web",
        hf_repo_id="owner/repo",
        github_repo="owner/repo",
        osf_title="Title",
        osf_node_id="abcde",
    )
    receipt = upload_osf(reuse, commit=False, env={})
    assert receipt["node_id"] == "abcde"
    assert receipt["url"] == "https://osf.io/abcde/"

    # Without a node id, the receipt does not claim a reused node.
    fresh = _targets(tmp_path)
    fresh_receipt = upload_osf(fresh, commit=False, env={})
    assert fresh_receipt["node_id"] != "abcde"


def test_select_jobs_defaults_to_core() -> None:
    jobs = select_jobs()
    assert set(jobs) == set(CORE_UPLOADERS)


def test_select_jobs_includes_optional() -> None:
    jobs = select_jobs(include_github=True, include_static=True)
    assert "github" in jobs
    assert "netlify" in jobs
    assert "cloudflare" in jobs
    assert "github_pages" in jobs


def test_select_jobs_only_filter() -> None:
    jobs = select_jobs(only=["pinata", "osf"], include_github=True)
    assert set(jobs) == {"pinata", "osf"}


def test_run_uploads_with_injected_callables(tmp_path: Path) -> None:
    def good(targets, commit, env):  # noqa: ANN001, ARG001
        return {"status": "dry-run", "url": "u"}

    run = run_uploads(_targets(tmp_path), jobs={"a": good, "b": good}, commit=False, env={})
    assert run.mode == "DRY-RUN"
    assert set(run.results) == {"a", "b"}
    assert run.ok


def test_run_uploads_captures_errors_without_aborting(tmp_path: Path) -> None:
    def good(targets, commit, env):  # noqa: ANN001, ARG001
        return {"status": "dry-run"}

    def boom(targets, commit, env):  # noqa: ANN001, ARG001
        raise RuntimeError("kaboom")

    run = run_uploads(_targets(tmp_path), jobs={"a": good, "b": boom, "c": good}, commit=False, env={})
    # The failing job is captured; the others still ran.
    assert run.results["b"]["status"] == "error"
    assert "kaboom" in run.results["b"]["error"]
    assert run.results["a"]["status"] == "dry-run"
    assert run.results["c"]["status"] == "dry-run"
    assert not run.ok


def test_run_uploads_commit_mode_label(tmp_path: Path) -> None:
    run = run_uploads(_targets(tmp_path), jobs={}, commit=True, env={})
    assert run.mode == "REAL UPLOAD"
    assert run.ok  # vacuously true with no jobs


def test_run_uploads_preflight_blocks_invalid_payload_before_provider(tmp_path: Path) -> None:
    project = tmp_path / "projects/templates/template_code_project"
    (project / "output/pdf").mkdir(parents=True)
    pdf = project / "output/pdf/paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 minimal")
    targets = UploadTargets(
        project_root=project,
        pdf=tmp_path / "outside.pdf",
        web_dir=project / "output/web",
        hf_repo_id="owner/repo",
        github_repo="owner/repo",
        osf_title="Title",
        repo_root=tmp_path,
        project_name="templates/template_code_project",
    )
    called = False

    def provider(_targets, _commit, _env):  # noqa: ANN001
        nonlocal called
        called = True
        return {"status": "ok"}

    with pytest.raises(ValueError, match="outside canonical project tree"):
        run_uploads(targets, jobs={"provider": provider}, commit=True, env={})
    assert called is False


def test_run_uploads_records_redacted_preflight_manifest(tmp_path: Path) -> None:
    project = tmp_path / "projects/templates/template_code_project"
    pdf_dir = project / "output/pdf"
    pdf_dir.mkdir(parents=True)
    pdf = pdf_dir / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 minimal")
    targets = UploadTargets(
        project_root=project,
        pdf=pdf,
        web_dir=project / "output/web",
        hf_repo_id="owner/repo",
        github_repo="owner/repo",
        osf_title="Title",
        repo_root=tmp_path,
        project_name="templates/template_code_project",
    )

    run = run_uploads(targets, jobs={}, commit=True, env={"GITHUB_TOKEN": "secret-token"})

    assert run.preflight is not None
    assert run.preflight["credential_sources"] == {}
    assert "secret-token" not in str(run.preflight)


def test_real_pinata_uploader_dry_run_no_network(tmp_path: Path) -> None:
    result = upload_pinata(_targets(tmp_path), False, {})
    assert result["status"] == "dry-run"
    assert result["cid"] is None
    assert result["error"] is None


def test_real_github_uploader_dry_run_no_network(tmp_path: Path) -> None:
    result = upload_github(_targets(tmp_path), False, {"GITHUB_REPO": "owner/repo"})
    assert result["status"] == "dry-run"
    assert result["repo"] == "owner/repo"
    assert result["would_release"]


def test_real_huggingface_uploader_dry_run_no_network(tmp_path: Path) -> None:
    result = upload_huggingface(_targets(tmp_path), False, {})
    assert result["status"] == "dry-run"
    assert result["url"] and "owner/repo" in result["url"]
    assert result["error"] is None


def test_real_github_pages_uploader_dry_run_no_network(tmp_path: Path) -> None:
    (tmp_path / "web").mkdir()
    result = upload_github_pages(_targets(tmp_path), False, {"GITHUB_REPO": "owner/repo", "GITHUB_TOKEN": "tok"})
    assert result["status"] == "dry-run"
    assert result["url"] == "https://owner.github.io/repo/"
    assert result["error"] is None


def test_real_github_pages_uploader_errors_without_site_dir(tmp_path: Path) -> None:
    result = upload_github_pages(_targets(tmp_path), False, {"GITHUB_REPO": "owner/repo"})
    assert result["status"] == "error"
    assert "does not exist" in (result["error"] or "")
