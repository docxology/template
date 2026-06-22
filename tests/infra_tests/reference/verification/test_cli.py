"""CLI tests for reference verification (no mocks)."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.reference.verification.cli import main


def _write_bib(tmp_path: Path, body: str) -> Path:
    bib = tmp_path / "refs.bib"
    bib.write_text(body, encoding="utf-8")
    return bib


class TestVerifyCommand:
    def test_offline_unchecked_exits_zero(self, tmp_path: Path):
        bib = _write_bib(tmp_path, "@article{a, title={X}, year={2020}, doi={10.1/x}}\n")
        rc = main(["verify", str(bib), "--cache", str(tmp_path / "c.db")])
        assert rc == 0  # unchecked is not blocking

    def test_anachronism_fails(self, tmp_path: Path):
        bib = _write_bib(tmp_path, "@article{a, title={X}, year={2099}, doi={10.1/x}}\n")
        rc = main(["verify", str(bib), "--as-of-year", "2026", "--no-cache"])
        assert rc == 1

    def test_warn_only_forces_zero(self, tmp_path: Path):
        bib = _write_bib(tmp_path, "@article{a, title={X}, year={2099}, doi={10.1/x}}\n")
        rc = main(["verify", str(bib), "--as-of-year", "2026", "--no-cache", "--warn-only"])
        assert rc == 0

    def test_json_output(self, tmp_path: Path, capsys):
        bib = _write_bib(tmp_path, "@article{a, title={X}, year={2020}, doi={10.1/x}}\n")
        rc = main(["verify", str(bib), "--no-cache", "--json"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["counts"]["unchecked"] == 1
        assert payload["verdicts"][0]["citation_key"] == "a"

    def test_missing_file(self, tmp_path: Path):
        rc = main(["verify", str(tmp_path / "nope.bib"), "--no-cache"])
        assert rc == 2


class TestSchemaCommand:
    def test_schema_emits_valid_json(self, capsys):
        rc = main(["schema"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert "subcommands" in payload
        assert "verify" in payload["subcommands"]


class TestCacheClearCommand:
    def test_cache_clear(self, tmp_path: Path):
        from infrastructure.reference.verification.cache import ResolutionCache
        from infrastructure.search.literature.models import Paper

        cache_path = tmp_path / "c.db"
        ResolutionCache(cache_path).put("k", Paper(id="x", title="T"))
        rc = main(["cache-clear", "--cache", str(cache_path)])
        assert rc == 0
        assert ResolutionCache(cache_path).clear() == 0
