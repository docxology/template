"""No-mocks tests for src/render_orchestration.py — real render, real repo."""

from __future__ import annotations

import logging
import random
from pathlib import Path

import pytest
import yaml
from pypdf import PdfReader
from infrastructure.rendering.slide_deck import Slide

from paths import locate_repo_root, project_root
from render_orchestration import (
    DeckAuditFailure,
    DiligenceAuditFailure,
    load_deck_config,
    render_all_decks,
    render_one_length,
)


@pytest.fixture(scope="module")
def repo_root():
    return locate_repo_root(project_root())


def test_load_deck_config_reads_real_config():
    config = load_deck_config(project_root())
    assert config["pitch_subject"] == "template_template"
    assert "theme" in config


def test_load_deck_config_prefers_nested_schema_and_supports_legacy(tmp_path: Path):
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    config_path = manuscript / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "deck": {"pitch_subject": "legacy"},
                "project_config": {"deck": {"pitch_subject": "canonical"}},
            }
        ),
        encoding="utf-8",
    )
    assert load_deck_config(tmp_path)["pitch_subject"] == "canonical"

    config_path.write_text(yaml.safe_dump({"deck": {"pitch_subject": "legacy"}}), encoding="utf-8")
    assert load_deck_config(tmp_path)["pitch_subject"] == "legacy"


def test_render_one_length_writes_real_pdf(tmp_path: Path, repo_root):
    from deck_tokens import build_deck_tokens
    from infrastructure.rendering.slide_deck import DeckTheme

    tokens = build_deck_tokens(repo_root)
    logger = logging.getLogger("test")
    written = render_one_length(
        "short",
        project_root=tmp_path,
        repo_root=repo_root,
        manuscript_dir=project_root() / "manuscript",
        figures_dir=tmp_path / "figures",
        pdf_dir=tmp_path / "pdf",
        pptx_dir=tmp_path / "pptx",
        tokens=tokens,
        theme=DeckTheme(),
        source_base_url="https://github.com/docxology/template/blob/main/",
        render_pptx_fn=None,
        logger=logger,
    )
    assert len(written) == 1
    assert written[0].suffix == ".pdf"
    assert written[0].is_file()
    assert len(PdfReader(str(written[0])).pages) > 0

    # Standalone per-slide pages are also written as a side effect.
    standalone_dir = tmp_path / "output" / "slides_standalone" / "template_template_short"
    assert standalone_dir.is_dir()
    assert len(list(standalone_dir.glob("slide_*.md"))) > 0


def test_render_one_length_raises_on_audit_failure(tmp_path: Path, repo_root):
    logger = logging.getLogger("test")
    broken_manuscript = tmp_path / "manuscript"
    broken_manuscript.mkdir()
    (broken_manuscript / "deck_content_short.yaml").write_text(
        yaml.safe_dump({"title": "{{MISSING_TOKEN}}", "slides": []}), encoding="utf-8"
    )
    from infrastructure.rendering.slide_deck import DeckTheme

    with pytest.raises(DeckAuditFailure):
        render_one_length(
            "short",
            project_root=tmp_path,
            repo_root=repo_root,
            manuscript_dir=broken_manuscript,
            figures_dir=tmp_path / "figures",
            pdf_dir=tmp_path / "pdf",
            pptx_dir=tmp_path / "pptx",
            tokens={},
            theme=DeckTheme(),
            source_base_url="",
            render_pptx_fn=None,
            logger=logger,
        )


