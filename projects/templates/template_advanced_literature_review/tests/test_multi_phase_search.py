"""Contract tests for phase-aware literature search behavior."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

from literature.models import Paper
from multi_phase.search import (
    LLMFilterEngine,
    MultiPhaseSearchRunner,
    PhasedPaper,
    PhaseMetadata,
)


@pytest.fixture
def sample_config() -> dict[str, object]:
    """Return a minimal phase configuration with one optional LLM filter."""
    return {
        "project_config": {
            "search_phases": {
                "phase_1_foundation": {
                    "name": "Foundation Phase",
                    "description": "Basic search",
                    "queries": ["test query"],
                    "max_results_per_query": 100,
                    "engines": {"arxiv": True, "openalex": False},
                    "deterministic_filters": {
                        "min_year": 2020,
                        "min_citation_count": 5,
                    },
                }
            },
            "llm_filters": {
                "test_filter": {
                    "prompt": "Classify this: {abstract}",
                    "apply_to_phases": ["phase_1_foundation"],
                    "keep_values": ["yes"],
                }
            },
            "llm_extraction": {
                "model": "gemma3:4b",
                "base_url": "http://127.0.0.1:1",
                "temperature": 0.1,
                "timeout_seconds": 1,
                "max_retries": 1,
            },
        }
    }


@pytest.fixture
def config_path(tmp_path: Path, sample_config: dict[str, object]) -> Path:
    """Write ``sample_config`` to a temporary YAML file."""
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(sample_config), encoding="utf-8")
    return path


@pytest.fixture
def sample_papers() -> list[Paper]:
    """Return papers spanning the deterministic filter boundaries."""
    return [
        Paper(
            title="Test Paper 1",
            abstract="This is a test abstract about exoplanets.",
            year=2022,
            citation_count=10,
            venue="Nature",
        ),
        Paper(
            title="Test Paper 2",
            abstract="Another test abstract about atmospheres.",
            year=2019,
            citation_count=2,
            venue="arXiv",
        ),
        Paper(
            title="Test Paper 3",
            abstract="A third test paper.",
            year=2023,
            citation_count=15,
            venue="Science",
        ),
    ]


@pytest.fixture
def llm_server() -> Iterator[str]:
    """Serve a real local Ollama-compatible response without external I/O."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            assert self.path == "/api/generate"
            assert payload["stream"] is False
            body = json.dumps({"response": '"yes".'}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_phase_metadata_initialization() -> None:
    metadata = PhaseMetadata(
        phase_id="test_phase",
        name="Test Phase",
        description="A test phase",
        start_time=1000.0,
    )
    assert metadata.queries_executed == []
    assert metadata.deterministic_filters_applied == {}
    assert metadata.depends_on == []


def test_phased_paper_records_discovery_phase() -> None:
    phased = PhasedPaper(
        paper=Paper(title="Test", abstract="Test abstract"),
        discovered_in_phase="phase_1",
    )
    assert phased.phases_found_in == ["phase_1"]


def test_deterministic_filters(config_path: Path, sample_papers: list[Paper], tmp_path: Path) -> None:
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    recent = runner.apply_deterministic_filters(sample_papers, {"min_year": 2020})
    cited = runner.apply_deterministic_filters(sample_papers, {"min_citation_count": 10})
    venues = runner.apply_deterministic_filters(sample_papers, {"venue_patterns": ["nature"]})
    older = runner.apply_deterministic_filters(sample_papers, {"max_year": 2022})
    unknown_venue = Paper(title="Unknown venue", abstract="Text", venue=None)
    venue_or_unknown = runner.apply_deterministic_filters(
        [*sample_papers, unknown_venue], {"venue_patterns": ["nature"]}
    )
    assert [paper.title for paper in recent] == ["Test Paper 1", "Test Paper 3"]
    assert [paper.title for paper in cited] == ["Test Paper 1", "Test Paper 3"]
    assert [paper.title for paper in venues] == ["Test Paper 1"]
    assert [paper.title for paper in older] == ["Test Paper 1", "Test Paper 2"]
    assert [paper.title for paper in venue_or_unknown] == [
        "Test Paper 1",
        "Unknown venue",
    ]


def test_llm_filter_uses_real_local_http_server(llm_server: str, sample_papers: list[Paper]) -> None:
    engine = LLMFilterEngine(
        {
            "model": "gemma3:4b",
            "base_url": llm_server,
            "temperature": 0.1,
            "timeout_seconds": 2,
            "max_retries": 1,
        }
    )
    result = engine.apply_filter(
        sample_papers[0],
        {"prompt": "Is this relevant? {abstract}", "keep_values": ["yes"]},
    )
    assert result == "yes"


def test_llm_filter_handles_missing_abstract_and_connection_failure() -> None:
    engine = LLMFilterEngine(
        {
            "base_url": "http://127.0.0.1:1",
            "timeout_seconds": 1,
            "max_retries": 1,
        }
    )
    assert (
        engine.apply_filter(
            Paper(title="No abstract"),
            {"prompt": "Classify: {abstract}"},
        )
        == "no_abstract"
    )
    assert (
        engine.apply_filter(
            Paper(title="Unavailable", abstract="Content"),
            {"prompt": "Classify: {abstract}"},
        )
        == "error"
    )


def test_runner_initialization(config_path: Path, tmp_path: Path) -> None:
    output_dir = tmp_path / "custom-output"
    runner = MultiPhaseSearchRunner(config_path, output_dir=output_dir)
    assert "phase_1_foundation" in runner.search_phases
    assert "test_filter" in runner.llm_filters
    assert runner.llm_engine is not None
    assert runner.output_dir == output_dir.resolve()


def test_llm_phase_filter_records_retained_provenance(
    config_path: Path,
    llm_server: str,
    sample_papers: list[Paper],
    tmp_path: Path,
) -> None:
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    assert runner.llm_engine is not None
    runner.llm_engine.base_url = llm_server
    paper = sample_papers[0]
    runner.all_phased_papers[paper.canonical_id] = PhasedPaper(
        paper=paper,
        discovered_in_phase="phase_1_foundation",
    )
    kept = runner.apply_llm_filters([paper], "phase_1_foundation")
    assert kept == [paper]
    assert runner.all_phased_papers[paper.canonical_id].llm_filters_passed == {"test_filter": "yes"}

    runner.llm_filters["test_filter"]["keep_values"] = ["no"]
    assert runner.apply_llm_filters([paper], "phase_1_foundation") == []
    runner.llm_filters["test_filter"].pop("keep_values")
    runner.llm_filters["test_filter"]["keep_categories"] = ["yes"]
    assert runner.apply_llm_filters([paper], "phase_1_foundation") == [paper]
    assert runner.apply_llm_filters([paper], "unconfigured_phase") == [paper]


def test_no_llm_configuration_returns_original_list(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config: {}\n", encoding="utf-8")
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    papers = [Paper(title="Paper", abstract="Text")]
    assert runner.apply_llm_filters(papers, "phase") is papers


def test_phase_overlap_calculation(config_path: Path, tmp_path: Path) -> None:
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    runner.all_phased_papers = {
        "id1": PhasedPaper(
            paper=Paper(title="Paper 1", abstract="Test"),
            discovered_in_phase="phase_1",
            phases_found_in=["phase_1", "phase_2"],
        ),
        "id2": PhasedPaper(
            paper=Paper(title="Paper 2", abstract="Test"),
            discovered_in_phase="phase_1",
        ),
        "id3": PhasedPaper(
            paper=Paper(title="Paper 3", abstract="Test"),
            discovered_in_phase="phase_2",
        ),
    }
    overlap = runner._calculate_phase_overlap()
    assert overlap["phase_1"]["phase_2"]["intersection"] == 1
    assert overlap["phase_1"]["phase_2"]["jaccard_similarity"] == pytest.approx(1 / 3)


def test_deduplication_and_phase_registry(config_path: Path, tmp_path: Path) -> None:
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    original = Paper(title="Same", abstract="First")
    duplicate = Paper(title="Same", abstract="Second")
    assert runner._deduplicate_papers([original, duplicate]) == [original]

    runner._record_phase_papers([original], "phase_1")
    runner._record_phase_papers([duplicate], "phase_2")
    runner._record_phase_papers([duplicate], "phase_2")
    phased = runner.all_phased_papers[original.canonical_id]
    assert phased.paper is original
    assert phased.phases_found_in == ["phase_1", "phase_2"]


def test_cross_phase_citation_validation(tmp_path: Path) -> None:
    config = {
        "project_config": {
            "search_phases": {
                "phase_1": {"queries": []},
                "phase_2": {"queries": [], "depends_on": ["phase_1"]},
            },
            "phase_integration": {
                "citation_validation": {
                    "enabled": True,
                    "min_cross_phase_citations": 1,
                }
            },
        }
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    foundation = Paper(title="Foundation", abstract="Base")
    later = Paper(
        title="Later",
        abstract="Follow-up",
        references=[foundation.canonical_id],
    )
    runner.all_phased_papers = {
        foundation.canonical_id: PhasedPaper(foundation, "phase_1"),
        later.canonical_id: PhasedPaper(later, "phase_2"),
    }
    result = runner.validate_cross_phase_citations()
    assert result["phase_2"]["papers_with_sufficient_citations"] == 1
    assert result["phase_2"]["citation_rate"] == 1


def test_cross_phase_citation_validation_can_be_disabled(config_path: Path, tmp_path: Path) -> None:
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    assert runner.validate_cross_phase_citations() == {}


def test_execute_phase_with_disabled_engines_is_hermetic(tmp_path: Path) -> None:
    config = {
        "project_config": {
            "search": {
                "term": "test",
                "query": "test",
                "engines": {},
                "clear_corpus": True,
                "resume": False,
            },
            "search_phases": {
                "phase_1": {
                    "name": "Hermetic phase",
                    "queries": ["test"],
                    "engines": {},
                    "deterministic_filters": {"min_year": 2020},
                }
            },
        }
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    runner = MultiPhaseSearchRunner(
        config_path,
        project_root=tmp_path,
        output_dir=tmp_path / "results",
    )
    assert runner.execute_phase("phase_1", runner.search_phases["phase_1"]) == []
    metadata = runner.phase_metadata["phase_1"]
    assert metadata.queries_executed == ["test"]
    assert metadata.papers_discovered == 0
    assert metadata.papers_final == 0
    assert not list(tmp_path.glob("tmp*.yaml"))


def test_empty_pipeline_writes_to_injected_output(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config: {}\n", encoding="utf-8")
    output_dir = tmp_path / "results"
    runner = MultiPhaseSearchRunner(config_path, output_dir=output_dir)
    runner.run()
    assert (output_dir / "combined_corpus.jsonl").read_text(encoding="utf-8") == ""
    metadata = json.loads((output_dir / "phase_metadata.json").read_text(encoding="utf-8"))
    assert metadata["total_unique_papers"] == 0
    assert metadata["phases"] == {}


def test_phase_pipeline_writes_phase_provenance(tmp_path: Path) -> None:
    config = {"project_config": {"search_phases": {"phase_1": {"name": "Empty phase", "queries": [], "engines": {}}}}}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    output_dir = tmp_path / "results"
    runner = MultiPhaseSearchRunner(
        config_path,
        project_root=tmp_path,
        output_dir=output_dir,
    )
    runner.run(specific_phase="phase_1")
    assert (output_dir / "phase_1_corpus.jsonl").is_file()
    metadata = json.loads((output_dir / "phase_metadata.json").read_text(encoding="utf-8"))
    assert metadata["phases"]["phase_1"]["papers_final"] == 0


def test_unknown_phase_fails_before_network(config_path: Path, tmp_path: Path) -> None:
    runner = MultiPhaseSearchRunner(config_path, output_dir=tmp_path / "output")
    with pytest.raises(ValueError, match="Phase 'missing' not found"):
        runner.run(specific_phase="missing")


def test_thin_cli_runs_from_outside_project(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent
    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config: {}\n", encoding="utf-8")
    output_dir = tmp_path / "cli-output"
    completed = subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "01_multi_phase_search.py"),
            "--config-path",
            str(config_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert (output_dir / "phase_metadata.json").is_file()
