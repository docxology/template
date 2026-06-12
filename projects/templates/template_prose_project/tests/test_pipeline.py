"""Tests for src.pipeline — uses real prose, real bib files, no mocks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.prose import analyze_files

from src.config import (
    BibliographyConfig,
    ProjectConfig,
    ProseAnalysisConfig,
    ReportConfig,
)
from pipeline_helpers import run_prose_pipeline_with_analysis

from src.pipeline import CheckResult
from src.pipeline.checks import (
    _check_bibliography,
    _check_citation_density,
    _check_grade_level,
    _check_h1_per_file,
    _check_no_skipped_levels,
)


def _make_project(tmp_path: Path, *, files: dict[str, str], bib: str) -> Path:
    """Create an isolated project root with manuscript + references.bib."""
    root = tmp_path / "proj"
    (root / "manuscript").mkdir(parents=True)
    for name, body in files.items():
        (root / "manuscript" / name).write_text(body, encoding="utf-8")
    (root / "manuscript" / "references.bib").write_text(bib, encoding="utf-8")
    return root


def _config(**overrides) -> ProjectConfig:
    return ProjectConfig(
        title="Test",
        prose=ProseAnalysisConfig(**overrides.get("prose", {})),
        bibliography=BibliographyConfig(**overrides.get("bibliography", {})),
        report=ReportConfig(),
    )


class TestRunProsePipeline:
    def test_passing_run(self, tmp_path: Path):
        files = {
            "00_abstract.md": (
                "# Abstract\n\n"
                "This paper [@k1] examines reproducibility carefully. "
                "We argue findings are important.\n"
            ),
            "01_intro.md": (
                "# Introduction\n\nThe field has grown rapidly [@k2].\n"
            ),
        }
        bib = "@article{k1, title={A}, year={2020}, author={X}}\n@article{k2, title={B}, year={2021}, author={Y}}\n"
        root = _make_project(tmp_path, files=files, bib=bib)

        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        assert artifacts.all_passed is True
        assert artifacts.total_words > 0
        assert (root / "output" / "manuscript_report.json").exists()
        assert (root / "output" / "checks.json").exists()

    def test_grade_level_out_of_band_fails(self, tmp_path: Path):
        files = {"00_abstract.md": "# Abstract\n\nShort plain text.\n"}
        bib = ""
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": 50.0, "target_grade_level_max": 60.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        assert artifacts.all_passed is False
        names = [c.name for c in artifacts.checks if not c.passed]
        assert "grade_level_in_band" in names

    def test_citation_density_floor(self, tmp_path: Path):
        files = {"00_abstract.md": "# Abstract\n\n" + "word " * 200 + ".\n"}
        bib = ""
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 5.0},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        names = [c.name for c in artifacts.checks if not c.passed]
        assert "citation_density_above_floor" in names

    def test_skipped_heading_levels_flagged(self, tmp_path: Path):
        files = {
            "00_abstract.md": "# A\n\n### Skipped heading.\n\nbody body body body.",
        }
        bib = ""
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0,
                   "forbid_skipped_levels": True},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        names = [c.name for c in artifacts.checks if not c.passed]
        assert "no_skipped_heading_levels" in names

    def test_missing_h1_flagged(self, tmp_path: Path):
        files = {"00_abstract.md": "## Only Subheading\n\nbody body."}
        root = _make_project(tmp_path, files=files, bib="")
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0,
                   "require_h1_per_section": True,
                   "forbid_skipped_levels": False},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        names = [c.name for c in artifacts.checks if not c.passed]
        assert "every_file_has_h1" in names

    def test_missing_citation_in_bib_fails(self, tmp_path: Path):
        files = {
            "00_abstract.md": "# A\n\nUnknown citation [@notinbib].\n",
        }
        bib = "@article{otherkey, title={X}, year={2020}, author={Z}}\n"
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": True},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        bib_check = next(c for c in artifacts.checks if c.name == "bibliography_consistency")
        assert bib_check.passed is False
        assert "notinbib" in bib_check.details["missing"]

    def test_unused_bib_warned_only(self, tmp_path: Path):
        files = {"00_abstract.md": "# A\n\nNo citations here."}
        bib = "@article{unused, title={X}, year={2020}, author={Z}}\n"
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": True, "fail_on_unused": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        bib_check = next(c for c in artifacts.checks if c.name == "bibliography_consistency")
        # Unused entries don't fail when fail_on_unused=False.
        assert bib_check.passed is True
        assert "unused" in bib_check.details["unused"]

    def test_missing_bib_handled(self, tmp_path: Path):
        # No references.bib at all.
        files = {"00_abstract.md": "# A\n\nbody."}
        root = tmp_path / "proj"
        (root / "manuscript").mkdir(parents=True)
        for name, body in files.items():
            (root / "manuscript" / name).write_text(body, encoding="utf-8")
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        bib_check = next(c for c in artifacts.checks if c.name == "bibliography_consistency")
        # fail_on_missing=False → check passes even when bib is absent
        assert bib_check.passed is True

    def test_no_write_outputs(self, tmp_path: Path):
        root = _make_project(tmp_path, files={"00_a.md": "# A\n\nbody"}, bib="")
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root, write_outputs=False)
        assert artifacts.report_path is None
        assert not (root / "output").exists()

    def test_unused_bib_fails_when_strict(self, tmp_path: Path):
        """Positive failure case for the fail_on_unused=True branch."""
        files = {"00_abstract.md": "# A\n\nNo citations here at all."}
        bib = (
            "@article{ghost1, title={X}, year={2020}, author={Z}}\n"
            "@article{ghost2, title={Y}, year={2021}, author={Q}}\n"
        )
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": False, "fail_on_unused": True},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        bib_check = next(c for c in artifacts.checks if c.name == "bibliography_consistency")
        assert bib_check.passed is False
        assert "ghost1" in bib_check.details["unused"]
        assert "ghost2" in bib_check.details["unused"]
        assert "unused" in bib_check.message

    def test_missing_bib_fails_when_strict(self, tmp_path: Path):
        """Absent bibliography file + fail_on_missing=True must fail the check."""
        files = {"00_abstract.md": "# A\n\nbody body."}
        root = tmp_path / "proj"
        (root / "manuscript").mkdir(parents=True)
        for name, body in files.items():
            (root / "manuscript" / name).write_text(body, encoding="utf-8")
        # Note: no references.bib written.
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": True},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        bib_check = next(c for c in artifacts.checks if c.name == "bibliography_consistency")
        assert bib_check.passed is False
        assert "not found" in bib_check.message


class TestOptionalChecks:
    """Verify config flags toggle whether structural checks are appended."""

    def test_disabled_h1_check_not_appended(self, tmp_path: Path):
        files = {"00_a.md": "## Subheading-only\n\nbody."}
        root = _make_project(tmp_path, files=files, bib="")
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0,
                   "require_h1_per_section": False,
                   "forbid_skipped_levels": False},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root, write_outputs=False)
        names = [c.name for c in artifacts.checks]
        assert "every_file_has_h1" not in names
        assert "no_skipped_heading_levels" not in names

    def test_disabled_skipped_check_not_appended(self, tmp_path: Path):
        files = {"00_a.md": "# A\n\nbody.\n\n#### Skipped"}
        root = _make_project(tmp_path, files=files, bib="")
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0,
                   "require_h1_per_section": True,
                   "forbid_skipped_levels": False},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root, write_outputs=False)
        names = [c.name for c in artifacts.checks]
        assert "no_skipped_heading_levels" not in names
        assert "every_file_has_h1" in names


class TestCheckUnits:
    """Per-check unit tests (positive AND negative outcome for every check)."""

    @staticmethod
    def _report(text: str = "# A\n\nbody body body."):
        return analyze_files({"f.md": text})

    def test_grade_level_positive(self):
        # Generous band — passes for any reasonable text.
        report = self._report()
        config = _config(prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0})
        result = _check_grade_level(report, config)
        assert result.passed is True
        assert result.name == "grade_level_in_band"
        assert "min" in result.details and "max" in result.details

    def test_grade_level_negative(self):
        # Impossible band — fails.
        report = self._report()
        config = _config(prose={"target_grade_level_min": 100.0, "target_grade_level_max": 200.0})
        result = _check_grade_level(report, config)
        assert result.passed is False
        assert result.details["value"] < 100.0

    def test_citation_density_positive(self):
        # Floor of 0 always passes.
        report = self._report("# A\n\n[@k1] body. [@k2] body body.")
        config = _config(prose={"citation_density_min_per_1000": 0.0})
        result = _check_citation_density(report, config)
        assert result.passed is True
        assert result.details["citation_count"] == 2

    def test_citation_density_negative(self):
        report = self._report("# A\n\n" + ("word " * 200))
        config = _config(prose={"citation_density_min_per_1000": 10.0})
        result = _check_citation_density(report, config)
        assert result.passed is False
        assert result.details["density_per_1000"] < 10.0

    def test_no_skipped_levels_positive(self):
        # Contiguous levels — passes.
        report = self._report("# A\n\nbody.\n\n## B\n\nbody.\n\n### C\n\nbody.")
        result = _check_no_skipped_levels(report, _config())
        assert result.passed is True
        assert result.details["offending_files"] == []

    def test_no_skipped_levels_negative(self):
        report = self._report("# A\n\nbody.\n\n#### Skipped\n\nbody.")
        result = _check_no_skipped_levels(report, _config())
        assert result.passed is False
        assert "f.md" in result.details["offending_files"]

    def test_h1_per_file_positive(self):
        report = self._report("# Heading\n\nbody.")
        result = _check_h1_per_file(report, _config())
        assert result.passed is True
        assert result.details["offending_files"] == []

    def test_h1_per_file_negative(self):
        report = self._report("## Only Subheading\n\nbody.")
        result = _check_h1_per_file(report, _config())
        assert result.passed is False
        assert "f.md" in result.details["offending_files"]

    def test_bibliography_positive(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text("@article{k1, title={A}, year={2020}, author={X}}\n", encoding="utf-8")
        report = self._report("# A\n\nCite [@k1].")
        config = _config(bibliography={"fail_on_missing": True, "fail_on_unused": True})
        result = _check_bibliography(report, config, bib_path=bib)
        assert result.passed is True
        assert result.details["missing"] == []
        assert result.details["unused"] == []

    def test_bibliography_negative_missing(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text("@article{other, title={A}, year={2020}, author={X}}\n", encoding="utf-8")
        report = self._report("# A\n\nCite [@nope].")
        config = _config(bibliography={"fail_on_missing": True, "fail_on_unused": False})
        result = _check_bibliography(report, config, bib_path=bib)
        assert result.passed is False
        assert "nope" in result.details["missing"]

    def test_bibliography_negative_unused_strict(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text("@article{lonely, title={A}, year={2020}, author={X}}\n", encoding="utf-8")
        report = self._report("# A\n\nNo citations.")
        config = _config(bibliography={"fail_on_missing": True, "fail_on_unused": True})
        result = _check_bibliography(report, config, bib_path=bib)
        assert result.passed is False
        assert "lonely" in result.details["unused"]

    def test_bibliography_missing_file_lenient(self, tmp_path: Path):
        # No bib file; fail_on_missing=False → check passes.
        report = self._report()
        config = _config(bibliography={"fail_on_missing": False, "fail_on_unused": False})
        result = _check_bibliography(
            report,
            config,
            bib_path=tmp_path / "absent.bib",
        )
        assert result.passed is True
        assert "not found" in result.message


class TestCitationExtractionViaPipeline:
    """Pandoc-flavour citation forms must round-trip through the pipeline.

    These exercise the bibliography consistency check via real files +
    real prose so the contract is reported end-to-end.
    """

    def _run(self, tmp_path: Path, prose_body: str, bib_keys: list[str]):
        files = {"00_a.md": "# A\n\n" + prose_body}
        bib = "\n".join(
            f"@article{{{k}, title={{T}}, year={{2020}}, author={{Z}}}}"
            for k in bib_keys
        )
        root = _make_project(tmp_path, files=files, bib=bib)
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": True, "fail_on_unused": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        return next(c for c in artifacts.checks if c.name == "bibliography_consistency")

    def test_bracketed_citation(self, tmp_path: Path):
        bib_check = self._run(tmp_path, "Cite [@bracket].", ["bracket"])
        assert bib_check.passed is True

    def test_bare_citation(self, tmp_path: Path):
        # Prose with bare @bare not inside brackets.
        bib_check = self._run(tmp_path, "Cite @bare in line.", ["bare"])
        assert bib_check.passed is True

    def test_suppression_marker(self, tmp_path: Path):
        # [-@key] suppresses the author name but still cites the key.
        bib_check = self._run(tmp_path, "Per [-@suppressed] this is true.", ["suppressed"])
        assert bib_check.passed is True

    def test_locator_after_key(self, tmp_path: Path):
        # [@key, p. 5] adds a page locator; the key should still resolve.
        bib_check = self._run(tmp_path, "See [@k, p. 5].", ["k"])
        assert bib_check.passed is True

    def test_locator_with_page_range(self, tmp_path: Path):
        bib_check = self._run(tmp_path, "See [@k, pp. 1-10].", ["k"])
        assert bib_check.passed is True

    def test_multiple_citations_in_one_bracket(self, tmp_path: Path):
        bib_check = self._run(tmp_path, "Cite [@a; @b].", ["a", "b"])
        assert bib_check.passed is True

    def test_pandoc_crossref_not_cited(self, tmp_path: Path):
        """[@sec:foo], [@fig:foo] etc. resolve via pandoc-crossref, NOT the bibliography."""
        # The bib intentionally does NOT contain sec:foo; the check must still pass.
        bib_check = self._run(
            tmp_path,
            "See [@sec:methods] and [@fig:plot] and [@tbl:summary].",
            [],
        )
        assert bib_check.passed is True
        assert bib_check.details["missing"] == []


class TestProseRunArtifacts:
    def test_to_dict_round_trips(self, tmp_path: Path):
        root = _make_project(
            tmp_path,
            files={"00_a.md": "# A\n\nbody body body."},
            bib="",
        )
        config = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0},
            bibliography={"fail_on_missing": False},
        )
        artifacts = run_prose_pipeline_with_analysis(config, project_root=root)
        payload = artifacts.to_dict()
        assert isinstance(payload, dict)
        assert payload["all_passed"] is True
        assert payload["total_words"] == artifacts.total_words
        assert isinstance(payload["checks"], list)
        assert all("name" in c and "passed" in c for c in payload["checks"])
        # Manuscript echoed back.
        assert "files" in payload["manuscript"]


class TestCheckResult:
    def test_default_message_and_details(self):
        c = CheckResult(name="x", passed=True)
        assert c.message == ""
        assert c.details == {}
        assert c.to_dict() == {
            "name": "x",
            "passed": True,
            "message": "",
            "details": {},
        }


class TestLongSentenceThresholdWired:
    """Confirm config.prose.long_sentence_threshold reaches analyze_quality."""

    def test_low_threshold_flags_more_sentences(self, tmp_path: Path):
        sentence = "This is a sentence with " + " ".join(["filler"] * 12) + " words."
        files = {"00_a.md": "# A\n\n" + sentence}
        root = _make_project(tmp_path, files=files, bib="")
        # Threshold below the sentence's word count → flagged.
        cfg_low = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0,
                   "long_sentence_threshold": 5},
            bibliography={"fail_on_missing": False},
        )
        artifacts_low = run_prose_pipeline_with_analysis(cfg_low, project_root=root, write_outputs=False)
        flagged_low = artifacts_low.manuscript_report.files[0].quality.long_sentence_count

        # Threshold well above the sentence's word count → not flagged.
        cfg_high = _config(
            prose={"target_grade_level_min": -10.0, "target_grade_level_max": 30.0,
                   "citation_density_min_per_1000": 0.0,
                   "long_sentence_threshold": 200},
            bibliography={"fail_on_missing": False},
        )
        artifacts_high = run_prose_pipeline_with_analysis(cfg_high, project_root=root, write_outputs=False)
        flagged_high = artifacts_high.manuscript_report.files[0].quality.long_sentence_count

        assert flagged_low > flagged_high
        assert flagged_high == 0
