"""SDK-owned Pitch compiler consuming admitted source DATA without executing it."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES, public_project_names
from infrastructure.rendering.slide_deck import DeckContent, Slide, SlideBudget
from infrastructure.reporting.native_projection_contracts import compile_projection_contract, ProjectionPage
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

COUNTS_ROW = re.compile(
    r"^\|\s*`(?P<name>[\w.]+)`\s*\|\s*(?P<tests>\d+)\s*\|\s*(?P<coverage>[\d.]+)\s*%\s*\|", re.MULTILINE
)
TOKEN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
DISPLAY_PLATFORMS = {
    "zenodo": "Zenodo",
    "github": "GitHub",
    "github_pages": "GitHub Pages",
    "pypi": "PyPI",
    "osf": "OSF",
    "software_heritage": "Software Heritage",
    "huggingface_hub": "Hugging Face",
    "ipfs_pinata": "IPFS",
    "ipfs_web3storage": "IPFS",
    "netlify": "Netlify",
    "cloudflare_pages": "Cloudflare Pages",
    "arxiv": "arXiv",
}


def pitch_source_tokens(
    root: Path, subject: str, reader: SnapshotReader, *, tracked_paths: tuple[str, ...], deadline: float
) -> dict[str, str]:
    """Rebuild exact source facts using loaded SDK consumers and original Root index.

    `tracked_paths` must be supplied by the enclosing admitted Git/DATA scope.
    This function neither computes nor self-authenticates its own membership.
    It does not import any project/provider modules or add source DATA to sys.path.
    """
    import yaml
    from infrastructure.documentation.counts_doc import infrastructure_packages, tracked_infra_python_count
    from infrastructure.publishing.status_report import PublicationState, compile_publishing_status

    if time.monotonic() >= deadline or f"templates/{subject}" not in PUBLIC_PROJECT_NAMES:
        raise ValueError("Pitch facts need an original live deadline and exact public subject")
    if (
        not tracked_paths
        or len(set(tracked_paths)) != len(tracked_paths)
        or any(Path(p).is_absolute() or ".." in Path(p).parts for p in tracked_paths)
    ):
        raise ValueError("Pitch facts need exact admitted original Root tracked membership")
    own = yaml.safe_load(reader.read("projects/templates/template_pitch_deck/manuscript/config.yaml").content)
    subject_snapshot = reader.read(f"projects/templates/{subject}/manuscript/config.yaml")
    config = yaml.safe_load(subject_snapshot.content)
    if not isinstance(config, dict) or not isinstance(own, dict):
        raise ValueError("Pitch facts require exact source configuration mappings")
    rows = [
        m
        for m in COUNTS_ROW.finditer(reader.read("docs/_generated/COUNTS.md").content.decode())
        if m["name"] == subject
    ]
    if len(rows) != 1:
        raise ValueError("Pitch facts require one exact generated source count row")
    roster = public_project_names(root)
    if set(roster) != set(PUBLIC_PROJECT_NAMES):
        raise ValueError("Pitch source roster differs from complete canonical public scope")
    report = compile_publishing_status(root / "projects/templates" / subject)

    def platform_summary(state: PublicationState) -> tuple[str, str]:
        selected = [item for item in report.platforms if item.state is state]

        def name(item: Any) -> str:
            label = DISPLAY_PLATFORMS.get(item.name, item.name.replace("_", " ").title())
            return (
                f"{label} (sandbox)"
                if item.name == "pypi" and item.reference and "test.pypi.org" in item.reference
                else label
            )

        return ", ".join(name(item) for item in selected), str(len(selected))

    published_names, published_count = platform_summary(PublicationState.PUBLISHED)
    historical_names, historical_count = platform_summary(PublicationState.HISTORICAL)
    paper, publication, metadata = (config.get(k) or {} for k in ("paper", "publication", "metadata"))
    alternatives = sorted(name.rsplit("/", 1)[-1] for name in roster if name != f"templates/{subject}")
    packages = infrastructure_packages(root)
    for package in packages:
        reader.read(f"infrastructure/{package}/__init__.py")
    counts = sorted(
        (
            (package, sum(p.startswith(f"infrastructure/{package}/") and p.endswith(".py") for p in tracked_paths))
            for package in packages
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    counts = [item for item in counts if item[1] > 0]
    total = tracked_infra_python_count(root, tracked_paths=tracked_paths)
    tokens = {
        "PITCH_SUBJECT_NAME": subject,
        "PITCH_SUBJECT_TITLE": str(paper.get("title", subject)),
        "PITCH_SUBJECT_VERSION": str(paper.get("version", "")),
        "PITCH_SUBJECT_RELEASE_STATUS": str(publication.get("release_status", "unknown")),
        "PITCH_SUBJECT_LAST_PUBLISHED_VERSION": str(publication.get("last_published_version", "")),
        "PITCH_SUBJECT_LICENSE": str(metadata.get("license", "")),
        "PITCH_SUBJECT_DOI": str(publication.get("doi", "")),
        "PITCH_SUBJECT_GITHUB": str(publication.get("github_repository", "")),
        "PITCH_SUBJECT_TEST_COUNT": rows[0]["tests"],
        "PITCH_SUBJECT_COVERAGE_PCT": rows[0]["coverage"],
        "PITCH_SUBJECT_PUBLISHED_PLATFORM_COUNT": published_count,
        "PITCH_SUBJECT_PUBLISHED_PLATFORM_NAMES": published_names,
        "PITCH_SUBJECT_LAST_PUBLISHED_PLATFORM_COUNT": historical_count,
        "PITCH_SUBJECT_LAST_PUBLISHED_PLATFORM_NAMES": historical_names,
        "EXEMPLAR_COUNT": str(len(roster)),
        "EXEMPLAR_COUNT_PLUS_ONE": str(len(roster) + 1),
        "SECOND_EXEMPLAR_NAME": alternatives[0],
        "EXEMPLAR_ROSTER": ", ".join(sorted(n.rsplit("/", 1)[-1] for n in roster)),
        "PITCH_DECK_DOI_STATUS": str(
            (own.get("publication") or {}).get("doi") or "not yet reserved — no Zenodo deposit on file for this deck"
        ),
        "INFRA_SUBPACKAGE_COUNT": str(len(packages)),
        "INFRA_PYTHON_FILE_COUNT": str(total),
        "INFRA_LARGEST_SUBPACKAGE": counts[0][0] if counts else "",
        "INFRA_LARGEST_SUBPACKAGE_COUNT": str(counts[0][1]) if counts else "0",
        "INFRA_UNATTRIBUTED_FILE_COUNT": str(total - sum(count for _, count in counts)),
    }
    if time.monotonic() >= deadline or not reader.unchanged():
        raise ValueError("Pitch exact admitted source DATA changed during SDK fact compilation")
    return tokens


def compile_pitch_source_model(
    root: Path, scope: str, artifact: Any, reader: SnapshotReader, *, tracked_paths: tuple[str, ...], deadline: float
) -> tuple[DeckContent, str]:
    """Complete exact current variant model built entirely by SDK-owned code."""
    import yaml

    if scope != "templates/template_pitch_deck":
        raise ValueError("Pitch source compiler requires its exact canonical public scope")
    parts = artifact.id.split(":")
    if (
        len(parts) != 3
        or parts[0] != "pitch"
        or parts[1] not in {"short", "medium", "long"}
        or parts[2] not in {"pdf", "pptx"}
    ):
        raise ValueError("Pitch artifact differs from its exact source-owned variant identity")
    config = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    deck_config = config.get("project_config", {}).get("deck")
    if not isinstance(deck_config, dict) or deck_config.get("lengths") != ["short", "medium", "long"]:
        raise ValueError("Pitch source requires all three configured deck lengths in order")
    if deck_config.get("formats") != ["pdf", "pptx"]:
        raise ValueError("Pitch source requires the complete configured PDF/PPTX pair")
    subject = str(deck_config.get("pitch_subject", "template_template"))
    if re.fullmatch(r"[\w-]+", subject) is None or f"templates/{subject}" not in PUBLIC_PROJECT_NAMES:
        raise ValueError("Pitch subject is outside its exact public source scope")
    declaration = deck_config.get("subjects", {}).get(subject, {})
    prefix = declaration.get("content_prefix", "deck_content")
    if not isinstance(prefix, str) or re.fullmatch(r"[A-Za-z0-9_-]+", prefix) is None:
        raise ValueError("Pitch source prefix is not one exact lexical source segment")
    raw_snapshot = reader.read(f"projects/{scope}/manuscript/{prefix}_{parts[1]}.yaml")
    raw = yaml.safe_load(raw_snapshot.content)
    if (
        not isinstance(raw, dict)
        or set(raw) - {"title", "subtitle", "slides", "metadata"}
        or not isinstance(raw.get("slides"), list)
    ):
        raise ValueError("Pitch source content schema has unobserved top-level data")
    tokens = pitch_source_tokens(root, subject, reader, tracked_paths=tracked_paths, deadline=deadline)

    def resolve(value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("Pitch source text is not an original literal string")
        missing = set(TOKEN.findall(value)) - tokens.keys()
        if missing:
            raise ValueError(f"Pitch source has unresolved original token identities: {sorted(missing)}")
        result = TOKEN.sub(lambda m: tokens[m[1]], value)
        if "{{" in result:
            raise ValueError("Pitch source contains an unresolved token value")
        return result

    rows = []
    source_base = str(deck_config.get("source_base_url", ""))
    allowed = {
        "title",
        "kind",
        "bullets",
        "notes",
        "figure",
        "stat_value",
        "stat_label",
        "quote_text",
        "quote_attribution",
        "source",
    }
    for ordinal, value in enumerate(raw["slides"], 1):
        if not isinstance(value, dict) or set(value) - allowed:
            raise ValueError("Pitch source slide schema has unobserved data")
        kind = value.get("kind", "content")
        if kind not in {"title", "section", "content", "stat", "quote", "diagram"}:
            raise ValueError("Pitch source has an unsupported original slide kind")
        bullets = value.get("bullets", [])
        if not isinstance(bullets, list):
            raise ValueError("Pitch source bullets differ from their original ordered list")
        figure = value.get("figure")
        if figure is not None and (not isinstance(figure, str) or Path(figure).name != figure or figure in {".", ".."}):
            raise ValueError("Pitch source figure escapes its exact declared resource directory")
        source = value.get("source", "")
        if not isinstance(source, str):
            raise ValueError("Pitch citation target is not one original literal path")
        qr = (
            source_base.rstrip("/")
            + f"/projects/{scope}/output/slides_standalone/{subject}_{parts[1]}/slide_{ordinal:02d}.md"
            if source_base
            else ""
        )
        rows.append(
            Slide(
                title=resolve(value.get("title", "")),
                kind=kind,
                bullets=tuple(resolve(text) for text in bullets),
                notes=resolve(value.get("notes", "")),
                figure_path=root / f"projects/{scope}/output/figures/{figure}" if figure else None,
                stat_value=resolve(value.get("stat_value", "")),
                stat_label=resolve(value.get("stat_label", "")),
                quote_text=resolve(value.get("quote_text", "")),
                quote_attribution=resolve(value.get("quote_attribution", "")),
                source=source,
                qr_url=qr,
            )
        )
    max_count = {"short": SlideBudget.SHORT.value, "medium": SlideBudget.MEDIUM.value, "long": SlideBudget.LONG.value}[
        parts[1]
    ]
    if not rows or len(rows) > max_count:
        raise ValueError("complete source-owned Pitch contract cannot silently discard original tail slides")
    deck = DeckContent(
        resolve(raw.get("title", "")), resolve(raw.get("subtitle", "")), tuple(rows), raw.get("metadata", {})
    )
    expected = f"projects/{scope}/output/{parts[2]}/{subject}_pitch_{parts[1]}.{parts[2]}"
    if artifact.path != expected or artifact.format != parts[2]:
        raise ValueError("Pitch path/format differs from exact current source declarations")
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("Pitch source DATA changed or original deadline expired during independent SDK compilation")
    return deck, source_base


def compile_pitch_source_contract(
    root: Path, scope: str, artifact: Any, reader: SnapshotReader, *, tracked_paths: tuple[str, ...], deadline: float
) -> tuple[ProjectionPage, ...]:
    """Complete projection from the independently held exact source model."""
    deck, source_base = compile_pitch_source_model(
        root,
        scope,
        artifact,
        reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
    pages = compile_projection_contract(deck, source_base_url=source_base, reader=reader)
    if not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("Pitch source figures changed or original deadline expired during projection compilation")
    return pages
