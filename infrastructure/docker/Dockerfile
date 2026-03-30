# Research Project Template - Development Environment
# Modernized with uv for fast, reproducible dependency management
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    UV_FROZEN=true \
    MPLBACKEND=Agg

# Install system dependencies for research workflows
RUN apt-get update && apt-get install -y --no-install-recommends \
    # LaTeX for PDF generation
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-xetex \
    # Ollama for LLM support (if running Ollama server externally)
    curl \
    # Development tools
    git \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN useradd --create-home --shell /bin/bash research && \
    chown -R research:research /home/research

USER research
WORKDIR /home/research/template

# Copy dependency files first (cache layer)
COPY --chown=research:research pyproject.toml uv.lock ./

# Install dependencies with uv (fast, reproducible)
RUN uv sync --frozen --no-dev

# Copy project files
COPY --chown=research:research . .

# Install project in editable mode with dev dependencies
RUN uv sync --frozen

# Create volume mount point for data persistence
VOLUME ["/home/research/template/output"]

# Default command
CMD ["bash"]