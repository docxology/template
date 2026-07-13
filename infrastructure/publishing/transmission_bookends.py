"""Generated transmission bookend pages for publication pairing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from infrastructure.core.config.loader import load_config
from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.zenodo_urls import zenodo_record_url_from_doi
from infrastructure.publishing.metadata_from_config import publication_metadata_from_config
from infrastructure.publishing.publication_ledger import load_publication_ledger
from infrastructure.publishing.release_pairing import (
    format_pairing_checklist,
    format_pairing_checklist_compact,
    validate_release_pairing,
)
from infrastructure.publishing.transmission_barcode_strip import (
    MANIFEST_FILENAME,
    STRIP_FILENAME,
    compact_manifest_json,
    write_transmission_barcode_strip,
    write_transmission_manifest,
)
from infrastructure.publishing.transmission_figure import write_transmission_diagram
from infrastructure.publishing.transmission_models import TransmissionContext
from infrastructure.steganography.config import SteganographyConfig

logger = get_logger(__name__)

BEGIN_FILENAME = "00_00_transmission_begin.md"
END_FILENAME = "99_zz_transmission_end.md"
FIGURE_NAME = "transmission_pairing.png"
TRANSMISSION_BOOKEND_FILENAMES = frozenset({BEGIN_FILENAME, END_FILENAME})
END_PAGE_MAX_PRIOR_ROWS = 3
# Pandoc image-width attributes MUST carry a unit. Bare decimals (e.g. ``0.35``)
# are parsed by pandoc as ~0.35px ≈ 0in → the bookend images render at zero width
# (invisible). Percentages map to a fraction of \textwidth and render correctly.
FIGURE_WIDTH = "35%"
STRIP_WIDTH = "98%"


def is_transmission_bookend(path: Path) -> bool:
    """Return True for generated transmission boundary sections."""
    return path.name in TRANSMISSION_BOOKEND_FILENAMES


@dataclass(frozen=True)
class TransmissionBookendSettings:
    """Bookend feature flags from config."""

    enabled: bool
    max_prior_releases: int
    show_steganography: bool
    github_repository: str | None


def _bookend_settings(config: dict[str, Any]) -> TransmissionBookendSettings:
    publication = config.get("publication") or {}
    if not isinstance(publication, dict):
        publication = {}
    transmission = publication.get("transmission_bookends") or {}
    if not isinstance(transmission, dict):
        transmission = {}
    github_repository = publication.get("github_repository")
    return TransmissionBookendSettings(
        enabled=bool(transmission.get("enabled")),
        max_prior_releases=int(transmission.get("max_prior_releases") or 5),
        show_steganography=transmission.get("show_steganography", True) is not False,
        github_repository=str(github_repository).strip() if github_repository else None,
    )


def transmission_bookends_enabled(config_path: Path) -> bool:
    """Return True when transmission bookends are enabled in config."""
    config = load_config(config_path)
    if not config:
        return False
    return _bookend_settings(config).enabled


def _load_raw_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    return config if isinstance(config, dict) else {}


def _latest_release(ledger: dict[str, Any]) -> dict[str, Any] | None:
    releases = ledger.get("releases") or []
    if not isinstance(releases, list) or not releases:
        return None
    last = releases[-1]
    return last if isinstance(last, dict) else None


def _format_steganography_one_liner(config: dict[str, Any]) -> str:
    stego_raw = config.get("steganography") or {}
    if not isinstance(stego_raw, dict):
        stego_raw = {}
    stego = SteganographyConfig.from_dict(stego_raw)
    return (
        f"**Stego:** {'on' if stego.enabled else 'off'} | overlays {stego.overlay_mode} | "
        f"barcodes {'on' if stego.barcodes_enabled else 'off'} | XMP {'on' if stego.metadata_enabled else 'off'} | "
        f"manifest {'on' if stego.hashing_enabled and stego.manifest_enabled else 'off'} → `./secure_run.sh`"
    )


def _format_steganography_summary(config: dict[str, Any]) -> str:
    return _format_steganography_one_liner(config)


def _format_prior_releases_compact(releases: list[dict[str, Any]], *, max_rows: int) -> str:
    """Compact prior-release lines for single-page end bookend."""
    if not releases:
        return "_No prior releases._"
    page_cap = min(max_rows, END_PAGE_MAX_PRIOR_ROWS)
    visible = releases[-page_cap:]
    hidden = max(0, len(releases) - len(visible))
    lines = []
    for entry in visible:
        tag = str(entry.get("tag") or "—")
        doi = str(entry.get("doi") or "pending")
        prefix = str(entry.get("pdf_sha256") or "")[:8]
        lines.append(f"`{tag}` · `{doi}` · `{prefix}…`")
    if hidden:
        lines.append(f"_{hidden} earlier in `publication_ledger.json`._")
    return " · ".join(lines)


def _format_prior_releases_table(
    releases: list[dict[str, Any]],
    *,
    max_rows: int,
    end_page: bool = False,
) -> str:
    if not releases:
        return "_No prior releases recorded._"

    page_cap = min(max_rows, END_PAGE_MAX_PRIOR_ROWS) if end_page else max_rows
    visible = releases[-page_cap:]
    hidden = max(0, len(releases) - len(visible))
    lines = [
        "| Tag | DOI | GitHub | SHA-256 (prefix) |",
        "| --- | --- | --- | --- |",
    ]
    for entry in visible:
        tag = str(entry.get("tag") or "—")
        doi = str(entry.get("doi") or "pending")
        gh = str(entry.get("github_release_url") or "pending")
        digest = str(entry.get("pdf_sha256") or "")
        prefix = digest[:12] + "…" if len(digest) > 12 else (digest or "pending")
        lines.append(f"| `{tag}` | `{doi}` | [release]({gh}) | `{prefix}` |")
    if hidden:
        lines.append("")
        lines.append(f"_{hidden} earlier release(s) in `output/data/publication_ledger.json`._")
    return "\n".join(lines)


def _publication_version_fields(raw_config: dict[str, Any]) -> tuple[str | None, str | None]:
    publication = raw_config.get("publication") or {}
    if not isinstance(publication, dict):
        return None, None
    version_doi = publication.get("version_doi")
    version_record = publication.get("version_record")
    v_doi = str(version_doi).strip() if version_doi else None
    v_rec = str(version_record).strip() if version_record else None
    return v_doi or None, v_rec or None


def _hash_prefix(digest: str | None, length: int = 16) -> str:
    if not digest:
        return "pending"
    if len(digest) <= length:
        return digest
    return f"{digest[:length]}…"


def _format_metadata_table(context: TransmissionContext) -> str:
    rows = [
        ("Title", context.title),
        ("Version", context.version or "—"),
        ("Concept DOI", context.doi or "pending"),
    ]
    if context.version_doi:
        rows.append(("Version DOI", context.version_doi))
    rows.extend(
        [
            ("GitHub", context.github_release_url or context.github_repository or "pending"),
            ("Zenodo", context.zenodo_record_url or "pending"),
            ("SHA-256", _hash_prefix(context.pdf_sha256, 16)),
            ("SHA-512", _hash_prefix(context.pdf_sha512, 16)),
        ]
    )
    lines = [
        "| Field | Value |",
        "| --- | --- |",
    ]
    for label, value in rows:
        if label.startswith("SHA") and value != "pending":
            lines.append(f"| {label} | `{value}` |")
        elif label in {"GitHub", "Zenodo"} and value.startswith("http"):
            lines.append(f"| {label} | [{value}]({value}) |")
        else:
            lines.append(f"| {label} | {value} |")
    return "\n".join(lines)


def _verification_steps() -> str:
    return "\n".join(
        [
            "- Scan **Integrity** QR and compare the embedded SHA-256 prefix to the table above.",
            "- Scan **Zenodo** / **GitHub** QR codes and confirm they resolve to this release pairing.",
            "- Full hashes and structured fields: `../data/transmission_manifest.json`.",
        ]
    )


def _format_metadata_lines(context: TransmissionContext) -> list[str]:
    lines = [
        f"- **Title:** {context.title}",
        f"- **Version:** {context.version or '—'}",
        f"- **DOI:** {context.doi or 'pending'}",
        f"- **GitHub:** {context.github_release_url or context.github_repository or 'pending'}",
    ]
    if context.zenodo_record_url:
        lines.append(f"- **Zenodo:** {context.zenodo_record_url}")
    if context.pdf_sha256:
        lines.append(f"- **SHA-256:** `{context.pdf_sha256}`")
    if context.pdf_sha512:
        lines.append(f"- **SHA-512:** `{context.pdf_sha512}`")
    return lines


def _manifest_snippet(context: TransmissionContext) -> str:
    hash_prefix = (context.pdf_sha256 or "pending")[:16]
    doi = context.doi or "pending"
    version = context.version or "—"
    return "\n".join(
        [
            "```",
            f"title={context.title[:48]}",
            f"version={version} doi={doi}",
            f"sha256={hash_prefix}… manifest={compact_manifest_json(context)}",
            "```",
        ]
    )


def _latex_envelope_open(*, end_bookend: bool = False) -> str:
    lines = [
        "```{=latex}",
    ]
    if end_bookend:
        lines.append("% transmission-end-bookend")
        lines.append("\\clearpage")
    lines.extend(
        [
            "\\thispagestyle{empty}",
            "\\setlength{\\parskip}{0pt}",
            "\\setlength{\\itemsep}{0pt}",
            "\\begin{samepage}",
            "\\scriptsize",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _latex_envelope_close(*, newpage: bool = True) -> str:
    close = "```{=latex}\n\\end{samepage}\n"
    if newpage:
        close += "\\newpage\n"
    close += "```\n"
    return close


def build_transmission_context(
    project_root: Path,
    project_name: str,
    *,
    repo_root: Path | None = None,
) -> TransmissionContext | None:
    """Build bookend context when the feature is enabled."""
    _config_candidates = [
        project_root / "manuscript" / "config.yaml",
        project_root / "output" / "manuscript" / "config.yaml",
        project_root / "docs" / "manuscript" / "config.yaml",
    ]
    config_path = next((p for p in _config_candidates if p.is_file()), None)
    if config_path is None:
        return None

    raw_config = _load_raw_config(config_path)
    settings = _bookend_settings(raw_config)
    if not settings.enabled:
        return None

    metadata = publication_metadata_from_config(config_path, allow_draft_abstract=True)
    resolved_repo = repo_root or project_root.parent.parent
    version_doi, version_record = _publication_version_fields(raw_config)
    if version_doi and not version_record:
        version_record = zenodo_record_url_from_doi(version_doi)
    ledger = load_publication_ledger(project_root, repo_root=resolved_repo, project_name=project_name)
    latest = _latest_release(ledger)

    doi = metadata.doi or (str(latest.get("doi")) if latest else None)
    github_release_url_value = (
        str(latest.get("github_release_url")) if latest and latest.get("github_release_url") else None
    )
    # Do not hash the current combined PDF here. During render, that file is
    # either absent or from a previous run, so embedding its digest in draft
    # bookends creates stale release metadata by construction. Published hashes
    # must come from the explicit publication ledger.
    pdf_sha256 = str(latest.get("pdf_sha256")) if latest and latest.get("pdf_sha256") else None
    pdf_sha512 = str(latest.get("pdf_sha512")) if latest and latest.get("pdf_sha512") else None

    zenodo_record_url = zenodo_record_url_from_doi(doi) if doi else None
    pairing = validate_release_pairing(
        {
            "doi": doi,
            "github_release_url": github_release_url_value,
            "pdf_sha256": pdf_sha256,
            "zenodo_record_url": zenodo_record_url,
        },
        require_doi=bool(doi),
    )

    figure_path = project_root / "output" / "figures" / FIGURE_NAME
    write_transmission_diagram(
        figure_path,
        current={"doi": doi, "pdf_sha256": pdf_sha256},
    )
    figure_markdown = f"![Publication pairing flow](../figures/{FIGURE_NAME}){{width={FIGURE_WIDTH}}}"

    authors = raw_config.get("authors") or []
    if not isinstance(authors, list):
        authors = []

    stego_one_liner = _format_steganography_one_liner(raw_config) if settings.show_steganography else ""
    releases = [item for item in (ledger.get("releases") or []) if isinstance(item, dict)]
    prior_table = _format_prior_releases_table(
        releases[:-1],
        max_rows=settings.max_prior_releases,
        end_page=True,
    )
    prior_compact = _format_prior_releases_compact(
        releases[:-1],
        max_rows=settings.max_prior_releases,
    )

    draft_context = TransmissionContext(
        title=metadata.title,
        version=metadata.paper_version,
        doi=doi,
        version_doi=version_doi,
        version_record=version_record,
        github_release_url=github_release_url_value,
        github_repository=settings.github_repository,
        pdf_sha256=pdf_sha256,
        pdf_sha512=pdf_sha512,
        zenodo_record_url=zenodo_record_url,
        pairing_valid=pairing.valid,
        pairing_checklist=format_pairing_checklist(pairing),
        pairing_compact=format_pairing_checklist_compact(pairing),
        steganography_summary=stego_one_liner,
        steganography_one_liner=stego_one_liner,
        figure_markdown=figure_markdown,
        integrity_strip_markdown=f"![Integrity QR strip](../figures/{STRIP_FILENAME}){{width={STRIP_WIDTH}}}",
        manifest_snippet="",
        manifest_path=f"../data/{MANIFEST_FILENAME}",
        prior_releases_table=prior_table,
        prior_compact=prior_compact,
        published=bool(latest and doi and github_release_url_value and pdf_sha256 and pairing.valid),
    )

    manifest_path = project_root / "output" / "data" / MANIFEST_FILENAME
    write_transmission_manifest(manifest_path, draft_context)
    strip_path = project_root / "output" / "figures" / STRIP_FILENAME
    write_transmission_barcode_strip(strip_path, context=draft_context, authors=authors)

    return TransmissionContext(
        title=draft_context.title,
        version=draft_context.version,
        doi=draft_context.doi,
        version_doi=draft_context.version_doi,
        version_record=draft_context.version_record,
        github_release_url=draft_context.github_release_url,
        github_repository=draft_context.github_repository,
        pdf_sha256=draft_context.pdf_sha256,
        pdf_sha512=draft_context.pdf_sha512,
        zenodo_record_url=draft_context.zenodo_record_url,
        pairing_valid=draft_context.pairing_valid,
        pairing_checklist=draft_context.pairing_checklist,
        pairing_compact=draft_context.pairing_compact,
        steganography_summary=draft_context.steganography_summary,
        steganography_one_liner=draft_context.steganography_one_liner,
        figure_markdown=draft_context.figure_markdown,
        integrity_strip_markdown=draft_context.integrity_strip_markdown,
        manifest_snippet=_manifest_snippet(draft_context),
        manifest_path=draft_context.manifest_path,
        prior_releases_table=draft_context.prior_releases_table,
        prior_compact=draft_context.prior_compact,
        published=draft_context.published,
    )


def _current_release_one_liner(context: TransmissionContext) -> str:
    hash_prefix = (context.pdf_sha256 or "pending")[:12]
    return (
        f"**Release:** v{context.version or '—'} · DOI `{context.doi or 'pending'}` · "
        f"SHA-256 `{hash_prefix}…` · pairing {'complete' if context.pairing_valid else 'pending'}"
    )


def render_transmission_markdown(context: TransmissionContext, *, boundary: Literal["begin", "end"]) -> str:
    """Render a single-page transmission bookend markdown section."""
    if boundary == "begin":
        banner_latex = r"\section*{BEGINNING OF TRANSMISSION}\label{beginning-of-transmission}"
        banner_text = "BEGINNING OF TRANSMISSION"
    else:
        banner_latex = r"\section*{END OF TRANSMISSION}\label{end-of-transmission}"
        banner_text = "END OF TRANSMISSION"

    status = "published" if context.published else "unpublished / pending pairing"

    body_parts = [
        _latex_envelope_open(end_bookend=(boundary == "end")),
        "```{=latex}",
        banner_latex,
        "```",
        "",
    ]

    if boundary == "begin":
        body_parts.extend(
            [
                f"**State:** {status}",
                "",
                context.pairing_compact,
                "",
                "```{=latex}",
                r"\subsubsection*{Release metadata}",
                "```",
                "",
                _format_metadata_table(context),
                "",
                "```{=latex}",
                r"\subsubsection*{How to verify}",
                "```",
                "",
                _verification_steps(),
                "",
                context.integrity_strip_markdown,
                "",
                f"Structured manifest: `{context.manifest_path}`",
                "",
                context.figure_markdown,
            ]
        )
        if context.steganography_one_liner:
            body_parts.extend(["", context.steganography_one_liner])
    else:
        body_parts.extend(
            [
                _current_release_one_liner(context),
                "",
                context.integrity_strip_markdown.replace(f"width={STRIP_WIDTH}", "width=88%"),
                "",
                f"**Prior:** {context.prior_compact}",
            ]
        )

    body_parts.extend(["", _latex_envelope_close(newpage=(boundary == "begin"))])
    # Keep plain-text marker for PDF page-span checks (LaTeX section title may not extract cleanly).
    body_parts.append(f"\n<!-- {banner_text} -->")
    return "\n".join(body_parts)


def write_transmission_bookends(
    project_root: Path,
    project_name: str,
    *,
    repo_root: Path | None = None,
) -> tuple[Path, Path] | None:
    """Write begin/end transmission bookends into ``output/manuscript/``."""
    context = build_transmission_context(project_root, project_name, repo_root=repo_root)
    if context is None:
        return None

    out_dir = project_root / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)

    begin_path = out_dir / BEGIN_FILENAME
    end_path = out_dir / END_FILENAME
    begin_path.write_text(render_transmission_markdown(context, boundary="begin"), encoding="utf-8")
    end_path.write_text(render_transmission_markdown(context, boundary="end"), encoding="utf-8")
    logger.info("Wrote transmission bookends: %s, %s", begin_path, end_path)
    return begin_path, end_path
