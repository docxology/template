"""Generator for the executable-bundle Dockerfile.

Produces a reproducible-build Dockerfile parameterized by Python version and
LaTeX package list. Mirrors the design in
``docs/maintenance/stage-10-executable-bundle.md``.

Output is deterministic given the same inputs — a Dockerfile generated today
and one generated next year from the same project state will be byte-identical
except for the timestamp comment at the top.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final

__all__ = [
    "DockerfileConfig",
    "build_dockerfile",
    "DEFAULT_BASE_IMAGE",
    "DEFAULT_LATEX_PACKAGES",
]


DEFAULT_BASE_IMAGE: Final[str] = "ubuntu:24.04"

# LaTeX packages this template's PDF rendering depends on at minimum.
# Mirror of the troubleshooting list in docs/operational/troubleshooting/.
DEFAULT_LATEX_PACKAGES: Final[tuple[str, ...]] = (
    "texlive-latex-base",
    "texlive-latex-extra",
    "texlive-fonts-recommended",
    "texlive-fonts-extra",
    "texlive-science",
    "texlive-publishers",
    "texlive-xetex",
)

# tlmgr packages installed at runtime that aren't in the apt texlive bundle.
DEFAULT_TLMGR_PACKAGES: Final[tuple[str, ...]] = (
    "multirow",
    "cleveref",
    "doi",
    "newunicodechar",
)


@dataclass(frozen=True)
class DockerfileConfig:
    """Inputs to the Dockerfile generator."""

    project_name: str
    python_version: str  # e.g. "3.12"
    base_image: str = DEFAULT_BASE_IMAGE
    latex_packages: tuple[str, ...] = DEFAULT_LATEX_PACKAGES
    tlmgr_packages: tuple[str, ...] = DEFAULT_TLMGR_PACKAGES
    uv_version: str = "latest"  # uv install pin (latest by default; pin for full reproducibility)


def build_dockerfile(config: DockerfileConfig) -> str:
    """Return the Dockerfile text for the given config.

    The Dockerfile is a single-stage build that:

    1. Starts from a pinned Ubuntu base
    2. Installs system packages (Python build deps + LaTeX + git)
    3. Installs ``uv`` for Python package management
    4. Copies the source tree into ``/workspace``
    5. Runs ``uv sync`` to install Python deps from the lockfile
    6. Sets ``MPLBACKEND=Agg`` for headless plotting
    7. Defaults to running the project's ``run.sh --pipeline --project <name> --core-only``
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    py_version_tag = config.python_version
    latex_pkg_line = " \\\n    ".join(config.latex_packages)
    tlmgr_pkg_line = " ".join(config.tlmgr_packages)

    lines = [
        f"# Auto-generated Dockerfile for executable-bundle of project {config.project_name!r}.",
        f"# Generated at {timestamp} by infrastructure/rendering/dockerfile_gen.py.",
        "# See docs/maintenance/stage-10-executable-bundle.md for rationale.",
        "",
        f"FROM {config.base_image}",
        "",
        "ENV DEBIAN_FRONTEND=noninteractive \\",
        "    PYTHONDONTWRITEBYTECODE=1 \\",
        "    PYTHONUNBUFFERED=1 \\",
        "    MPLBACKEND=Agg",
        "",
        "RUN apt-get update && apt-get install -y --no-install-recommends \\",
        f"    python{py_version_tag} \\",
        f"    python{py_version_tag}-venv \\",
        f"    python{py_version_tag}-dev \\",
        "    build-essential \\",
        "    git \\",
        "    curl \\",
        "    ca-certificates \\",
        f"    {latex_pkg_line} \\",
        "  && rm -rf /var/lib/apt/lists/*",
        "",
        "# Install additional LaTeX packages via tlmgr (template-specific)",
        f"RUN tlmgr init-usertree || true && tlmgr install {tlmgr_pkg_line} || true",
        "",
        f"# Install uv ({config.uv_version})",
        "RUN curl -LsSf https://astral.sh/uv/install.sh | sh",
        'ENV PATH="/root/.local/bin:${PATH}"',
        "",
        "WORKDIR /workspace",
        "COPY . /workspace/",
        "",
        "# Install Python deps from the committed lockfile",
        "RUN uv sync --frozen",
        "",
        f"# Default entry: run the core pipeline for project {config.project_name!r}",
        f'CMD ["bash", "-lc", "./run.sh --pipeline --project {config.project_name} --core-only"]',
        "",
    ]
    return "\n".join(lines)


def build_compose_yaml(project_name: str) -> str:
    """Return a minimal docker-compose.yml for the bundle.

    Provides four named services matching the manifest's entry_points so the
    bundle is self-describing.
    """

    return (
        "# Auto-generated docker-compose.yml — see manifest.json entry_points.\n"
        "services:\n"
        "  reproduce:\n"
        "    build:\n"
        "      context: .\n"
        f"    image: template-bundle-{project_name}:latest\n"
        "    environment:\n"
        "      - MPLBACKEND=Agg\n"
        "  tests:\n"
        f"    image: template-bundle-{project_name}:latest\n"
        f'    command: ["bash", "-lc", "uv run python scripts/01_run_tests.py --project {project_name}"]\n'
        "  render:\n"
        f"    image: template-bundle-{project_name}:latest\n"
        f'    command: ["bash", "-lc", "uv run python scripts/03_render_pdf.py --project {project_name}"]\n'
        "  verify:\n"
        f"    image: template-bundle-{project_name}:latest\n"
        f'    command: ["bash", "-lc", "uv run pytest tests/regression/projects/{project_name} -v"]\n'
    )
