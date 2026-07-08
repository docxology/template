from __future__ import annotations

import re
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.validation.output.prose_quality import load_project_config_yaml

logger = get_logger(__name__)

Verdict = Literal["supported", "contradicted", "insufficient"]
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_BULLET_RE = re.compile(r"(?m)^\s*[-*+]\s+(.*)$")
_CLAIM_HINT_RE = re.compile(
    r"(?:\b\d+(?:\.\d+)?%?\b|\b(?:first|last|largest|smallest|highest|lowest|only|significant|increase|decrease|reported|found|demonstrated|observed|measured|estimated|approximately|roughly)\b)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_PREPOSITIONAL_STOPWORDS = {
    "the",
    "and",
    "or",
    "for",
    "with",
    "from",
    "this",
    "that",
    "these",
    "those",
    "into",
    "over",
    "under",
    "between",
    "after",
    "before",
    "within",
    "without",
    "about",
    "above",
    "below",
    "there",
    "their",
    "them",
    "than",
    "then",
    "when",
    "where",
    "which",
    "while",
}


@dataclass(frozen=True)
class ClaimVerdict:
    """Data container for ClaimVerdict."""

    claim: str
    verdict: Verdict
    confidence: float
    evidence_title: str = ""
    evidence_url: str = ""
    evidence_snippet: str = ""
    evidence_count: int = 0


@dataclass
class ClaimVerificationReport:
    """Data container for ClaimVerificationReport."""

    claims: list[str] = field(default_factory=list)
    verdicts: list[ClaimVerdict] = field(default_factory=list)
    skipped: bool = False
    reason: str = ""

    def summary(self) -> dict[str, Any]:
        """Return a summary dict of counts and status."""
        counts = {"supported": 0, "contradicted": 0, "insufficient": 0}
        for verdict in self.verdicts:
            counts[verdict.verdict] += 1
        return {
            "claim_count": len(self.claims),
            "verdict_count": len(self.verdicts),
            "supported": counts["supported"],
            "contradicted": counts["contradicted"],
            "insufficient": counts["insufficient"],
            "skipped": self.skipped,
            "reason": self.reason,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "claims": list(self.claims),
            "verdicts": [verdict.__dict__ for verdict in self.verdicts],
            "summary": self.summary(),
        }


