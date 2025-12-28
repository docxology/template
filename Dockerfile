# Research Project Template - Development Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for research workflows
RUN apt-get update && apt-get install -y \
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
    vim \
    htop \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash research && \
    chown -R research:research /home/research

USER research
WORKDIR /home/research

# Copy project files
COPY --chown=research:research . /home/research/template/

# Set working directory to project
WORKDIR /home/research/template

# Install Python dependencies
RUN pip install --user -e . && \
    pip install --user pre-commit ruff mypy safety bandit

# Add local bin to PATH
ENV PATH="/home/research/.local/bin:$PATH"

# Create volume mount point for data persistence
VOLUME ["/home/research/template/output", "/home/research/template/project/output"]

# Default command
CMD ["bash"]