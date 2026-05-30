"""Generate a one-page architecture diagram from live repository state.

This module discovers ``infrastructure/`` packages and ``projects/`` from the
filesystem and emits a Mermaid ``flowchart TB`` source plus a rendered ``.svg``.

Two public functions are exposed:

* :func:`build_architecture_mermaid` — pure function that scans the repo and
  returns the Mermaid source string (deterministic, sorted alphabetically).
* :func:`render_architecture_svg` — runs the above, writes the ``.mmd`` source
  alongside the rendered ``.svg`` via the ``mmdc`` (mermaid-cli) binary.

The renderer is **zero-mock**: it shells out to a real ``mmdc`` install via
``subprocess``. If ``mmdc`` is missing on ``PATH`` it raises :class:`RuntimeError`
with a clear remediation hint so callers (and tests) can skip gracefully.

The Mermaid source uses **double-quoted node labels** so that the diagram parses
cleanly when rendered by GitHub's Mermaid frontend. The legacy ``[/path/]``
parallelogram syntax is intentionally avoided (GitHub's parser has rejected it
in the past for this repo's other generated diagrams).
"""

import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.public_scope import public_project_names

logger = get_logger(__name__)


# Default Chrome path used by the local mermaid-cli setup. mmdc launches
# Puppeteer which needs a Chromium-compatible browser; on macOS dev machines
# the system Chrome works and avoids a separate Chromium download.
_DEFAULT_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _discover_infrastructure_packages(repo_root: Path) -> list[str]:
    """Return alphabetically-sorted names of Python packages under ``infrastructure/``.

    A directory is treated as a package iff it contains an ``__init__.py``.
    Hidden directories and ``__pycache__`` are skipped.
    """
    infra_dir = repo_root / "infrastructure"
    if not infra_dir.is_dir():
        return []

    names: list[str] = []
    for child in infra_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name == "__pycache__":
            continue
        if (child / "__init__.py").is_file():
            names.append(child.name)
    return sorted(names)


def _discover_infrastructure_config_dirs(repo_root: Path) -> list[str]:
    """Return alphabetically-sorted names of non-Python config dirs under ``infrastructure/``.

    These are sibling directories that do not have an ``__init__.py`` but are
    still part of the infrastructure layer (e.g. ``config/``, ``docker/``,
    ``logrotate.d/``). Used to render a separate "Config" cluster on the diagram.
    """
    infra_dir = repo_root / "infrastructure"
    if not infra_dir.is_dir():
        return []

    names: list[str] = []
    for child in infra_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name == "__pycache__":
            continue
        if not (child / "__init__.py").is_file():
            names.append(child.name)
    return sorted(names)


def _project_qualified_names(repo_root: Path) -> list[str]:
    """Return alphabetically-sorted public project names.

    Runtime discovery may include local-only symlinked private projects. This
    generated diagram is committed to the public repository, so it uses the
    narrower public template scope.
    """
    try:
        return public_project_names(repo_root)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("public project scope discovery failed: %s", exc)
        return []


def _safe_node_id(prefix: str, name: str) -> str:
    """Return a Mermaid-safe node id derived from ``name``.

    Mermaid node identifiers must be ASCII-alphanumeric (plus ``_``). We map
    every other character to ``_`` and prepend ``prefix`` so ids are unique
    across clusters.
    """
    cleaned = "".join(c if c.isalnum() else "_" for c in name)
    return f"{prefix}_{cleaned}"


