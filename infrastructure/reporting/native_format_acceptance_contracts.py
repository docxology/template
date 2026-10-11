"""Source-owned native artifact obligations, separate from existing-file discovery."""

from __future__ import annotations

import re
import math
import os
import stat
import signal
import threading
import time
from contextlib import contextmanager
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import public_source_paths
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.project.public_acceptance_evidence import evidence_directory
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.transmission.transmission_bookends import is_transmission_bookend
from infrastructure.validation.output.render_formats import render_config_manuscript_dir

NATIVE_SCHEMA = "template-native-format-execution-v13"
CONTROL_SCHEMA = "template-native-format-control-v1"
TOOL_SCHEMA = "template-native-tool-execution-v3"
TOOL_FIELDS = frozenset(
    (
        "caller_deadline_monotonic",
        "command",
        "custody_refused",
        "diagnostic",
        "environment_digest",
        "executable",
        "executable_identity_after",
        "executable_identity_before",
        "executable_observation_after",
        "executable_observation_before",
        "executable_sha256",
        "exit_code",
        "native_process_artifact",
        "original_deadline_monotonic",
        "original_exit_code",
        "owner_pid",
        "pid",
        "purpose",
        "raw_stderr",
        "raw_stdout",
        "run_id",
        "schema_version",
        "stderr",
        "stdout",
        "timed_out",
        "tool",
    )
)
CITATION_TOOL_FIELDS = TOOL_FIELDS | frozenset(
    {
        "cwd",
        "input_observations_before",
        "input_observations_after",
        "consumed_input_artifacts",
        "started_at_monotonic",
        "duration_seconds",
    }
)
HTML_TOOL_FIELDS = TOOL_FIELDS | frozenset({"html_python_source_closure", "html_python_source_closure_error"})
WORKER_MODULE = "infrastructure.reporting.native_format_acceptance_worker"
PROCESS_SCHEMA = "template-native-format-process-v3"


class NativeDeadlineUnavailable(RuntimeError):
    """This caller cannot safely establish the native whole-operation deadline."""


class NativeDeadlineExpired(BaseException):
    """A deadline cannot be swallowed as an ordinary observer parse/IO error."""


@contextmanager
def native_deadline_guard(deadline: float) -> Iterator[None]:
    """Interrupt supported POSIX admission/finalization on its original clock."""
    if os.name != "posix" or threading.current_thread() is not threading.main_thread():
        raise NativeDeadlineUnavailable("native admission/finalization requires a POSIX main-thread deadline")
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    if any(previous_timer):
        raise NativeDeadlineUnavailable("an active caller-owned real-time timer prevents independent native admission")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise NativeDeadlineExpired("original native deadline expired before admission/finalization")

    def expired(_signal: int, _frame: object) -> None:
        raise NativeDeadlineExpired("original native deadline expired during admission/finalization")

    try:
        signal.signal(signal.SIGALRM, expired)
        try:
            signal.setitimer(signal.ITIMER_REAL, remaining)
        except (OverflowError, OSError, ValueError) as error:
            raise ValueError("native deadline cannot be represented by the selected operating system timer") from error
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)


SOURCE_RENDER_ENV_NAMES = frozenset(
    {
        "MANUSCRIPT_DIR",
        "FIGURES_DIR",
        "OUTPUT_DIR",
        "PDF_DIR",
        "WEB_DIR",
        "SLIDES_DIR",
        "DOCX_DIR",
        "EPUB_DIR",
        "LATEX_COMPILER",
        "PANDOC_PATH",
        "TEMPLATE_DIR",
        "SLIDE_THEME",
        "WEB_THEME",
        "RENDER_SECURITY_PROFILE",
        "RENDER_UNTRUSTED_TEMP_ROOT",
        "ENABLE_PDF",
        "ENABLE_HTML",
        "ENABLE_SLIDES",
        "ENABLE_DOCX",
        "ENABLE_EPUB",
        "AUTHOR_NAME",
        "AUTHOR_ORCID",
        "AUTHOR_EMAIL",
        "DOI",
        "PROJECT_TITLE",
    }
)


def native_environment(root: Path, interpreter: Path, directory: Path) -> dict[str, str]:
    """Use explicit offline policy, source format configuration and no credentials."""
    from infrastructure.core.execution_boundary import build_bounded_env
    from infrastructure.project.public_acceptance_evidence import cell_environment

    env = build_bounded_env(cell_environment(interpreter, directory, repo_root=root))
    for key in tuple(env):
        if key in SOURCE_RENDER_ENV_NAMES or key.startswith("SLIDES_"):
            env.pop(key)
    return env


