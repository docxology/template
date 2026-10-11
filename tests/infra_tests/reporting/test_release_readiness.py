"""Tests for the release-readiness dashboard aggregator.

No mocks: every test feeds real files via ``tmp_path`` and asserts the typed
report and deterministic Markdown/HTML render. Absent inputs must degrade to
``"not available"`` style sections rather than crashing.
"""

from __future__ import annotations

import hashlib
import json

import pytest
from pathlib import Path

from infrastructure.reporting import release_readiness as rr
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

FIXED_TS = "2026-06-06T00:00:00Z"
NOT_AVAILABLE_LOWER = "not available"


def _write_canonical_facts(repo_root: Path) -> None:
    """Write a minimal COUNTS.md with a coverage table."""
    gen = repo_root / "docs" / "_generated"
    gen.mkdir(parents=True, exist_ok=True)
    (gen / "COUNTS.md").write_text(
        "# Canonical Factsheet\n"
        "\n"
        "## Test Status\n"
        "\n"
        "| Project | Tests collected | `src/` line+branch coverage |\n"
        "|---------|-----------------|----------------------------|\n"
        "| `template_code_project` | 196 | 98.25 % |\n"
        "| `template_prose_project` | 76 | 100.00 % |\n"
        "\n"
        "Coverage gates (enforced in CI):\n"
        "\n"
        "- infrastructure/ : >= 60%\n"
        "- public template project `src/` trees : >= 90%\n",
        encoding="utf-8",
    )