def build_architecture_mermaid(repo_root: Path) -> str:
    """Build a Mermaid ``flowchart TB`` source string for the live repo layout.

    The diagram has three clusters:

    1. **Infrastructure (Python packages)** — every directory under
       ``infrastructure/`` containing an ``__init__.py``.
    2. **Infrastructure (Config)** — sibling directories without ``__init__.py``
       (``config/``, ``docker/``, ``logrotate.d/`` at the time of writing).
    3. **Projects** — tracked public exemplar projects. Runtime discovery may
       include additional local-only symlinked projects; those are not rendered
       into committed public docs.

    All three clusters connect to a central ``Pipeline`` node so the diagram
    reads as a single page.

    Args:
        repo_root: Repository root directory (the parent of ``infrastructure/``).

    Returns:
        A complete Mermaid ``flowchart TB`` source string. Lines are joined by
        ``\\n`` and the string ends with a trailing newline so the file parses
        as valid Markdown when wrapped in a fence.
    """
    repo_root = Path(repo_root).resolve()

    packages = _discover_infrastructure_packages(repo_root)
    config_dirs = _discover_infrastructure_config_dirs(repo_root)
    projects = _project_qualified_names(repo_root)

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines: list[str] = [
        f"%% Generated by infrastructure.documentation.architecture_overview at {timestamp}",
        "%% Re-run scripts/generate_architecture_overview.py to refresh.",
        "flowchart TB",
        '    Pipeline["Pipeline orchestrator<br/>scripts/ + run.sh"]',
        "",
        '    subgraph InfraPy["Infrastructure (Python packages)"]',
        "        direction TB",
    ]
    for name in packages:
        node_id = _safe_node_id("infra", name)
        label = f"infrastructure/{name}/"
        lines.append(f'        {node_id}["{label}"]')
    lines.append("    end")
    lines.append("")

    lines.append('    subgraph InfraCfg["Infrastructure (Config)"]')
    lines.append("        direction TB")
    if config_dirs:
        for name in config_dirs:
            node_id = _safe_node_id("cfg", name)
            label = f"infrastructure/{name}/"
            lines.append(f'        {node_id}["{label}"]')
    else:
        lines.append('        cfg__none["(no non-Python config dirs)"]')
    lines.append("    end")
    lines.append("")

    lines.append('    subgraph Projects["Projects (public CI scope)"]')
    lines.append("        direction TB")
    if projects:
        for qname in projects:
            node_id = _safe_node_id("proj", qname)
            label = f"projects/{qname}/"
            lines.append(f'        {node_id}["{label}"]')
    else:
        lines.append('        proj__none["(no active projects discovered)"]')
    lines.append("    end")
    lines.append("")

    # Cluster-level edges. We draw edges from cluster anchors to keep the
    # diagram readable on a single page rather than fanning out from every node.
    lines.append("    InfraPy --> Pipeline")
    lines.append("    InfraCfg --> Pipeline")
    lines.append("    Pipeline --> Projects")
    lines.append("")

    return "\n".join(lines) + "\n"


def render_architecture_svg(repo_root: Path, output_path: Path) -> Path:
    """Render the architecture diagram to ``output_path`` (SVG) plus a sibling ``.mmd``.

    The function:

    1. Builds the Mermaid source via :func:`build_architecture_mermaid`.
    2. Writes the source to ``output_path.with_suffix(".mmd")``.
    3. Invokes the ``mmdc`` (mermaid-cli) binary via ``subprocess`` with a
       generated Puppeteer config that points at the system Chrome.
    4. Writes the rendered ``.svg`` to ``output_path``.

    Args:
        repo_root: Repository root.
        output_path: Final ``.svg`` path. The parent directory is created if
            missing. The sibling ``.mmd`` is written next to it (same stem).

    Returns:
        The resolved ``output_path`` (SVG file).

    Raises:
        RuntimeError: If ``mmdc`` is not available on ``PATH``, or if the
            ``mmdc`` invocation exits non-zero. The error message includes
            stderr so callers can diagnose Chrome / Puppeteer issues.
    """
    repo_root = Path(repo_root).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mmd_path = output_path.with_suffix(".mmd")
    mermaid_source = build_architecture_mermaid(repo_root)
    mmd_path.write_text(mermaid_source, encoding="utf-8")
    logger.info("Wrote Mermaid source: %s (%d bytes)", mmd_path, mmd_path.stat().st_size)

    mmdc_bin = shutil.which("mmdc")
    if mmdc_bin is None:
        raise RuntimeError(
            "mmdc (mermaid-cli) not found on PATH. Install with "
            "`npm install -g @mermaid-js/mermaid-cli` or `brew install mermaid-cli`."
        )

    # Write a Puppeteer config that points at the system Chrome so mmdc does
    # not download its own Chromium. We pass --no-sandbox so the launch works
    # from CI containers and from macOS shells that lack a TTY.
    with tempfile.TemporaryDirectory() as tmp:
        puppeteer_cfg = Path(tmp) / "puppeteer.json"
        puppeteer_cfg.write_text(
            json.dumps(
                {
                    "executablePath": _DEFAULT_CHROME_PATH,
                    "args": ["--no-sandbox"],
                }
            ),
            encoding="utf-8",
        )

        cmd = [
            mmdc_bin,
            "-i",
            str(mmd_path),
            "-o",
            str(output_path),
            "-e",
            "svg",
            "-b",
            "white",
            "-p",
            str(puppeteer_cfg),
            "-q",
        ]
        logger.info("Invoking mmdc: %s", " ".join(cmd))
        result = subprocess.run(  # noqa: S603 - command list is built from validated paths
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"mmdc failed with exit code {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    if not output_path.is_file():
        raise RuntimeError(
            f"mmdc reported success but {output_path} does not exist. stdout: {result.stdout} stderr: {result.stderr}"
        )

    logger.info("Wrote SVG: %s (%d bytes)", output_path, output_path.stat().st_size)
    return output_path


__all__ = ["build_architecture_mermaid", "render_architecture_svg"]
