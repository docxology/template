"""Tests for the per-format on/off toggle in RenderingConfig.

Covers:
- Defaults preserve historical behavior (PDF + HTML + slides on; DOCX + EPUB off).
- ``from_env`` honors ``ENABLE_<FORMAT>`` env vars (case-insensitive).
- ``from_project_config`` honors a ``render.formats`` block in config.yaml.
- An unrecognized ``render.formats`` shape (string instead of mapping) falls
  back to defaults rather than raising.
"""

from __future__ import annotations

from infrastructure.rendering.config import RenderingConfig


def test_defaults_preserve_legacy_behavior() -> None:
    cfg = RenderingConfig()
    assert cfg.enable_pdf is True
    assert cfg.enable_html is True
    assert cfg.enable_slides is True
    assert cfg.enable_docx is False
    assert cfg.enable_epub is False


def test_from_env_honors_enable_flags() -> None:
    env = {
        "ENABLE_PDF": "0",
        "ENABLE_HTML": "false",
        "ENABLE_SLIDES": "NO",
        "ENABLE_DOCX": "1",
        "ENABLE_EPUB": "yes",
    }
    cfg = RenderingConfig.from_env(env=env)
    assert cfg.enable_pdf is False
    assert cfg.enable_html is False
    assert cfg.enable_slides is False
    assert cfg.enable_docx is True
    assert cfg.enable_epub is True


def test_from_env_ignores_unset_keys() -> None:
    cfg = RenderingConfig.from_env(env={})
    assert cfg.enable_pdf is True
    assert cfg.enable_docx is False


def test_from_project_config_reads_render_block() -> None:
    yaml_mapping = {
        "render": {
            "formats": {
                "pdf": False,
                "html": True,
                "docx": True,
                "epub": True,
            }
        }
    }
    cfg = RenderingConfig.from_project_config(yaml_mapping, env={})
    assert cfg.enable_pdf is False
    assert cfg.enable_html is True
    assert cfg.enable_slides is True  # defaulted — not in yaml
    assert cfg.enable_docx is True
    assert cfg.enable_epub is True


def test_from_project_config_missing_block_returns_defaults() -> None:
    cfg = RenderingConfig.from_project_config({}, env={})
    assert cfg.enable_pdf is True
    assert cfg.enable_docx is False


def test_from_project_config_none_input_returns_env_defaults() -> None:
    cfg = RenderingConfig.from_project_config(None, env={})
    assert cfg.enable_pdf is True


def test_from_project_config_malformed_formats_falls_back() -> None:
    """If render.formats is not a mapping, fall back to defaults."""
    yaml_mapping = {"render": {"formats": "not-a-dict"}}
    cfg = RenderingConfig.from_project_config(yaml_mapping, env={})
    assert cfg.enable_pdf is True
    assert cfg.enable_docx is False


def test_new_dirs_default_paths() -> None:
    cfg = RenderingConfig()
    assert cfg.docx_dir == "output/docx"
    assert cfg.epub_dir == "output/epub"


def test_pipeline_skip_branches_present() -> None:
    """The orchestrator must emit `[skip]` lines for disabled formats.

    Verified by reading the source of the orchestrator — we don't run a full
    pipeline here. This is a guard against the skip-branches being deleted.
    """
    from pathlib import Path

    source = Path("infrastructure/rendering/pipeline.py").read_text()
    assert "[skip] PDF rendering disabled" in source
    assert "[skip] HTML rendering disabled" in source
    assert "_render_combined_docx" in source
    assert "_render_combined_epub" in source


def test_combined_html_skips_missing_transmission_bookends(tmp_path) -> None:
    """Combined HTML should survive PDF-side cleanup of generated bookends."""
    from infrastructure.publishing.transmission_bookends import BEGIN_FILENAME, END_FILENAME
    from infrastructure.rendering.pipeline import _html_combined_source_files

    body = tmp_path / "01_body.md"
    body.write_text("# Body\n", encoding="utf-8")
    missing_regular = tmp_path / "02_missing.md"

    filtered = _html_combined_source_files(
        [
            tmp_path / BEGIN_FILENAME,
            body,
            tmp_path / END_FILENAME,
        ]
    )
    with_regular_missing = _html_combined_source_files([body, missing_regular])

    assert filtered == [body]
    assert with_regular_missing == [body, missing_regular]
