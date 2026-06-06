"""Tests for the validation CLI ``prose-quality`` command (no mocks)."""

from __future__ import annotations

import argparse

import pytest

from infrastructure.validation.cli import main as cli

AI_PROSE = (
    "It is worth noting that we delve into a rich tapestry of results. "
    "Moreover, this plays a crucial role in the realm of discovery."
)


def _args(**kw):
    base = {"path": "", "json": False, "fail_on_flags": False}
    base.update(kw)
    return argparse.Namespace(**base)


class TestProseQualityCommand:
    def test_clean_file_exits_zero(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("Ants forage. They return. The colony follows the trail home.", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            cli.validate_prose_quality_command(_args(path=str(f), fail_on_flags=True))
        assert exc.value.code == 0

    def test_ai_file_fails_when_requested(self, tmp_path):
        f = tmp_path / "ai.md"
        f.write_text(AI_PROSE, encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            cli.validate_prose_quality_command(_args(path=str(f), fail_on_flags=True))
        assert exc.value.code == 1

    def test_advisory_by_default_exits_zero(self, tmp_path):
        f = tmp_path / "ai.md"
        f.write_text(AI_PROSE, encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            cli.validate_prose_quality_command(_args(path=str(f), fail_on_flags=False))
        assert exc.value.code == 0

    def test_directory_scan(self, tmp_path):
        (tmp_path / "a.md").write_text(AI_PROSE, encoding="utf-8")
        (tmp_path / "b.md").write_text("Plain sentence one. Plain sentence two here.", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            cli.validate_prose_quality_command(_args(path=str(tmp_path), fail_on_flags=True))
        assert exc.value.code == 1

    def test_missing_path(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            cli.validate_prose_quality_command(_args(path=str(tmp_path / "nope.md")))
        assert exc.value.code == 1

    def test_json_output(self, tmp_path, caplog):
        import logging

        f = tmp_path / "ai.md"
        f.write_text(AI_PROSE, encoding="utf-8")
        with caplog.at_level(logging.INFO):
            with pytest.raises(SystemExit):
                cli.validate_prose_quality_command(_args(path=str(f), json=True))
        assert "ai_term_per_1k" in caplog.text
