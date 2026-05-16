"""Render inline Mermaid fences for combined PDF builds.

Pandoc does not render Mermaid diagrams by itself. Combined PDF rendering
therefore converts each fenced Mermaid block into a deterministic PNG and
replaces the fence with a normal Markdown image reference before Pandoc runs.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_MERMAID_BLOCK_RE: Final[re.Pattern[str]] = re.compile(
    r"```\s*mermaid\s*\n(?P<source>.*?)```"
    r"(?P<alts>(?:\s*<!--\s*alt:\s*.*?\s*-->)+)?"
    r"(?P<caption>\s*\n[ \t]*\*(?!\*)(?P<caption_text>[^\n]+?)\*[ \t]*(?=\n|$))?",
    flags=re.DOTALL | re.IGNORECASE,
)
_ALT_RE: Final[re.Pattern[str]] = re.compile(r"<!--\s*alt:\s*(?P<alt>.*?)\s*-->", flags=re.DOTALL)
_SQUARE_LABEL_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<prefix>\b[A-Za-z][\w.-]*)\[(?P<label>(?![\"`])[^]\n]*<br/>[^]\n]*)\]"
)
_BRACE_LABEL_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<prefix>\b[A-Za-z][\w.-]*)\{(?P<label>(?![\"`])[^}\n]*<br/>[^}\n]*)\}"
)
_STATE_DESCRIPTION_RE: Final[re.Pattern[str]] = re.compile(r"^\s*[A-Za-z_][\w.-]*\s*:")


@dataclass(frozen=True)
class MermaidReplacementResult:
    """Result of replacing inline Mermaid fences."""

    content: str
    diagrams_rendered: int


def replace_inline_mermaid(content: str, manuscript_dir: Path | None) -> MermaidReplacementResult:
    """Render Mermaid fences and replace them with Markdown image references.

    Args:
        content: Combined Markdown content.
        manuscript_dir: Manuscript directory for resolving project output paths.

    Returns:
        Rewritten content and the number of Mermaid blocks processed.
    """
    if not _MERMAID_BLOCK_RE.search(content):
        return MermaidReplacementResult(content, 0)
    if manuscript_dir is None:
        logger.warning("Mermaid blocks found but no manuscript_dir was supplied; leaving fences unchanged")
        return MermaidReplacementResult(content, 0)

    output_dir = _inline_mermaid_dir(Path(manuscript_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    puppeteer_config = _find_puppeteer_config(Path(manuscript_dir))
    mmdc = shutil.which("mmdc")
    if mmdc is None:
        raise RenderingError(
            "Mermaid CLI 'mmdc' is required to render inline Mermaid diagrams for PDF output. "
            "Install @mermaid-js/mermaid-cli and rerun the PDF render."
        )
    expected_artifacts = _expected_inline_artifacts(content)
    _prune_inline_mermaid_dir(output_dir, expected_artifacts)

    index = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal index
        index += 1
        source = _normalise_mermaid_source(match.group("source").strip())
        alt = _first_alt(match.group("alts")) or "Mermaid diagram"
        caption = _caption_for_markdown(_caption_text(match) or alt)
        stem = f"inline_mermaid_{index:04d}_{_source_hash(source)}"
        png_path = _render_mermaid(
            mmdc=mmdc,
            output_dir=output_dir,
            stem=stem,
            source=source,
            puppeteer_config=puppeteer_config,
        )
        rel_path = f"../figures/mermaid_inline/{png_path.name}"
        escaped_caption = _latex_caption(caption)
        return (
            "\n\\begin{figure}[htbp]\n"
            "\\centering\n"
            f"\\includegraphics[width=0.82\\linewidth,height=4.2in,keepaspectratio]{{{rel_path}}}\n"
            f"\\caption{{{escaped_caption}}}\n"
            "\\end{figure}\n"
        )

    rewritten = _MERMAID_BLOCK_RE.sub(_replace, content)
    logger.info("Rendered %d inline Mermaid diagram(s) for PDF output", index)
    return MermaidReplacementResult(rewritten, index)


def _inline_mermaid_dir(manuscript_dir: Path) -> Path:
    """Return the project output directory for inline Mermaid images."""
    if manuscript_dir.name == "manuscript" and manuscript_dir.parent.name == "output":
        return manuscript_dir.parent / "figures" / "mermaid_inline"
    if manuscript_dir.name == "manuscript":
        return manuscript_dir.parent / "output" / "figures" / "mermaid_inline"
    return manuscript_dir / "output" / "figures" / "mermaid_inline"


def _expected_inline_artifacts(content: str) -> set[str]:
    """Return the exact inline Mermaid artifact filenames for this build."""
    expected: set[str] = set()
    for index, match in enumerate(_MERMAID_BLOCK_RE.finditer(content), start=1):
        source = _normalise_mermaid_source(match.group("source").strip())
        stem = f"inline_mermaid_{index:04d}_{_source_hash(source)}"
        expected.add(f"{stem}.mmd")
        expected.add(f"{stem}.png")
    return expected


def _prune_inline_mermaid_dir(output_dir: Path, expected_artifacts: set[str]) -> None:
    """Remove stale inline Mermaid render artifacts without discarding cache hits."""
    for pattern in ("inline_mermaid_*.png", "inline_mermaid_*.mmd"):
        for artifact in output_dir.glob(pattern):
            if artifact.name not in expected_artifacts:
                artifact.unlink()


def _find_puppeteer_config(start: Path) -> Path | None:
    """Walk upward to find a project-level Puppeteer config for mmdc."""
    for candidate in (start, *start.parents):
        config = candidate / ".puppeteer.json"
        if config.is_file():
            return config
    return None


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def _normalise_mermaid_source(source: str) -> str:
    """Return a render-ready Mermaid source while preserving diagram semantics.

    Older manuscript sections used literal ``\n`` escapes inside node and edge
    labels. Mermaid CLI is stricter than the Markdown previewers that tolerated
    those escapes, so normalise them according to the diagram grammar before
    rendering.
    """
    if _diagram_kind(source).startswith("statediagram"):
        return _normalise_state_diagram_text(source)
    normalised = source.replace(r"\n", "<br/>")
    normalised = _normalise_sequence_diagram_text(normalised)
    return _quote_html_break_labels(normalised)


def _diagram_kind(source: str) -> str:
    """Return the first non-empty Mermaid directive in lowercase."""
    for line in source.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lower()
    return ""


def _normalise_state_diagram_text(source: str) -> str:
    """Make prose-heavy state-diagram labels acceptable to Mermaid.

    State diagrams allow labels after a single colon, but additional colons in
    the label body are parsed as syntax. Keep literal line breaks valid for this
    grammar and replace only those secondary prose colons.
    """
    lines: list[str] = []
    for line in source.replace("<br/>", r"\n").splitlines():
        lines.append(_normalise_state_label_line(line))
    return "\n".join(lines)


def _normalise_state_label_line(line: str) -> str:
    stripped = line.lstrip()
    lowered = stripped.lower()
    is_state_description = _STATE_DESCRIPTION_RE.match(line) is not None
    if (
        "-->" not in stripped
        and not lowered.startswith(("note left of ", "note right of ", "note over "))
        and not is_state_description
    ):
        return line
    head, separator, label = line.partition(":")
    if not separator:
        return line
    label = label.replace(":", " -")
    label = label.replace(";", ",")
    return f"{head}:{label}"


def _normalise_sequence_diagram_text(source: str) -> str:
    """Make prose-heavy sequence-diagram labels acceptable to Mermaid."""
    if _diagram_kind(source) != "sequencediagram":
        return source
    return source.replace(";", ",")


def _quote_html_break_labels(source: str) -> str:
    """Quote flowchart labels that contain HTML breaks.

    Mermaid treats ``<br/>`` followed by punctuation in unquoted node labels as
    syntax, so labels such as ``A[step<br/>(detail)]`` must become
    ``A["step<br/>(detail)"]``. Already quoted labels are left unchanged.
    """

    def quote_square(match: re.Match[str]) -> str:
        label = _mermaid_quoted_label(match.group("label"))
        return f'{match.group("prefix")}["{label}"]'

    def quote_brace(match: re.Match[str]) -> str:
        label = _mermaid_quoted_label(match.group("label"))
        return f'{match.group("prefix")}{{"{label}"}}'

    source = _SQUARE_LABEL_RE.sub(quote_square, source)
    return _BRACE_LABEL_RE.sub(quote_brace, source)


def _mermaid_quoted_label(label: str) -> str:
    return label.replace('"', "&quot;")


def _first_alt(raw_alts: str | None) -> str:
    if not raw_alts:
        return ""
    match = _ALT_RE.search(raw_alts)
    if match is None:
        return ""
    return " ".join(match.group("alt").split())


def _caption_text(match: re.Match[str]) -> str:
    raw_caption = match.group("caption_text")
    if raw_caption is None:
        return ""
    return " ".join(raw_caption.split())


def _caption_for_markdown(text: str) -> str:
    """Return caption text that is accessible and LaTeX-font friendly."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("`", "")
    replacements = {
        "α": "alpha",
        "β": "beta",
        "γ": "gamma",
        "δ": "delta",
        "ε": "epsilon",
        "θ": "theta",
        "κ": "kappa",
        "λ": "lambda",
        "μ": "mu",
        "π": "pi",
        "σ": "sigma",
        "φ": "phi",
        "χ": "chi",
        "Δ": "Delta",
        "Σ": "Sigma",
        "Ψ": "Psi",
        "🔬": "clinical",
        "🫛": "pea genetics",
        "📊": "data",
        "🌿": "plant",
        "💧": "water",
        "🌬️": "wind",
        "🌬": "wind",
        "☀️": "sunlight",
        "☀": "sunlight",
        "⚖️": "balance",
        "⚖": "balance",
        "↑": "increased",
        "↓": "decreased",
        "→": "to",
        "←": "from",
        "↔": "between",
        "≈": "about",
        "∼": "about",
        "≤": "less than or equal to",
        "≥": "greater than or equal to",
        "∝": "is proportional to",
        "√": "square root",
        "⊣": "inhibits",
        "⇌": "reversible reaction",
        "∣": "|",
        "×": "x",
        "°": " degrees ",
        "⁺": "+",
        "⁻": "-",
        "¹": "1",
        "²": "2",
        "³": "3",
        "₀": "0",
        "₁": "1",
        "₂": "2",
        "₃": "3",
        "₄": "4",
        "₅": "5",
        "₆": "6",
        "₇": "7",
        "₈": "8",
        "₉": "9",
        "ᵢ": "_i",
        "—": "-",
        "–": "-",
        "’": "'",
        "“": '"',
        "”": '"',
        "\ufe0f": "",
    }
    for glyph, replacement in replacements.items():
        text = text.replace(glyph, replacement)
    text = text.encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def _latex_caption(text: str) -> str:
    """Escape sanitized caption text for a raw LaTeX caption."""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _markdown_alt(text: str) -> str:
    cleaned = " ".join(text.split())
    cleaned = cleaned.replace("[", "(").replace("]", ")")
    return cleaned or "Mermaid diagram"


def _render_mermaid(
    *,
    mmdc: str,
    output_dir: Path,
    stem: str,
    source: str,
    puppeteer_config: Path | None,
) -> Path:
    """Render one Mermaid source string to PNG with strict failure handling."""
    if not source:
        raise RenderingError(f"Inline Mermaid block {stem} is empty")

    mmd_path = output_dir / f"{stem}.mmd"
    png_path = output_dir / f"{stem}.png"
    if png_path.is_file() and png_path.stat().st_size > 0 and mmd_path.is_file():
        if mmd_path.read_text(encoding="utf-8").rstrip("\n") == source:
            return png_path

    mmd_path.write_text(source + "\n", encoding="utf-8")
    cmd = [
        mmdc,
        "--input",
        str(mmd_path),
        "--output",
        str(png_path),
        "--width",
        "1400",
        "--height",
        "900",
        "--backgroundColor",
        "white",
        "--quiet",
    ]
    if puppeteer_config is not None:
        cmd.extend(["--puppeteerConfigFile", str(puppeteer_config)])

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderingError(f"mmdc timed out while rendering {stem}") from exc
    except OSError as exc:
        raise RenderingError(f"Could not execute mmdc while rendering {stem}: {exc}") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise RenderingError(f"mmdc failed for {stem}: {stderr[:800]}")
    if not png_path.is_file() or png_path.stat().st_size == 0:
        raise RenderingError(f"mmdc reported success for {stem} but did not produce a PNG")
    return png_path


__all__ = ["MermaidReplacementResult", "replace_inline_mermaid"]
