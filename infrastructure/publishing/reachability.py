"""Opt-in live reachability verification for publishing status reports.

The publishing status block (:mod:`infrastructure.publishing.status_report`)
is compiled **offline** from ``manuscript/config.yaml`` — a non-empty
``publication.github_repository`` or DOI is trusted as published. That trust
is blind: a private or deleted repository, or an unregistered DOI, still
renders as "✅ published" (observed 2026-07-10 when a private repo was
claimed as published).

This module is the opt-in antidote, mirroring the ``--refresh-external``
precedent in ``scripts/docgen/publication_records.py``: the
``--verify-reachability`` CLI flag on
``python -m infrastructure.publishing.status_report`` probes each referenced
identifier over the network and downgrades rows whose identifier is
**definitively** gone. It is never part of the default pipeline or CI — the
default status report stays fully offline and deterministic.

Verification semantics
----------------------
* GitHub repository — unauthenticated no-redirect
  ``HEAD {github}/{owner}/{repo}`` against the public HTML URL (the URL a
  reader actually clicks). Verified live 2026-07-10: public → 200,
  private/missing → 404. The REST API was deliberately rejected — anonymous
  ``api.github.com`` calls are rate-limited (observed HTTP 403) and would
  make the check chronically inconclusive. Deliberately **no**
  ``Authorization`` header even when ``GITHUB_TOKEN`` is set: the question
  is *public* reachability, and credentials that can see a private repo
  would launder exactly the failure this check exists to catch.
* Concept DOI — no-redirect ``HEAD {resolver}/{doi}``. A 3xx from the
  resolver itself proves the DOI is registered without following through to
  the publisher (which may bot-block and produce false errors).
* Only HTTP 404/410 count as ``unreachable`` (downgrade). Rate limits,
  auth walls, server errors, and network failures are ``error``
  (annotate-only): a transient outage must not demote a genuinely published
  artifact.

Public API
----------
* :class:`ReachabilityCheck` — one probe result.
* :func:`probe_url` — classify a single URL as ok / unreachable / error.
* :func:`verify_reachability` — probe a compiled report's identifiers.
* :func:`apply_reachability` — downgrade definitively-unreachable rows.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass, replace

from infrastructure.publishing.status_report import (
    PublicationState,
    PublishingStatusReport,
)

GITHUB_BASE = "https://github.com"
DOI_BASE = "https://doi.org"

STATUS_OK = "ok"
STATUS_UNREACHABLE = "unreachable"
STATUS_ERROR = "error"

_USER_AGENT = "template-status-report-reachability/1.0"
_GONE_CODES = frozenset({404, 410})


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse to follow redirects so a 3xx surfaces as the probe result."""

    def redirect_request(self, *args: object, **kwargs: object) -> None:
        """Suppress all redirects so a 3xx surfaces as the probe result."""
        return None


# Retains urllib's default ProxyHandler (HTTP(S)_PROXY env vars are honoured);
# the opt-in probe is a best-effort public-view check, not a hermetic one.
_OPENER = urllib.request.build_opener(_NoRedirect)


@dataclass(frozen=True)
class ReachabilityCheck:
    """Result of one live reachability probe.

    Attributes:
        platform: Registry platform name the probe verifies (e.g. ``github``).
        identifier: The durable identifier from config (repo slug or DOI).
        url: The URL actually probed.
        status: One of ``ok``, ``unreachable``, ``error``.
        detail: HTTP status line or exception class name.
    """

    platform: str
    identifier: str
    url: str
    status: str
    detail: str


def probe_url(url: str, *, timeout: float = 10.0, method: str = "GET") -> tuple[str, str]:
    """Probe a URL and classify the outcome.

    Redirects are not followed: a 3xx response is classified ``ok`` (the
    identifier resolves) without contacting the redirect target.

    Args:
        url: Absolute ``http(s)`` URL to probe.
        timeout: Socket timeout in seconds.
        method: HTTP method (``GET`` or ``HEAD``).

    Returns:
        ``(status, detail)`` where status is :data:`STATUS_OK` (2xx/3xx),
        :data:`STATUS_UNREACHABLE` (404/410), or :data:`STATUS_ERROR`
        (any other HTTP code, unsupported scheme, or network failure).
    """
    if not url.startswith(("http://", "https://")):
        return STATUS_ERROR, "unsupported URL scheme"
    request = urllib.request.Request(  # noqa: S310
        url, headers={"User-Agent": _USER_AGENT}, method=method
    )
    try:
        with _OPENER.open(request, timeout=timeout) as response:  # noqa: S310  # nosec B310
            return STATUS_OK, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            return STATUS_OK, f"HTTP {exc.code}"
        if exc.code in _GONE_CODES:
            return STATUS_UNREACHABLE, f"HTTP {exc.code}"
        return STATUS_ERROR, f"HTTP {exc.code}"
    except (TimeoutError, OSError) as exc:
        return STATUS_ERROR, f"error: {exc.__class__.__name__}"


def verify_reachability(
    report: PublishingStatusReport,
    *,
    github_base: str = GITHUB_BASE,
    doi_base: str = DOI_BASE,
    timeout: float = 10.0,
) -> tuple[ReachabilityCheck, ...]:
    """Probe the durable identifiers referenced by a compiled report.

    Checks the GitHub repository (when ``report.github_repo`` is set) and the
    concept DOI (when ``report.concept_doi`` is set). Base URLs are
    parameterized for tests (``pytest-httpserver``) and enterprise mirrors.

    Args:
        report: Offline-compiled status report.
        github_base: GitHub web base URL (public HTML, not the REST API).
        doi_base: DOI resolver base URL.
        timeout: Per-probe socket timeout in seconds.

    Returns:
        One :class:`ReachabilityCheck` per identifier present, in
        (github, zenodo) order; empty when the report references nothing.
    """
    checks: list[ReachabilityCheck] = []
    if report.github_repo:
        url = f"{github_base.rstrip('/')}/{report.github_repo}"
        status, detail = probe_url(url, timeout=timeout, method="HEAD")
        checks.append(ReachabilityCheck("github", report.github_repo, url, status, detail))
    if report.concept_doi:
        url = f"{doi_base.rstrip('/')}/{report.concept_doi}"
        status, detail = probe_url(url, timeout=timeout, method="HEAD")
        checks.append(ReachabilityCheck("zenodo", report.concept_doi, url, status, detail))
    return tuple(checks)


def apply_reachability(
    report: PublishingStatusReport,
    checks: tuple[ReachabilityCheck, ...],
) -> PublishingStatusReport:
    """Downgrade definitively-unreachable PUBLISHED rows to UNREACHABLE.

    Only rows whose platform has a check with status
    :data:`STATUS_UNREACHABLE` *and* whose offline state is PUBLISHED are
    downgraded. RESERVED rows are exempt: a Zenodo-reserved DOI is minted but
    deliberately not registered with DataCite until the record is published,
    so a 404 from the resolver is its normal, expected state — not an alarm.
    ``ok`` and ``error`` checks never change a row — a transient failure is
    reported by the caller, not encoded in the block.

    Args:
        report: Offline-compiled status report.
        checks: Probe results from :func:`verify_reachability`.

    Returns:
        A new report with downgraded platform rows (input is not mutated).
    """
    unreachable = {c.platform for c in checks if c.status == STATUS_UNREACHABLE}
    rows = tuple(
        replace(row, state=PublicationState.UNREACHABLE)
        if row.name in unreachable and row.state is PublicationState.PUBLISHED
        else row
        for row in report.platforms
    )
    return replace(report, platforms=rows)