def test_render_one_length_raises_on_uncited_fact_slide(tmp_path: Path, repo_root):
    """Negative control (Proof-of-Detection): a fact-bearing slide with no
    `source` citation must block the render itself, not just the separate
    `scripts/30_audit_diligence.py` check — this is the exact gap Advisor
    flagged in this session's own deck content ('this deck audits itself'
    was false for diligence_audit.py until this gate was wired in)."""
    logger = logging.getLogger("test")
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "deck_content_short.yaml").write_text(
        yaml.safe_dump(
            {
                "title": "Deck",
                "slides": [
                    {
                        "kind": "content",
                        "title": "Uncited claim",
                        "bullets": ["{{EXEMPLAR_COUNT}} exemplars, no source given"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    from infrastructure.rendering.slide_deck import DeckTheme

    with pytest.raises(DiligenceAuditFailure, match="Uncited claim"):
        render_one_length(
            "short",
            project_root=tmp_path,
            repo_root=repo_root,
            manuscript_dir=manuscript_dir,
            figures_dir=tmp_path / "figures",
            pdf_dir=tmp_path / "pdf",
            pptx_dir=tmp_path / "pptx",
            tokens={"EXEMPLAR_COUNT": "20"},
            theme=DeckTheme(),
            source_base_url="",
            render_pptx_fn=None,
            logger=logger,
        )
    assert not (tmp_path / "pdf").exists() or not list((tmp_path / "pdf").glob("*.pdf"))


def test_render_all_decks_writes_real_artifacts(repo_root):
    """Six artifacts (PDF+PPTX) when python-pptx is installed, three (PDF-only)
    when it isn't — PPTX is an opt-in dependency (`uv sync --group rendering-pptx`),
    not a hard requirement, so this project's own isolated venv (as used by
    `execute_pipeline.py --core-only`) legitimately may not have it."""
    try:
        import pptx  # noqa: F401

        pptx_available = True
    except ImportError:
        pptx_available = False

    logger = logging.getLogger("test")
    written = render_all_decks(project_root(), repo_root, logger)
    assert len(written) == (6 if pptx_available else 3)
    for path in written:
        assert path.is_file()
        assert path.stat().st_size > 1000


def test_rendered_output_actually_reflects_token_value_not_a_cached_default(tmp_path: Path, repo_root):
    """Anti-circularity control: flip a real token's value and confirm the
    rendered PDF text changes accordingly — proves the pipeline actually
    threads the live-sourced value through to the artifact, rather than a
    hardcoded default that happens to match."""
    from content_loader import build_deck_content, load_deck_yaml
    from deck_tokens import build_deck_tokens
    from infrastructure.rendering.slide_deck import SlideBudget, filter_deck_for_budget, render_pdf

    tokens = build_deck_tokens(repo_root)
    raw = load_deck_yaml(project_root() / "manuscript" / "deck_content_short.yaml")

    real_deck = filter_deck_for_budget(build_deck_content(raw, tokens), SlideBudget.SHORT)
    real_pdf = render_pdf(real_deck, tmp_path / "real.pdf")
    real_text = "\n".join(p.extract_text() or "" for p in PdfReader(str(real_pdf)).pages)

    flipped_tokens = dict(tokens)
    flipped_tokens["PITCH_SUBJECT_TEST_COUNT"] = "999999"
    flipped_deck = filter_deck_for_budget(build_deck_content(raw, flipped_tokens), SlideBudget.SHORT)
    flipped_pdf = render_pdf(flipped_deck, tmp_path / "flipped.pdf")
    flipped_text = "\n".join(p.extract_text() or "" for p in PdfReader(str(flipped_pdf)).pages)

    assert tokens["PITCH_SUBJECT_TEST_COUNT"] in real_text
    assert "999999" not in real_text
    assert "999999" in flipped_text
    assert real_text != flipped_text


@pytest.mark.parametrize("slide_count", (0, 1, 11, 12, 38, 39, 58, 59, 80))
def test_budget_filter_is_prefix_preserving_and_non_mutating(slide_count):
    from infrastructure.rendering.slide_deck import DeckContent, SlideBudget, filter_deck_for_budget

    rng = random.Random(slide_count)
    original = tuple(
        Slide(
            title=f"generated-{index}",
            bullets=tuple(f"bullet-{rng.randrange(1000)}" for _ in range(index % 5)),
            kind=("content", "diagram", "stat", "quote", "section")[index % 5],
        )
        for index in range(slide_count)
    )
    deck = DeckContent(title="Property deck", slides=original)
    for budget in SlideBudget:
        filtered = filter_deck_for_budget(deck, budget)
        assert filtered.slides == original[: budget.max_slides]
        assert deck.slides == original


@pytest.mark.parametrize(
    "names",
    (
        (),
        ("A",),
        ("A", "B", "TOKEN_123"),
        tuple(f"TOKEN_{index}" for index in range(12)),
    ),
)
def test_token_resolution_handles_adversarial_uppercase_token_sequences(names):
    from token_resolution import resolve_tokens

    source = " ".join(f"{{{{{name}}}}}" for name in names)
    values = {name: f"value-{index}" for index, name in enumerate(names)}
    resolved = resolve_tokens(source, values)
    assert "{{" not in resolved
    assert all(value in resolved for value in values.values())
