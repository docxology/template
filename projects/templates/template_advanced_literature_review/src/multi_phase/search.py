"""Advanced Multi-Phase Literature Search with LLM Filtering.

Executes a multi-phase search strategy where each phase can build on
previous phases, apply both deterministic and LLM-based filters, and
maintain detailed phase metadata for analysis.

Usage:
    python 01_multi_phase_search.py [--config-path manuscript/config.yaml]
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import requests
import yaml

from config_loader import _load_yaml
from literature.corpus import Corpus
from literature.models import Paper
from literature.search_runner import run_literature_search

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


@dataclass
class PhaseMetadata:
    """Metadata for a search phase execution."""

    phase_id: str
    name: str
    description: str
    start_time: float
    end_time: float | None = None
    queries_executed: list[str] = field(default_factory=list)
    papers_discovered: int = 0
    papers_after_deterministic_filters: int = 0
    papers_after_llm_filters: int = 0
    papers_final: int = 0
    deterministic_filters_applied: dict[str, Any] = field(default_factory=dict)
    llm_filters_applied: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class PhasedPaper:
    """A paper plus the phase-level provenance accumulated for it."""

    paper: Paper
    discovered_in_phase: str
    phases_found_in: list[str] = field(default_factory=list)
    deterministic_filters_passed: dict[str, bool] = field(default_factory=dict)
    llm_filters_passed: dict[str, str] = field(default_factory=dict)
    cross_phase_citations: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure the discovery phase is always present in provenance."""
        if self.discovered_in_phase not in self.phases_found_in:
            self.phases_found_in.insert(0, self.discovered_in_phase)


class LLMFilterEngine:
    """Engine for applying LLM-based content filters to papers."""

    def __init__(self, llm_config: dict[str, Any]):
        self.model: str = llm_config.get("model", "gemma3:4b")
        self.base_url: str = llm_config.get("base_url", "http://localhost:11434")
        self.temperature: float = llm_config.get("temperature", 0.1)
        self.timeout: int = llm_config.get("timeout_seconds", 120)
        self.max_retries: int = llm_config.get("max_retries", 3)

    def apply_filter(self, paper: Paper, filter_config: dict[str, Any]) -> str:
        """Apply an LLM filter to a paper's abstract. Returns the classification."""
        if not paper.abstract or not paper.abstract.strip():
            return "no_abstract"

        prompt = filter_config["prompt"].format(abstract=paper.abstract)

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": self.temperature},
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()
                answer = str(result.get("response", "")).strip().lower()

                # Clean up common single-label response punctuation without
                # altering punctuation inside a legitimate category name.
                answer = answer.strip(" \t\r\n\"'.")

                return answer

            except (requests.RequestException, ValueError, TypeError) as exc:
                logger.warning("LLM filter attempt %d failed: %s", attempt + 1, exc)
                if attempt == self.max_retries - 1:
                    return "error"
                time.sleep(2**attempt)

        return "error"