def _write_pyproject(repo_root: Path, version: str = "9.9.9") -> None:
    (repo_root / "pyproject.toml").write_text(
        f'[project]\nname = "template"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def _write_changelog(repo_root: Path) -> None:
    (repo_root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n- nothing\n\n## [3.2.0] — 2026-06-04\n\n### Added\n\n- thing\n",
        encoding="utf-8",
    )


def _write_pipeline_report(repo_root: Path, *, failing: bool = False) -> None:
    reports = repo_root / "output" / "template_code_project" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": "ignored-wall-clock",
        "total_duration": 12.5,
        "stages": [
            {"name": "Environment Setup", "exit_code": 0, "duration": 1.0, "status": "passed"},
            {
                "name": "Project Tests",
                "exit_code": 1 if failing else 0,
                "duration": 4.0,
                "status": "failed" if failing else "passed",
            },
        ],
    }
    (reports / "pipeline_report.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_evidence_graph(repo_root: Path) -> None:
    eg = repo_root / "output" / "template_code_project" / "reports" / "evidence_graph.json"
    eg.parent.mkdir(parents=True, exist_ok=True)
    eg.write_text(json.dumps({"nodes": [1, 2, 3], "edges": [[1, 2], [2, 3]]}), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Collection
# --------------------------------------------------------------------------- #


def test_collect_full_report_populates_all_sections(tmp_path: Path) -> None:
    _write_canonical_facts(tmp_path)
    _write_pyproject(tmp_path, "1.2.3")
    _write_changelog(tmp_path)
    _write_pipeline_report(tmp_path)
    _write_evidence_graph(tmp_path)

    report = rr.collect_release_readiness(tmp_path, latest_tag="v1.2.0", generated_at=FIXED_TS)

    assert isinstance(report, rr.ReleaseReadinessReport)
    assert report.generated_at == FIXED_TS
    assert report.release.version == "1.2.3"
    assert report.release.latest_tag == "v1.2.0"
    # coverage facts parsed from canonical_facts
    assert any(p.name == "template_code_project" and p.tests == 196 for p in report.coverage.projects)
    # pipeline state present
    assert report.pipeline.available is True
    assert report.pipeline.total_stages == 2
    assert report.pipeline.failed_stages == 0
    # evidence graph present
    assert report.evidence_graph.available is True
    assert report.evidence_graph.node_count == 3


def test_collect_with_no_artifacts_degrades_gracefully(tmp_path: Path) -> None:
    # Empty repo root — nothing present.
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)

    assert report.release.version is None
    assert report.release.latest_tag is None
    assert report.coverage.projects == []
    assert report.pipeline.available is False
    assert report.evidence_graph.available is False
    assert report.docs_lint.available is False


def test_pipeline_failing_stage_detected(tmp_path: Path) -> None:
    _write_pipeline_report(tmp_path, failing=True)
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    assert report.pipeline.available is True
    assert report.pipeline.failed_stages == 1
    assert report.pipeline.ready is False


def test_docs_lint_consumed_from_json_payload(tmp_path: Path) -> None:
    # A docs-lint JSON snapshot (the shape lint_runner emits) placed on disk.
    payload = {
        "mermaid": [],
        "broken_links": [{"file": "README.md", "line": 3, "text": "x", "target": "y", "reason": "missing"}],
        "consistency": [],
        "doc_pairs": [],
    }
    snap = tmp_path / "docs_lint.json"
    snap.write_text(json.dumps(payload), encoding="utf-8")

    report = rr.collect_release_readiness(tmp_path, docs_lint_json=snap, generated_at=FIXED_TS)
    assert report.docs_lint.available is True
    assert report.docs_lint.total_issues == 1
    assert report.docs_lint.broken_links == 1
    assert report.docs_lint.ready is False


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


def test_markdown_render_is_deterministic(tmp_path: Path) -> None:
    _write_canonical_facts(tmp_path)
    _write_pyproject(tmp_path, "1.2.3")
    _write_pipeline_report(tmp_path)
    _write_evidence_graph(tmp_path)

    report = rr.collect_release_readiness(tmp_path, latest_tag="v1.2.0", generated_at=FIXED_TS)
    md_a = rr.render_markdown(report)
    md_b = rr.render_markdown(report)
    assert md_a == md_b
    # contains each required section heading
    assert "# Release Readiness" in md_a
    assert "## Release Metadata" in md_a
    assert "## Pipeline State" in md_a
    assert "## Coverage & Test Facts" in md_a
    assert "## Evidence Graph" in md_a
    assert "## Documentation Lint" in md_a
    # no wall-clock leaked: only the provided generated_at appears
    assert FIXED_TS in md_a
    assert "ignored-wall-clock" not in md_a


def test_markdown_absent_inputs_say_not_available(tmp_path: Path) -> None:
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    md = rr.render_markdown(report)
    assert "not available" in md.lower()
    # still renders all sections
    assert "## Pipeline State" in md
    assert "## Evidence Graph" in md


def test_html_render_is_deterministic_and_well_formed(tmp_path: Path) -> None:
    _write_canonical_facts(tmp_path)
    _write_pyproject(tmp_path, "1.2.3")
    _write_pipeline_report(tmp_path)

    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    html_a = rr.render_html(report)
    html_b = rr.render_html(report)
    assert html_a == html_b
    assert "<!DOCTYPE html>" in html_a
    assert "Release Readiness" in html_a
    assert "</html>" in html_a


def test_report_to_dict_is_byte_stable_json(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.2.3")
    _write_pipeline_report(tmp_path)
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    a = json.dumps(report.to_dict(), sort_keys=True)
    b = json.dumps(report.to_dict(), sort_keys=True)
    assert a == b
    assert '"version": "1.2.3"' in a


# --------------------------------------------------------------------------- #
# Overall readiness
# --------------------------------------------------------------------------- #


def _write_green_evidence(repo_root: Path) -> tuple[Path, Path]:
    _write_canonical_facts(repo_root)
    counts = repo_root / "docs/_generated/COUNTS.md"
    additional = [
        name.split("/")[-1]
        for name in PUBLIC_PROJECT_NAMES
        if not name.endswith(("template_code_project", "template_prose_project"))
    ]
    counts.write_text(
        counts.read_text() + "".join(f"| `{name}` | 10 | 95.00 % |\n" for name in additional), encoding="utf-8"
    )
    _write_pyproject(repo_root, "1.2.3")
    (repo_root / "CHANGELOG.md").write_text("## [1.2.3] — intended release\n", encoding="utf-8")
    _write_pipeline_report(repo_root)
    _write_evidence_graph(repo_root)
    docs = repo_root / "docs_lint.json"
    docs.write_text(
        json.dumps({key: [] for key in ("mermaid", "broken_links", "consistency", "doc_pairs")}), encoding="utf-8"
    )
    artifact_paths = {
        "release": repo_root / "pyproject.toml",
        "coverage": counts,
        "pipeline": repo_root / "output/template_code_project/reports/pipeline_report.json",
        "evidence_graph": repo_root / "output/template_code_project/reports/evidence_graph.json",
        "docs_lint": docs,
    }
    receipt = repo_root / "readiness_receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "source_fingerprint": source_fingerprint(repo_root),
                "gates": {
                    key: {
                        "status": "passed",
                        "command": f"test {key}",
                        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    for key, path in artifact_paths.items()
                },
            }
        ),
        encoding="utf-8",
    )
    return docs, receipt