def create_private_native_directory(root: Path, directory: Path) -> None:
    """Create and permission a fresh owned leaf through held no-follow parents."""
    from infrastructure.core.files.secure_write import (
        _close_all,
        _directory_identity_matches,
        _open_parent,
        _relative_target,
    )

    directory = evidence_directory(root, directory, fresh=True)
    lexical_root, parts, name = _relative_target(root, directory)
    parent, opened = _open_parent(lexical_root, parts, create=True)
    child = -1
    try:
        if not _directory_identity_matches(lexical_root, parts, parent):
            raise ValueError("native evidence parent changed before private creation")
        os.mkdir(name, mode=0o700, dir_fd=parent)
        child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        held = os.fstat(child)
        named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(named.st_mode) or (held.st_dev, held.st_ino) != (
            named.st_dev,
            named.st_ino,
        ):
            raise ValueError("native private evidence leaf changed after creation")
        if not _directory_identity_matches(lexical_root, parts, parent):
            raise ValueError("native evidence parent changed after private creation")
        os.fchmod(child, 0o700)
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (held.st_dev, held.st_ino) != (
            current.st_dev,
            current.st_ino,
        ) or not _directory_identity_matches(lexical_root, parts, parent):
            raise ValueError("native private evidence custody changed during permission admission")
    finally:
        if child >= 0:
            os.close(child)
        _close_all(opened)


