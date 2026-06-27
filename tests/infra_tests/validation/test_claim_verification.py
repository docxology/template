from __future__ import annotations

from pathlib import Path

from infrastructure.validation.output import claim_verification as mod


class _FakeResult:
    def __init__(self, title: str, url: str = "", highlights: list[str] | None = None, summary: str = "", text: str = "") -> None:
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


class _FakeVerifier:
    def verify_claims(self, claims: list[str]):
        return [
            mod.ClaimVerdict(
                claim=claim,
                verdict="supported",
                confidence=0.9,
                evidence_title="Fake source",
                evidence_url="https://example.com/source",
                evidence_snippet="supported",
                evidence_count=1,
            )
            for claim in claims
        ]


def test_fact_check_verifier_scores_supported_and_insufficient() -> None:
    verifier = mod.FactCheckVerifier(client=_FakeClient())
    supported = verifier.verify_claim("We observed 12 participants in the cohort.")
    insufficient = verifier.verify_claim("The moon is made of cheese.")

    assert supported.verdict == "supported"
    assert insufficient.verdict == "insufficient"


def test_verify_project_claims_extracts_candidates_and_summarizes(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    manuscript_dir = project_root / "manuscript"
    manuscript_dir.mkdir(parents=True)
    (manuscript_dir / "config.yaml").write_text(
        "validation:\n  claim_verification:\n    enabled: true\n",
        encoding="utf-8",
    )
    (manuscript_dir / "01_intro.md").write_text(
        "- We observed 12 participants in the cohort.\n\nThe method reduced error by 15%.",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod.FactCheckVerifier, "from_env", classmethod(lambda cls, **kwargs: _FakeVerifier()))

    report = mod.verify_project_claims(project_root)

    assert len(report.claims) == 2
    assert report.summary()["supported"] == 2
