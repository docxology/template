"""
Determinism-artifact, in-process analysis CLI, and citation-key
extraction edge cases.
"""

from __future__ import annotations
from pathlib import Path
import pytest
from template_search_project.analysis import _extract_citation_keys, check_determinism_artifacts


# ---------------------------------------------------------------------------
# Determinism-check empty cache directory
# ---------------------------------------------------------------------------


class TestDeterminismEmptyCache:
    """Cover the line-294 branch where ``output/search/cache`` exists
    but contains zero ``*.json`` files (an aborted prior run)."""

    def test_check_determinism_empty_cache_dir(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        (out / "search" / "cache").mkdir(parents=True)
        # No *.json files inside the cache dir on purpose.
        (out / "run_summary.json").write_text("{}", encoding="utf-8")
        mdir = tmp_path / "manuscript"
        mdir.mkdir()
        (mdir / "config.yaml").write_text("llm:\n  seed: 1\n  temperature: 0\n", encoding="utf-8")
        res = check_determinism_artifacts(tmp_path)
        assert res.status == "failed"
        assert any("cache directory empty" in i for i in res.details["issues"])
        assert res.details["findings"]["search_cache_files"] == 0


# ---------------------------------------------------------------------------
# Citation-key extraction edge case (empty after stripping prefixes)
# ---------------------------------------------------------------------------


class TestDeterminismSeedMissing:
    """Cover line 311 — seed absent from config.yaml is flagged."""

    def test_check_determinism_seed_missing(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        (out / "search" / "cache").mkdir(parents=True)
        (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
        (out / "run_summary.json").write_text("{}", encoding="utf-8")
        mdir = tmp_path / "manuscript"
        mdir.mkdir()
        # llm block present but no `seed` key.
        (mdir / "config.yaml").write_text("llm:\n  temperature: 0\n", encoding="utf-8")
        res = check_determinism_artifacts(tmp_path)
        assert res.status == "failed"
        assert any("llm.seed not set" in i for i in res.details["issues"])

    def test_check_determinism_no_config_yaml(self, tmp_path: Path) -> None:
        """Cover the 300->315 branch: config.yaml absent entirely.

        Determinism check still runs (cache present, run_summary present)
        but the seed/temperature subsection is skipped silently and the
        result is 'passed' iff no other issues were collected.
        """
        out = tmp_path / "output"
        (out / "search" / "cache").mkdir(parents=True)
        (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
        (out / "run_summary.json").write_text("{}", encoding="utf-8")
        # No manuscript/config.yaml on purpose.
        res = check_determinism_artifacts(tmp_path)
        assert res.status == "passed"
        # findings dict should not contain llm_seed / llm_temperature
        # because the config-yaml-absent branch skips that entirely.
        assert "llm_seed" not in res.details["findings"]


class TestAnalysisCLIInProcess:
    """Cover ``analysis._cli`` in-process so coverage tracks it (subprocess
    invocation does not contribute to ``--cov`` totals)."""

    def test_cli_bibliography_completeness_pass(self, tmp_path: Path) -> None:
        from template_search_project import analysis

        md = tmp_path / "manuscript"
        md.mkdir()
        (md / "references.bib").write_text("@article{k1,\n title={x}\n}\n", encoding="utf-8")
        (md / "01_intro.md").write_text("Cite [@k1].", encoding="utf-8")
        argv = [
            "--stage",
            "bibliography_completeness",
            "--project-root",
            str(tmp_path),
        ]
        with pytest.raises(SystemExit) as excinfo:
            analysis._cli(argv)
        assert excinfo.value.code == 0

    def test_cli_determinism_check_routes_correctly(self, tmp_path: Path) -> None:
        from template_search_project import analysis

        # Set up an empty repo skeleton — determinism_check will fail
        # (no run_summary.json, etc.) which is fine; we only need to
        # exercise the CLI dispatch.
        argv = [
            "--stage",
            "determinism_check",
            "--project-root",
            str(tmp_path),
        ]
        with pytest.raises(SystemExit) as excinfo:
            analysis._cli(argv)
        # Exit code is 1 (failed) because run_summary missing — this is
        # the expected behaviour and it proves the dispatch + return-code
        # plumbing in _cli works.
        assert excinfo.value.code == 1


class TestCitationKeyExtractionEdge:
    """``_extract_citation_keys`` guards against tokens that become empty
    after stripping ``-+@`` (the ``token = token.lstrip(...)`` step)."""

    def test_empty_after_prefix_stripping_is_skipped(self) -> None:
        """``[@-]`` is a malformed pandoc cite — the inner token is just
        the prefix character, which strips to empty. The extractor must
        skip silently rather than emit an empty string into the key set.
        """
        keys = _extract_citation_keys("Garbage [@-] more")
        assert "" not in keys
        # The malformed cite contributes no key.
        assert keys == set()

    def test_mixed_valid_and_empty_token(self) -> None:
        keys = _extract_citation_keys("Real [@valid_key] and bad [@-]")
        assert keys == {"valid_key"}