def validate_native_specification(specification: dict[str, Any]) -> None:
    """Refuse invalid scopes, paths and budgets before any native execution."""
    names = {
        "scope",
        "run_id",
        "directory",
        "formats",
        "source_digest",
        "timeout_seconds",
        "deadline_monotonic",
        "expected_platform",
        "source_inputs",
    }
    if (
        set(specification) not in (names, names | {"observer_tools"})
        or specification["scope"] not in PUBLIC_PROJECT_NAMES
    ):
        raise ValueError("native worker requires an exact canonical public specification")
    from infrastructure.reporting.native_format_process_custody import (
        require_native_platform,
    )

    require_native_platform(specification["expected_platform"])
    from infrastructure.reporting.native_format_joint_source import (
        validate_joint_source_inputs,
    )

    validate_joint_source_inputs(specification["source_inputs"])
    if "observer_tools" in specification:
        tools = specification["observer_tools"]
        if not isinstance(tools, dict) or set(tools) != {
            "epubcheck_jar",
            "java_executable",
            "frozen_epub_engine",
        }:
            raise ValueError("native observer tools require the exact source-owned selection")
        if (tools["epubcheck_jar"] is None) != (tools["java_executable"] is None):
            raise ValueError("native EPUB observation needs both actual tools")
        for key in ("epubcheck_jar", "java_executable"):
            value = tools[key]
            if value is not None and (
                not isinstance(value, str)
                or not Path(value).is_absolute()
                or ".." in Path(value).parts
                or "\\" in value
                or "\0" in value
            ):
                raise ValueError("native EPUB tool paths must be explicit absolute paths")
        shared = tools["frozen_epub_engine"]
        if shared is not None and (
            tools["epubcheck_jar"] is None
            or not isinstance(shared, str)
            or Path(shared).is_absolute()
            or ".." in Path(shared).parts
            or "\\" in shared
            or "\0" in shared
            or not Path(shared).is_relative_to(Path("output/readiness"))
        ):
            raise ValueError("shared native EPUB engine must remain in confined readiness evidence")
    nonce = specification["run_id"]
    if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise ValueError("native worker requires its fresh run nonce")
    directory = specification["directory"]
    if not isinstance(directory, str) or Path(directory).is_absolute() or ".." in Path(directory).parts:
        raise ValueError("native evidence directory must be repository-relative")
    if not Path(directory).is_relative_to(Path("output/readiness")) or "\\" in directory or "\0" in directory:
        raise ValueError("native evidence directory is outside public readiness custody")
    formats = specification["formats"]
    if (
        not isinstance(formats, list)
        or not formats
        or any(item not in {"pdf", "html", "slides", "docx", "epub"} for item in formats)
        or len(set(formats)) != len(formats)
    ):
        raise ValueError("native worker formats must be unique supported declarations")
    digest = specification["source_digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("native source identity is invalid")
    for name in ("timeout_seconds", "deadline_monotonic"):
        value = specification[name]
        if type(value) not in {int, float} or not math.isfinite(value) or value <= 0:
            raise ValueError("native execution requires positive finite admitted budgets")


@dataclass(frozen=True)
class NativeArtifact:
    """One artifact whose identity comes from the source contract."""

    id: str
    format: str
    path: str


def public_source_digest(root: Path) -> str:
    """Bind public source/config/locks without outputs that rendering must change."""
    reader = SnapshotReader(root)
    records = [
        (
            path.relative_to(root).as_posix(),
            reader.read(path.relative_to(root).as_posix()).sha256,
        )
        for path in public_source_paths(root)
    ]
    if not records or not reader.unchanged():
        raise ValueError("public source custody changed during native admission")
    return canonical_digest(records)


def _mapping(reader: SnapshotReader, relative: str) -> dict[str, Any]:
    value = yaml.safe_load(reader.read(relative).content)
    if not isinstance(value, dict):
        raise ValueError(f"native source declaration is not a mapping: {relative}")
    return value


def _basename(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is None:
        raise ValueError("native artifact basename is unsafe or missing")
    return value


def native_artifact_contract(
    root: Path, scope: str, formats: tuple[str, ...], reader: SnapshotReader
) -> tuple[NativeArtifact, ...]:
    """Compile all native identities, including the project-owned primary editions.

    Hydrated manuscript names are accepted only as exact consumed public inputs;
    the worker additionally requires current rendered-provenance validation.
    No output glob can nominate a passing artifact.
    """
    if scope not in PUBLIC_PROJECT_NAMES or not formats or len(set(formats)) != len(formats):
        raise ValueError("native acceptance requires a canonical public scope and declared formats")
    base = f"projects/{scope}"
    project = root / base
    output = f"{base}/output"
    basename = Path(scope).name
    manuscript = render_config_manuscript_dir(project)
    config = _mapping(reader, f"{base}/manuscript/config.yaml")
    consumed = discover_manuscript_files(manuscript)
    if not consumed:
        raise ValueError("native acceptance has no current manuscript sources")
    for path in consumed:
        reader.read(path.relative_to(root).as_posix())
    rows: list[NativeArtifact] = []

    def add(id_: str, kind: str, relative: str) -> None:
        path = Path(relative)
        if not path.is_relative_to(Path(output)) or ".." in path.parts:
            raise ValueError("native identity escapes its public project output")
        reader.public_path(relative)
        rows.append(NativeArtifact(id_, kind, path.as_posix()))

    for kind in formats:
        if kind == "pdf":
            add("manuscript:pdf", "pdf", f"{output}/pdf/{basename}_combined.pdf")
            for source in consumed:
                if source.suffix == ".tex" and not is_transmission_bookend(source):
                    add(
                        f"section:{source.relative_to(manuscript).as_posix()}:pdf",
                        "pdf",
                        f"{output}/pdf/{source.stem}.pdf",
                    )
        elif kind == "html":
            add("manuscript:html", "html", f"{output}/web/index.html")
            for source in consumed:
                if source.suffix != ".md" or is_transmission_bookend(source):
                    continue
                raw = f"{source.parent.name}__{source.stem}"
                stem = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-._") or source.stem
                add(
                    f"section:{source.relative_to(manuscript).as_posix()}:html",
                    "html",
                    f"{output}/web/{stem}.html",
                )
        elif kind == "slides":
            effective = _mapping(reader, (manuscript / "config.yaml").relative_to(root).as_posix())
            profile = effective.get("render", {}).get("slides", {}).get("profile", "archive")
            for source in consumed:
                if source.suffix != ".md" or is_transmission_bookend(source):
                    continue
                text = reader.read(source.relative_to(root).as_posix()).content.decode()
                if "<!-- render:skip-beamer -->" in text:
                    continue
                add(
                    f"section:{source.relative_to(manuscript).as_posix()}:slides",
                    "pdf",
                    f"{output}/slides/{source.stem}_slides.pdf",
                )
                if profile == "accessible":
                    add(
                        f"section:{source.relative_to(manuscript).as_posix()}:reveal",
                        "html",
                        f"{output}/slides/{source.stem}_slides.html",
                    )
        elif kind in {"docx", "epub"}:
            add(
                f"manuscript:{kind}",
                kind,
                f"{output}/{kind}/{basename}_combined.{kind}",
            )
        else:
            raise ValueError("native acceptance received an unsupported declared format")

    if scope == "templates/template_pitch_deck":
        deck = config.get("project_config", {}).get("deck")
        if not isinstance(deck, dict):
            raise ValueError("native deck obligations require current project_config.deck")
        kinds = deck.get("formats", ["pdf", "pptx"])
        if (
            not isinstance(kinds, list)
            or not kinds
            or any(kind not in {"pdf", "pptx"} for kind in kinds)
            or len(set(kinds)) != len(kinds)
            or "pdf" not in kinds
        ):
            raise ValueError("native deck format declarations are invalid")
        subject = _basename(deck.get("pitch_subject", "template_template"))
        for length in ("short", "medium", "long"):
            for kind in kinds:
                add(
                    f"pitch:{length}:{kind}",
                    kind,
                    f"{output}/{kind}/{subject}_pitch_{length}.{kind}",
                )
    if scope == "templates/template_newspaper":
        edition = _mapping(reader, f"{base}/content/edition.yaml")
        name = _basename(edition.get("render", {}).get("output_basename", "the-triplicate"))
        add("newspaper:edition:pdf", "pdf", f"{output}/pdf/{name}.pdf")
    if scope == "templates/template_storybook":
        story = _mapping(reader, f"{base}/content/story.yaml")
        book, pages = story.get("storybook"), story.get("pages")
        if not isinstance(book, dict) or not isinstance(pages, list) or not pages:
            raise ValueError("native storybook obligations are incomplete")
        target = book.get("output_pdf")
        if not isinstance(target, str):
            raise ValueError("storybook must declare its primary PDF")
        add("storybook:print:pdf", "pdf", f"{base}/{target}")
        for number, page in enumerate(pages):
            if not isinstance(page, dict) or type(page.get("number")) is not int or page["number"] != number:
                raise ValueError("storybook page identities must be contiguous")
            slug = _basename(page.get("slug"))
            name = "00_cover.png" if number == 0 else f"{number:02d}_{slug}.png"
            add(
                f"storybook:page:{number}",
                "png",
                f"{output}/figures/storybook_pages/{name}",
            )
        add(
            "storybook:contact-sheet",
            "png",
            f"{output}/figures/storybook_contact_sheet.png",
        )
    if len({row.id for row in rows}) != len(rows) or len({row.path for row in rows}) != len(rows):
        raise ValueError("native artifact obligations collide")
    if "slides" in formats and not any(row.id.endswith(":slides") for row in rows):
        raise ValueError("enabled slides have no source-owned native artifacts")
    return tuple(rows)


def contract_digest(rows: tuple[NativeArtifact, ...]) -> str:
    """Hash ordered independently compiled artifact obligations."""
    return canonical_digest([asdict(row) for row in rows])


def unsupported_native_controls(scope: str, formats: tuple[str, ...]) -> list[dict[str, str]]:
    """Keep absent native/visual oracles explicit even after structural success."""
    blockers = []
    controls = {
        "pdf": (
            "pdf-visual-source-parity",
            "source-content/layout parity and visual negative controls are not implemented",
        ),
        "html": (
            "browser-layout",
            "fresh browser DOM/reflow/asset and source-content parity controls are not implemented",
        ),
        "docx": (
            "native-docx-layout",
            "native DOCX viewing/conversion and source-content/layout parity controls are not implemented",
        ),
        "epub": (
            "native-epub-reader",
            "EPUBCheck/reader execution and source-content/layout parity controls are not implemented",
        ),
        "slides": (
            "projection-visual-oracle",
            "all-deck projection typography, clipping, and visual negative controls are not implemented",
        ),
    }
    for kind in formats:
        if kind in controls:
            tool, reason = controls[kind]
            blockers.append({"tool": tool, "reason": reason})
    extra = {
        "templates/template_pitch_deck": (
            "pitch-native-parity",
            "all three PDF/PPTX pairs need actual native layout, citation/QR-target and content-parity controls",
        ),
        "templates/template_newspaper": (
            "newspaper-print-oracle",
            "configured editions need independent print geometry, font, content separation and raster controls",
        ),
        "templates/template_storybook": (
            "storybook-print-oracle",
            "all pages need print-scale visual and localized text/background pixel negative controls",
        ),
    }
    if scope in extra:
        tool, reason = extra[scope]
        blockers.append({"tool": tool, "reason": reason})
    return blockers
