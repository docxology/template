from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.validation.output import claim_verification as mod


class _FakeResult:
    def __init__(
        self, title: str, url: str = "", highlights: list[str] | None = None, summary: str = "", text: str = ""
    ) -> None:
        self.title = title
        self.url = url
        self.highlights = highlights or []
        self.summary = summary
        self.text = text


class _FakeResponse:
    def __init__(self, results: list[_FakeResult]) -> None:
        self.results = results


class _FakeClient:
    def search(self, query: str, **kwargs):
        if "12 participants" in query:
            return _FakeResponse(
                [
                    _FakeResult(
                        title="Cohort study reports 12 participants",
                        url="https://example.com/study",
                        highlights=["The cohort included 12 participants."],
                        summary="The study included 12 participants in the cohort.",
                        text="The cohort included 12 participants.",
                    )
                ]
            )
        return _FakeResponse([])


def test_fact_check_verifier_scores_supported_and_insufficient() -> None:
    verifier = mod.FactCheckVerifier(client=_FakeClient())
    supported = verifier.verify_claim("We observed 12 participants in the cohort.")
    insufficient = verifier.verify_claim("The moon is made of cheese.")

    assert supported.verdict == "supported"
    assert insufficient.verdict == "insufficient"


def test_generated_claims_check_only_ordered_admitted_deep_inputs(tmp_path: Path) -> None:
    from infrastructure.validation.content.manuscript_config import GENERATED_ORDERING_MARKER

    project_root = tmp_path / "project"
    authored = project_root / "manuscript"
    authored.mkdir(parents=True)
    (authored / "intro.md").write_text("The template reported 999 participants.", encoding="utf-8")
    generated = project_root / "output" / "manuscript"
    deep = generated / "volume" / "part" / "chapters"
    deep.mkdir(parents=True)
    (generated / "anchor.md").write_text("Compiler selection anchor.", encoding="utf-8")
    (generated / "config.yaml").write_text(
        f"{GENERATED_ORDERING_MARKER}\n"
        "units:\n"
        "  - directory: volume/part/chapters\n"
        "    chapters: [second.md, first.md]\n",
        encoding="utf-8",
    )
    second = "The unknown treatment reduced error by 73%."
    first = "The unsupported study reported 42 participants."
    (deep / "second.md").write_text(second, encoding="utf-8")
    (deep / "first.md").write_text(first, encoding="utf-8")
    (deep / "residue.md").write_text("Discarded output reported 888 participants.", encoding="utf-8")

    report = mod.verify_project_claims(project_root, verifier_factory=mod.FactCheckVerifier)

    assert report.skipped is False
    assert report.claims == [second, first]
    assert [verdict.verdict for verdict in report.verdicts] == ["insufficient", "insufficient"]
    assert report.summary()["supported"] == 0


def test_generated_claim_admission_error_is_not_a_skipped_report(tmp_path: Path) -> None:
    from infrastructure.validation.content.manuscript_config import GENERATED_ORDERING_MARKER
    from infrastructure.validation.rendered_snapshot import RenderedSnapshotError

    project_root = tmp_path / "project"
    generated = project_root / "output" / "manuscript"
    generated.mkdir(parents=True)
    (generated / "anchor.md").write_text("Compiler selection anchor.", encoding="utf-8")
    (generated / "config.yaml").write_text(
        f"{GENERATED_ORDERING_MARKER}\nunits:\n  - directory: chapters\n    chapters: [missing.md]\n",
        encoding="utf-8",
    )

    with pytest.raises(RenderedSnapshotError, match="missing.md"):
        mod.verify_project_claims(project_root, verifier_factory=mod.FactCheckVerifier)