class FactCheckVerifier:
    """Data container for FactCheckVerifier."""

    def __init__(
        self,
        client: Any | None = None,
        *,
        max_workers: int = 4,
        max_results: int = 5,
        cache_size: int = 128,
    ) -> None:
        self.client = client
        self.max_workers = max_workers
        self.max_results = max_results
        self._cache: OrderedDict[str, ClaimVerdict] = OrderedDict()
        self._cache_size = cache_size

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str | None = None,
        max_workers: int = 4,
        max_results: int = 5,
    ) -> FactCheckVerifier | None:
        """Construct an instance from env."""
        try:
            from infrastructure.search.exa.client import ExaClient
            from infrastructure.search.exa.errors import ExaError
        except ImportError as exc:
            logger.info("Claim verification disabled: optional search dependency missing: %s", exc)
            return None
        try:
            client = ExaClient.from_env(base_url=base_url)
        except ExaError as exc:
            logger.info("Claim verification disabled: %s", exc)
            return None
        return cls(client=client, max_workers=max_workers, max_results=max_results)

    def _cache_get(self, claim: str) -> ClaimVerdict | None:
        if claim in self._cache:
            verdict = self._cache.pop(claim)
            self._cache[claim] = verdict
            return verdict
        return None

    def _cache_put(self, claim: str, verdict: ClaimVerdict) -> None:
        if claim in self._cache:
            self._cache.pop(claim, None)
        elif len(self._cache) >= self._cache_size:
            self._cache.popitem(last=False)
        self._cache[claim] = verdict

    def verify_claims(self, claims: list[str]) -> list[ClaimVerdict]:
        """Verify claims."""
        if not claims:
            return []
        results: list[ClaimVerdict | None] = [None] * len(claims)
        workers = max(1, min(self.max_workers, len(claims)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_index = {executor.submit(self.verify_claim, claim): index for index, claim in enumerate(claims)}
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                results[index] = future.result()
        return [result for result in results if result is not None]

    def verify_claim(self, claim: str) -> ClaimVerdict:
        """Verify claim."""
        claim = " ".join(claim.split())
        if not claim:
            return ClaimVerdict(claim="", verdict="insufficient", confidence=0.0, evidence_snippet="empty claim")
        cached = self._cache_get(claim)
        if cached is not None:
            return cached
        verdict = self._verify_uncached(claim)
        self._cache_put(claim, verdict)
        return verdict

    def _verify_uncached(self, claim: str) -> ClaimVerdict:
        if self.client is None:
            return ClaimVerdict(
                claim=claim,
                verdict="insufficient",
                confidence=0.0,
                evidence_snippet="Exa client unavailable",
            )
        try:
            response = self.client.search(claim, num_results=self.max_results, highlights=True, text=True, summary=True)
        except Exception as exc:
            return ClaimVerdict(
                claim=claim,
                verdict="insufficient",
                confidence=0.0,
                evidence_snippet=f"search failed: {exc}",
            )
        results = list(response.results or [])
        if not results:
            return ClaimVerdict(
                claim=claim,
                verdict="insufficient",
                confidence=0.0,
                evidence_snippet="no evidence found",
            )
        best_verdict = "insufficient"
        best_confidence = 0.0
        best_title = ""
        best_url = ""
        best_snippet = ""
        for result in results:
            verdict, confidence = self._score_result(claim, result)
            if confidence > best_confidence:
                best_verdict = verdict
                best_confidence = confidence
                best_title = result.title or ""
                best_url = result.url or ""
                best_snippet = self._result_snippet(result)
        return ClaimVerdict(
            claim=claim,
            verdict=best_verdict,
            confidence=best_confidence,
            evidence_title=best_title,
            evidence_url=best_url,
            evidence_snippet=best_snippet,
            evidence_count=len(results),
        )

    def _score_result(self, claim: str, result: Any) -> tuple[Verdict, float]:
        text = " ".join(
            part
            for part in (
                getattr(result, "title", "") or "",
                " ".join(getattr(result, "highlights", []) or []),
                getattr(result, "summary", "") or "",
                getattr(result, "text", "") or "",
            )
            if part
        ).lower()
        claim_text = claim.lower()
        claim_numbers = set(_NUMBER_RE.findall(claim_text))
        text_numbers = set(_NUMBER_RE.findall(text))
        significant_tokens = [
            token
            for token in _TOKEN_RE.findall(claim_text)
            if len(token) >= 5 and token not in _PREPOSITIONAL_STOPWORDS
        ]
        matched_tokens = sum(1 for token in significant_tokens if token in text)
        exact_match = claim_text in text
        number_match = bool(claim_numbers & text_numbers)
        if exact_match or (matched_tokens >= max(2, len(significant_tokens) // 2) and number_match):
            return "supported", min(0.99, 0.65 + 0.10 * matched_tokens + (0.10 if number_match else 0.0))
        if (
            claim_numbers
            and matched_tokens >= max(2, len(significant_tokens) // 2)
            and text_numbers
            and not number_match
        ):
            return "contradicted", min(0.90, 0.55 + 0.05 * matched_tokens)
        if matched_tokens >= 3:
            return "supported", min(0.85, 0.45 + 0.10 * matched_tokens)
        return "insufficient", min(0.60, 0.20 + 0.05 * matched_tokens)

    def _result_snippet(self, result: Any) -> str:
        for part in (
            getattr(result, "summary", "") or "",
            getattr(result, "highlights", []) or [],
            getattr(result, "text", "") or "",
        ):
            if isinstance(part, list) and part:
                candidate = " ".join(str(item) for item in part if item)
                if candidate:
                    return candidate[:500]
            if isinstance(part, str) and part:
                return part[:500]
        return ""


def _collect_claim_candidates(text: str) -> list[str]:
    claims: list[str] = []
    for bullet in _BULLET_RE.findall(text):
        bullet = " ".join(bullet.split())
        if bullet and _CLAIM_HINT_RE.search(bullet):
            claims.append(_normalize_claim_candidate(bullet))
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        sentence = " ".join(sentence.split())
        if len(sentence) < 25:
            continue
        if _CLAIM_HINT_RE.search(sentence):
            claims.append(_normalize_claim_candidate(sentence))
    unique: list[str] = []
    seen: set[str] = set()
    for claim in claims:
        key = claim.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(claim)
    return unique


def _normalize_claim_candidate(text: str) -> str:
    text = re.sub(r"^\s*[-*+]\s+", "", text)
    text = " ".join(text.split())
    return text.strip(" \t\r\n-:;")


def claim_verification_enabled(project_root: Path | str) -> bool:
    """Process claim verification enabled."""
    project_root = Path(project_root)
    config = load_project_config_yaml(project_root / "manuscript")
    if not config:
        return False
    validation = config.get("validation") or {}
    claim_verification = validation.get("claim_verification") or {}
    return bool(claim_verification.get("enabled"))


def verify_project_claims(project_root: Path | str) -> ClaimVerificationReport:
    """Verify project claims."""
    project_root = Path(project_root)
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        return ClaimVerificationReport(skipped=True, reason="manuscript directory missing")
    config = load_project_config_yaml(manuscript_dir) or {}
    validation = config.get("validation") or {}
    claim_cfg = validation.get("claim_verification") or {}
    max_workers = int(claim_cfg.get("max_workers") or 4)
    max_results = int(claim_cfg.get("max_results") or 5)
    verifier = FactCheckVerifier.from_env(
        max_workers=max_workers,
        max_results=max_results,
    )
    if verifier is None:
        return ClaimVerificationReport(skipped=True, reason="exa api key missing")
    claims: list[str] = []
    for md_file in sorted(manuscript_dir.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        claims.extend(_collect_claim_candidates(text))
    unique_claims: list[str] = []
    seen: set[str] = set()
    for claim in claims:
        key = claim.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_claims.append(claim)
    if not unique_claims:
        return ClaimVerificationReport(claims=[], verdicts=[], skipped=False, reason="no claims found")
    verdicts = verifier.verify_claims(unique_claims)
    return ClaimVerificationReport(claims=unique_claims, verdicts=verdicts)


def validate_claim_verification(project_root: Path | str) -> bool:
    """Validate claim verification."""
    project_root = Path(project_root)
    log_substep("Verifying manuscript claims against web evidence...", logger)
    report = verify_project_claims(project_root)
    if report.skipped:
        logger.warning("Claim verification skipped: %s", report.reason)
        return True
    summary = report.summary()
    logger.info(
        "Claim verification summary: %d claims, %d supported, %d contradicted, %d insufficient",
        summary["claim_count"],
        summary["supported"],
        summary["contradicted"],
        summary["insufficient"],
    )
    for verdict in report.verdicts:
        if verdict.verdict != "supported":
            logger.warning(
                "Claim flag: %s -> %s (confidence %.2f)",
                verdict.claim,
                verdict.verdict,
                verdict.confidence,
            )
    if summary["supported"] == 0 and summary["insufficient"] == 0 and summary["contradicted"] == 0:
        log_success("Claim verification: no claims were extracted", logger)
    return True