def test_five_structural_snapshots_cannot_grant_full_roster_readiness(tmp_path: Path) -> None:
    docs, receipt = _write_green_evidence(tmp_path)
    report = rr.collect_release_readiness(
        tmp_path, docs_lint_json=docs, readiness_receipt=receipt, generated_at=FIXED_TS
    )
    assert report.overall_ready is False
    assert report.candidate_ready is False
    assert report.status == "fail"


def test_missing_evidence_is_incomplete_not_ready(tmp_path: Path) -> None:
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    assert not report.overall_ready
    assert report.status == "unknown"
    assert rr.main(["--repo-root", str(tmp_path), "--strict"]) == 2


def test_stale_source_or_artifact_cannot_pass_readiness(tmp_path: Path) -> None:
    docs, receipt = _write_green_evidence(tmp_path)
    (tmp_path / "README.md").write_text("changed release inputs", encoding="utf-8")
    report = rr.collect_release_readiness(tmp_path, docs_lint_json=docs, readiness_receipt=receipt)
    assert not report.overall_ready
    assert any("source-stale" in issue for issue in report.evidence.issues)
    (tmp_path / "README.md").unlink()
    docs.write_text('{"mermaid":[],"broken_links":[],"consistency":[],"doc_pairs":[]}\n', encoding="utf-8")
    report = rr.collect_release_readiness(tmp_path, docs_lint_json=docs, readiness_receipt=receipt)
    assert not report.overall_ready
    assert any("malformed" in issue for issue in report.evidence.issues)


def test_skipped_or_malformed_pipeline_stages_cannot_pass(tmp_path: Path) -> None:
    _write_pipeline_report(tmp_path)
    path = tmp_path / "output/template_code_project/reports/pipeline_report.json"
    for stages in [[{"exit_code": 0, "status": "skipped"}], ["bad"], [{"exit_code": False, "status": "passed"}]]:
        path.write_text(json.dumps({"stages": stages}), encoding="utf-8")
        assert not rr.collect_pipeline_state(tmp_path).ready


def test_empty_docs_object_cannot_pass(tmp_path: Path) -> None:
    docs = tmp_path / "lint.json"
    docs.write_text("{}", encoding="utf-8")
    assert not rr.collect_docs_lint(docs).ready


def test_partial_coverage_roster_cannot_pass(tmp_path: Path) -> None:
    _write_canonical_facts(tmp_path)
    assert not rr.collect_coverage_facts(tmp_path).ready