class MultiPhaseSearchRunner:
    """Main runner for multi-phase literature search."""

    def __init__(
        self,
        config_path: Path,
        *,
        project_root: Path = PROJECT_ROOT,
        output_dir: Path | None = None,
    ):
        self.config_path = config_path
        self.project_root = project_root.resolve()
        self.output_dir = output_dir.resolve() if output_dir is not None else self.project_root / "output" / "data"
        self.config = _load_yaml(config_path)
        self.project_config = self.config.get("project_config", {})
        self.search_phases: dict[str, Any] = self.project_config.get("search_phases", {})
        self.llm_filters: dict[str, Any] = self.project_config.get("llm_filters", {})

        self.phase_metadata: dict[str, PhaseMetadata] = {}
        self.all_phased_papers: dict[str, PhasedPaper] = {}

        # Initialize LLM filter engine if filters are configured
        self.llm_engine: LLMFilterEngine | None = None
        if self.llm_filters:
            llm_config = self.project_config.get("llm_extraction", {})
            self.llm_engine = LLMFilterEngine(llm_config)

    def apply_deterministic_filters(self, papers: list[Paper], filters: dict[str, Any]) -> list[Paper]:
        """Apply deterministic filters to a list of papers."""
        filtered = list(papers)

        if "min_year" in filters:
            min_year = filters["min_year"]
            filtered = [p for p in filtered if p.year is None or p.year >= min_year]

        if "max_year" in filters:
            max_year = filters["max_year"]
            filtered = [p for p in filtered if p.year is None or p.year <= max_year]

        if "min_citation_count" in filters:
            min_citations = filters["min_citation_count"]
            filtered = [p for p in filtered if p.citation_count is None or p.citation_count >= min_citations]

        if "venue_patterns" in filters:
            venue_patterns = [p.lower() for p in filters["venue_patterns"]]

            def matches_venue(paper: Paper) -> bool:
                if not paper.venue:
                    return True  # No venue = keep (don't penalize missing data)
                venue_lower = paper.venue.lower()
                return any(pat in venue_lower for pat in venue_patterns)

            filtered = [p for p in filtered if matches_venue(p)]

        return filtered

    def apply_llm_filters(self, papers: list[Paper], phase_id: str) -> list[Paper]:
        """Apply LLM filters relevant to a specific phase."""
        if not self.llm_engine or not self.llm_filters:
            return papers

        filtered = []
        from tqdm import tqdm

        for paper in tqdm(papers, desc=f"LLM filtering {phase_id}"):
            keep_paper = True
            llm_results: dict[str, str] = {}

            for filter_id, filter_config in self.llm_filters.items():
                if phase_id not in filter_config.get("apply_to_phases", []):
                    continue

                result = self.llm_engine.apply_filter(paper, filter_config)
                llm_results[filter_id] = result

                # Check if this paper should be kept
                keep_values = filter_config.get("keep_values", [])
                keep_categories = filter_config.get("keep_categories", [])

                if keep_values and result not in keep_values:
                    keep_paper = False
                    break

                if keep_categories and result not in keep_categories:
                    keep_paper = False
                    break

            # Store LLM results
            canonical_id = paper.canonical_id
            if canonical_id in self.all_phased_papers:
                self.all_phased_papers[canonical_id].llm_filters_passed.update(llm_results)

            if keep_paper:
                filtered.append(paper)

        return filtered

    @staticmethod
    def _deduplicate_papers(papers: list[Paper]) -> list[Paper]:
        """Return the first record for each canonical paper identifier."""
        seen_ids: set[str] = set()
        unique_papers: list[Paper] = []
        for paper in papers:
            canonical_id = paper.canonical_id
            if canonical_id not in seen_ids:
                seen_ids.add(canonical_id)
                unique_papers.append(paper)
        return unique_papers

    def _record_phase_papers(self, papers: list[Paper], phase_id: str) -> None:
        """Merge retained papers into the cross-phase provenance registry."""
        for paper in papers:
            canonical_id = paper.canonical_id
            if canonical_id not in self.all_phased_papers:
                self.all_phased_papers[canonical_id] = PhasedPaper(
                    paper=paper,
                    discovered_in_phase=phase_id,
                )
                continue
            phases = self.all_phased_papers[canonical_id].phases_found_in
            if phase_id not in phases:
                phases.append(phase_id)

    def execute_phase(self, phase_id: str, phase_config: dict[str, Any]) -> list[Paper]:
        """Execute a single search phase using the existing search infrastructure."""
        logger.info(f"=== Starting phase: {phase_id} ===")

        metadata = PhaseMetadata(
            phase_id=phase_id,
            name=phase_config.get("name", phase_id),
            description=phase_config.get("description", ""),
            start_time=time.time(),
            depends_on=phase_config.get("depends_on", []),
        )

        queries = phase_config.get("queries", [])
        max_results_per_query = phase_config.get("max_results_per_query", 500)
        engines_config = phase_config.get("engines", {})

        metadata.queries_executed = queries

        all_papers: list[Paper] = []

        import argparse

        # Execute each query using the existing search runner
        for i, query in enumerate(queries):
            logger.info(f"Phase {phase_id} query {i + 1}/{len(queries)}: {query}")

            # Create a temporary config with this query to prevent override
            import copy
            import tempfile

            temp_config = copy.deepcopy(self.config)
            temp_config["project_config"]["search"]["query"] = query
            temp_config["project_config"]["search"]["max_results"] = max_results_per_query
            temp_config["project_config"]["search"]["engines"] = engines_config

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, dir=str(self.project_root)) as f:
                yaml.dump(temp_config, f)
                temp_config_path = Path(f.name)

            try:
                phase_output_dir = self.output_dir / "queries" / phase_id / str(i)

                args = argparse.Namespace(
                    config=str(temp_config_path),
                    query=query,
                    max_results=max_results_per_query,
                    start_year=None,
                    resume=False,
                    clear_corpus=True,
                    output_dir=str(phase_output_dir),
                    skip_arxiv=not engines_config.get("arxiv", False),
                    skip_s2=not engines_config.get("semantic_scholar", False),
                    skip_openalex=not engines_config.get("openalex", False),
                    skip_crossref=not engines_config.get("crossref", False),
                    skip_pubmed=not engines_config.get("pubmed", False),
                    skip_sovietrxiv=not engines_config.get("sovietrxiv", False),
                    skip_chinarxiv=not engines_config.get("chinarxiv", False),
                    skip_europepmc=not engines_config.get("europepmc", False),
                    skip_biorxiv=not engines_config.get("biorxiv", False),
                )

                corpus_path = run_literature_search(args, project_root=self.project_root)
                if corpus_path.exists():
                    query_corpus = Corpus.load(corpus_path)
                    all_papers.extend(query_corpus.papers)
                    logger.info(f"  Query {i + 1}: {len(query_corpus.papers)} papers")
                else:
                    logger.warning(f"  Query {i + 1}: No results file created")
            except (
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
                yaml.YAMLError,
            ) as exc:
                logger.error("  Query %d failed: %s", i + 1, exc)
            finally:
                if temp_config_path.exists():
                    temp_config_path.unlink()

        # Deduplicate within phase
        unique_papers = self._deduplicate_papers(all_papers)

        metadata.papers_discovered = len(unique_papers)
        logger.info(f"Phase {phase_id}: {len(unique_papers)} unique papers discovered")

        # Apply deterministic filters
        deterministic_filters = phase_config.get("deterministic_filters", {})
        if deterministic_filters:
            filtered_papers = self.apply_deterministic_filters(unique_papers, deterministic_filters)
            metadata.deterministic_filters_applied = deterministic_filters
            metadata.papers_after_deterministic_filters = len(filtered_papers)
            logger.info(f"Phase {phase_id}: {len(filtered_papers)} papers after deterministic filters")
        else:
            filtered_papers = unique_papers
            metadata.papers_after_deterministic_filters = len(filtered_papers)

        # Apply LLM filters
        llm_filtered_papers = self.apply_llm_filters(filtered_papers, phase_id)
        metadata.papers_after_llm_filters = len(llm_filtered_papers)

        # Track papers
        self._record_phase_papers(llm_filtered_papers, phase_id)

        metadata.papers_final = len(llm_filtered_papers)
        metadata.end_time = time.time()
        self.phase_metadata[phase_id] = metadata

        logger.info(
            f"Phase {phase_id} completed: {len(llm_filtered_papers)} final papers "
            f"({metadata.end_time - metadata.start_time:.1f}s)"
        )
        return llm_filtered_papers

    def validate_cross_phase_citations(self) -> dict[str, Any]:
        """Validate citation relationships between phases."""
        validation_config = self.project_config.get("phase_integration", {}).get("citation_validation", {})
        if not validation_config.get("enabled", False):
            return {}

        min_citations = validation_config.get("min_cross_phase_citations", 2)

        phase_papers: dict[str, set[str]] = {}
        for cid, phased in self.all_phased_papers.items():
            for phase_id in phased.phases_found_in:
                if phase_id not in phase_papers:
                    phase_papers[phase_id] = set()
                phase_papers[phase_id].add(cid)

        validation_results: dict[str, Any] = {}

        for phase_id in self.search_phases:
            if phase_id not in phase_papers:
                continue

            phase_config = self.search_phases[phase_id]
            depends_on = phase_config.get("depends_on", [])

            if not depends_on:
                continue

            citing_papers = 0
            total_papers = len(phase_papers[phase_id])

            for cid in phase_papers[phase_id]:
                paper = self.all_phased_papers[cid].paper
                citations_found = 0
                for dep_phase in depends_on:
                    if dep_phase in phase_papers:
                        for ref_id in paper.references:
                            if ref_id in phase_papers[dep_phase]:
                                citations_found += 1

                if citations_found >= min_citations:
                    citing_papers += 1

            validation_results[phase_id] = {
                "total_papers": total_papers,
                "papers_with_sufficient_citations": citing_papers,
                "citation_rate": citing_papers / total_papers if total_papers > 0 else 0,
                "min_required_citations": min_citations,
                "depends_on": depends_on,
            }

        return validation_results

    def _calculate_phase_overlap(self) -> dict[str, Any]:
        """Calculate overlap statistics between phases."""
        phase_sets: dict[str, set[str]] = {}
        for cid, phased in self.all_phased_papers.items():
            for phase_id in phased.phases_found_in:
                if phase_id not in phase_sets:
                    phase_sets[phase_id] = set()
                phase_sets[phase_id].add(cid)

        overlap_matrix: dict[str, Any] = {}
        for phase1 in phase_sets:
            overlap_matrix[phase1] = {}
            for phase2 in phase_sets:
                if phase1 != phase2:
                    intersection = len(phase_sets[phase1] & phase_sets[phase2])
                    union = len(phase_sets[phase1] | phase_sets[phase2])
                    jaccard = intersection / union if union > 0 else 0
                    overlap_matrix[phase1][phase2] = {
                        "intersection": intersection,
                        "jaccard_similarity": jaccard,
                    }

        return overlap_matrix

    def run(self, specific_phase: str | None = None) -> None:
        """Run the multi-phase search pipeline."""
        if specific_phase:
            if specific_phase not in self.search_phases:
                raise ValueError(f"Phase '{specific_phase}' not found in configuration")
            phases_to_run = [specific_phase]
        else:
            phases_to_run = list(self.search_phases.keys())

        # Execute phases in order
        for phase_id in phases_to_run:
            phase_config = self.search_phases[phase_id]
            self.execute_phase(phase_id, phase_config)

        # Validate cross-phase relationships
        citation_validation = self.validate_cross_phase_citations()

        # Save phase-specific corpora
        output_dir = self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        for phase_id in phases_to_run:
            phase_papers = [
                phased.paper for phased in self.all_phased_papers.values() if phase_id in phased.phases_found_in
            ]
            phase_corpus = Corpus(papers=phase_papers)
            phase_path = output_dir / f"{phase_id}_corpus.jsonl"
            phase_corpus.save(phase_path)
            logger.info(f"Saved {len(phase_papers)} papers to {phase_path}")

        # Save combined corpus
        all_paper_list = [phased.paper for phased in self.all_phased_papers.values()]
        combined_corpus = Corpus(papers=all_paper_list)
        combined_path = output_dir / "combined_corpus.jsonl"
        combined_corpus.save(combined_path)
        logger.info(f"Saved {len(all_paper_list)} total papers to {combined_path}")

        # Save phase metadata
        metadata_summary = {
            "phases": {pid: asdict(meta) for pid, meta in self.phase_metadata.items()},
            "citation_validation": citation_validation,
            "total_papers": len(all_paper_list),
            "total_unique_papers": len(self.all_phased_papers),
            "phase_overlap": self._calculate_phase_overlap(),
        }

        metadata_path = output_dir / "phase_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata_summary, f, indent=2)
        logger.info(f"Saved phase metadata to {metadata_path}")

        # Print summary
        print("\n=== Multi-Phase Search Summary ===")
        for phase_id, meta in self.phase_metadata.items():
            print(
                f"  {phase_id}: {meta.papers_discovered} discovered → "
                f"{meta.papers_after_deterministic_filters} after deterministic → "
                f"{meta.papers_final} final"
            )
        print(f"  Total unique papers: {len(all_paper_list)}")
        print(f"  Combined corpus: {combined_path}")


def main() -> None:  # pragma: no cover - exercised through the thin CLI script
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Multi-phase literature search")
    parser.add_argument(
        "--config-path",
        type=Path,
        default=PROJECT_ROOT / "manuscript" / "config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument("--phase", type=str, help="Run only a specific phase")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "data",
        help="Output directory for results",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    runner = MultiPhaseSearchRunner(args.config_path, output_dir=args.output_dir)
    runner.run(specific_phase=args.phase)


if __name__ == "__main__":
    main()
