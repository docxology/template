"""Fresh bibliography integrity for the committed prose manuscript.

Editorial counts and readability vary with current wording; they are derived
values, not frozen quantitative baselines. This lane checks that actual source
citations resolve against the current bibliography, never stored output reports.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_prose_project"
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.prose import analyze_manuscript  # noqa: E402


from template_prose_project.pipeline.config import load_project_config  # noqa: E402
from template_prose_project.pipeline.prose_facade import parse_bib_keys  # noqa: E402


def test_bibliography_consistency_claim_rederives_from_source() -> None:
    """Every citation in the committed manuscript must resolve in its bibliography."""

    config = load_project_config(PROJECT_ROOT / "manuscript" / "config.yaml")
    manuscript_dir = (PROJECT_ROOT / config.manuscript_dir).resolve()
    report = analyze_manuscript(
        manuscript_dir,
        long_sentence_threshold=config.prose.long_sentence_threshold,
    )
    bib_keys = parse_bib_keys(manuscript_dir / "references.bib")
    cited_keys = set(report.citation_keys)
    missing = cited_keys - bib_keys

    # The claim: no cited key is missing from the bib.
    assert missing == set(), f"cited keys missing from bib: {sorted(missing)}"