def test_overall_not_ready_when_pipeline_failing(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.2.3")
    _write_pipeline_report(tmp_path, failing=True)
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    assert report.overall_ready is False


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def test_cli_writes_markdown_out(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.2.3")
    _write_pipeline_report(tmp_path)
    out = tmp_path / "report.md"

    rc = rr.main(
        [
            "--repo-root",
            str(tmp_path),
            "--out",
            str(out),
            "--generated-at",
            FIXED_TS,
        ]
    )
    assert rc == 0
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "# Release Readiness" in text
    assert FIXED_TS in text


def test_cli_html_format(tmp_path: Path) -> None:
    _write_pyproject(tmp_path, "1.2.3")
    out = tmp_path / "report.html"
    rc = rr.main(
        [
            "--repo-root",
            str(tmp_path),
            "--out",
            str(out),
            "--format",
            "html",
            "--generated-at",
            FIXED_TS,
        ]
    )
    assert rc == 0
    assert "<!DOCTYPE html>" in out.read_text(encoding="utf-8")


def test_cli_stdout_when_no_out(tmp_path: Path, capsys) -> None:
    _write_pyproject(tmp_path, "1.2.3")
    rc = rr.main(["--repo-root", str(tmp_path), "--generated-at", FIXED_TS])
    assert rc == 0
    captured = capsys.readouterr()
    assert "# Release Readiness" in captured.out


# --------------------------------------------------------------------------- #
# Malformed inputs degrade gracefully (no crash)
# --------------------------------------------------------------------------- #


def test_malformed_pipeline_json_degrades(tmp_path: Path) -> None:
    reports = tmp_path / "output" / "p" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "pipeline_report.json").write_text("{not json", encoding="utf-8")
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    assert report.pipeline.available is False


def test_malformed_docs_lint_json_degrades(tmp_path: Path) -> None:
    snap = tmp_path / "docs_lint.json"
    snap.write_text("[not an object]", encoding="utf-8")
    report = rr.collect_release_readiness(tmp_path, docs_lint_json=snap, generated_at=FIXED_TS)
    assert report.docs_lint.available is False


def test_changelog_with_only_unreleased_yields_no_tag(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n- x\n", encoding="utf-8")
    meta = rr.collect_release_metadata(tmp_path)
    assert meta.latest_changelog_version is None
    assert meta.latest_tag is None


def test_explicit_latest_tag_overrides_changelog(tmp_path: Path) -> None:
    _write_changelog(tmp_path)
    meta = rr.collect_release_metadata(tmp_path, latest_tag="v5.0.0")
    assert meta.latest_tag == "v5.0.0"
    assert meta.latest_changelog_version == "3.2.0"


def test_evidence_graph_missing_lists_degrades(tmp_path: Path) -> None:
    eg = tmp_path / "output" / "template_code_project" / "reports" / "evidence_graph.json"
    eg.parent.mkdir(parents=True, exist_ok=True)
    eg.write_text(json.dumps({"meta": "no node/edge lists"}), encoding="utf-8")
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    assert report.evidence_graph.available is True
    assert report.evidence_graph.node_count is None
    assert report.evidence_graph.edge_count is None


def test_html_renders_not_available_when_empty(tmp_path: Path) -> None:
    report = rr.collect_release_readiness(tmp_path, generated_at=FIXED_TS)
    html = rr.render_html(report)
    assert NOT_AVAILABLE_LOWER in html.lower()
    assert "<!DOCTYPE html>" in html


@pytest.mark.timeout(180)
def test_documented_module_invocation_writes_report(tmp_path: Path) -> None:
    """DASHBOARD-CLI-1: the documented ``python -m`` command writes a report and exits 0.

    Exercises the real ``__main__`` entrypoint as a subprocess (the in-process
    tests above call ``main()`` directly), matching the CLAUDE.md Quick Reference
    invocation a maintainer would copy-paste.
    """
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parents[3]
    out_path = tmp_path / "release_readiness.md"
    # Documented argv form: only --out (repo-root/format/timestamp use their
    # documented defaults). Exercises exactly the CLAUDE.md copy-paste string.
    result = subprocess.run(
        [sys.executable, "-m", "infrastructure.reporting.release_readiness", "--out", str(out_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert "Release Readiness" in text  # static heading

    # Assert a NON-static, repo-derived field so a fully-degraded report can't
    # green-wash this: the report's release version must reflect the real repo.
    import tomllib

    version = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert version in text, f"expected repo version {version} in the rendered report"


def test_private_pipeline_snapshots_do_not_enter_public_readiness(tmp_path: Path) -> None:
    private = tmp_path / "output/private_workspace/reports"
    private.mkdir(parents=True)
    (private / "pipeline_report.json").write_text(
        json.dumps({"stages": [{"exit_code": 0, "status": "passed"}]}), encoding="utf-8"
    )
    report = rr.collect_release_readiness(tmp_path)
    assert not report.pipeline.available
    assert "private_workspace" not in rr.render_markdown(report)
