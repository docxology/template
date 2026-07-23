"""Tests for scripts/pipeline/stage_08_connector_search.py.

No mocks. Uses real subprocess calls and real filesystem behaviour.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pytest_httpserver import HTTPServer

from infrastructure.search.connectors import ArxivConnector, ConnectorRegistry
from infrastructure.search.connectors.http import ConnectorHttpClient
from infrastructure.search.connectors.stage import main as connector_stage_main

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "pipeline" / "stage_08_connector_search.py"

ARXIV_ATOM = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <published>2024-01-15T00:00:00Z</published>
    <title>Active inference as a scientific method</title>
    <summary>A local-server abstract used for the Stage 08 integration test.</summary>
    <author><name>Ada Researcher</name></author>
  </entry>
</feed>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_script(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run the connector search script with the given arguments."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Import / structural tests
# ---------------------------------------------------------------------------


class TestScriptImports:
    def test_script_imports_cleanly(self) -> None:
        """The scripts package imports cleanly (ensure_repo_root_on_path)."""
        result = subprocess.run(
            [sys.executable, "-c", "import scripts; from scripts import ensure_repo_root_on_path; print('ok')"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "ok" in result.stdout

    def test_script_exists(self) -> None:
        """The canonical pipeline entrypoint exists."""
        assert SCRIPT.exists(), f"Script not found at {SCRIPT}"

    def test_script_is_python(self) -> None:
        """The script is a valid Python file (no syntax errors)."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"Syntax error in {SCRIPT}: {result.stderr}"


# ---------------------------------------------------------------------------
# --help tests
# ---------------------------------------------------------------------------


class TestScriptHelp:
    def test_script_help_exits_zero(self) -> None:
        """--help returns exit code 0."""
        result = run_script("--help")
        assert result.returncode == 0, f"--help failed: {result.stderr}"

    def test_script_help_mentions_project(self) -> None:
        """--help output mentions --project argument."""
        result = run_script("--help")
        assert "--project" in result.stdout

    def test_script_help_mentions_max_results(self) -> None:
        """--help output mentions --max-results argument."""
        result = run_script("--help")
        assert "--max-results" in result.stdout


# ---------------------------------------------------------------------------
# Graceful skip / error handling tests
# ---------------------------------------------------------------------------


class TestScriptGracefulSkip:
    def test_script_missing_project_returns_two(self) -> None:
        """--project nonexistent returns exit code 2 (graceful skip)."""
        result = run_script("--project", "nonexistent_project_xyz_12345")
        assert result.returncode == 2, (
            f"Expected exit 2 for missing project, got {result.returncode}. stderr: {result.stderr}"
        )

    def test_script_missing_project_warns(self) -> None:
        """--project nonexistent emits a warning message."""
        result = run_script("--project", "nonexistent_project_xyz_12345")
        combined = result.stdout + result.stderr
        assert "not found" in combined.lower() or "skip" in combined.lower(), (
            f"Expected skip message in output: {combined!r}"
        )

    def test_script_no_args_fails(self) -> None:
        """The default placeholder project produces a non-zero graceful skip."""
        result = run_script()
        assert result.returncode != 0

    def test_script_disabled_config_returns_two(self, tmp_path: Path) -> None:
        """A project with connector_search.enabled=false returns exit code 2."""
        project_dir = tmp_path / "projects" / "templates" / "test_proj"
        (project_dir / "manuscript").mkdir(parents=True)
        (project_dir / "manuscript" / "config.yaml").write_text(
            "connector_search:\n  enabled: false\n", encoding="utf-8"
        )

        exit_code = connector_stage_main(
            ["--project", "templates/test_proj"],
            repo_root=tmp_path,
        )

        assert exit_code == 2

    def test_script_invalid_config_returns_one(self, tmp_path: Path) -> None:
        """Malformed Stage 08 config fails instead of silently using defaults."""
        project_dir = tmp_path / "projects" / "templates" / "test_proj"
        (project_dir / "manuscript").mkdir(parents=True)
        (project_dir / "manuscript" / "config.yaml").write_text(
            "connector_search:\n  enabled: true\n  max_result: 5\n",
            encoding="utf-8",
        )

        exit_code = connector_stage_main(
            ["--project", "templates/test_proj"],
            repo_root=tmp_path,
        )

        assert exit_code == 1

    def test_connector_failure_is_persisted(self, tmp_path: Path) -> None:
        """An unknown connector produces evidence and a failing exit code."""
        project_dir = tmp_path / "projects" / "templates" / "test_proj"
        project_dir.mkdir(parents=True)
        output_path = tmp_path / "connector-report.json"

        exit_code = connector_stage_main(
            [
                "--project",
                "templates/test_proj",
                "--connector",
                "missing-connector",
                "--query",
                "active inference",
                "--output",
                str(output_path),
            ],
            repo_root=tmp_path,
            registry=ConnectorRegistry(),
        )

        assert exit_code == 1
        report = json.loads(output_path.read_text(encoding="utf-8"))
        assert report["summary"]["failed"] == 1
        search = report["searches"][0]
        assert search["status"] == "error"
        assert "missing-connector" in search["error"]


class TestScriptSuccessPath:
    def test_local_arxiv_search_writes_normalised_report(
        self,
        httpserver: HTTPServer,
        tmp_path: Path,
    ) -> None:
        """Stage 08 performs real local HTTP, parsing, and JSON serialisation."""
        httpserver.expect_request(
            "/api/query",
            query_string={
                "search_query": "all:active inference",
                "start": "0",
                "max_results": "1",
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
        ).respond_with_data(
            ARXIV_ATOM,
            content_type="application/atom+xml",
        )
        project_dir = tmp_path / "projects" / "templates" / "test_proj"
        manuscript_dir = project_dir / "manuscript"
        manuscript_dir.mkdir(parents=True)
        (manuscript_dir / "config.yaml").write_text(
            """\
connector_search:
  enabled: true
  max_results: 3
  connectors:
    arxiv:
      - active inference
""",
            encoding="utf-8",
        )

        registry = ConnectorRegistry()
        registry.register(
            ArxivConnector(
                http_client=ConnectorHttpClient(max_retries=0, ttl=0),
                base_url=httpserver.url_for("/api"),
            )
        )

        exit_code = connector_stage_main(
            [
                "--project",
                "templates/test_proj",
                "--max-results",
                "1",
            ],
            repo_root=tmp_path,
            registry=registry,
        )

        assert exit_code == 0
        output_path = project_dir / "output" / "data" / "connector_search" / "results.json"
        report = json.loads(output_path.read_text(encoding="utf-8"))
        assert report["max_results"] == 1
        assert report["summary"] == {
            "failed": 0,
            "hits": 1,
            "searches": 1,
            "successful": 1,
        }
        search = report["searches"][0]
        assert search["status"] == "success"
        assert search["results"][0]["abstract"].startswith("A local-server")
        assert "summary" not in search["results"][0]
