# Research Project Template - Development Environment
# Modernized with uv for fast, reproducible dependency management
# The available base supplies system libraries; .python-version selects the runtime.
# The current full repository profile requires 3.14 for its locked jaxlib dependency.
FROM python:3.14-slim

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

# Install the immutable official uv 0.13.0 release after verifying its checksum.
RUN curl --proto '=https' --tlsv1.2 -fsSL \
      https://github.com/astral-sh/uv/releases/download/0.13.0/uv-installer.sh -o /tmp/uv-install.sh \
    && echo '283cbef4bdaca819bd896b0dacb8a085c4c05dbc880642aa5001d97bc4db74ba  /tmp/uv-install.sh' | sha256sum -c - \
    && UV_UNMANAGED_INSTALL=/usr/local/bin sh /tmp/uv-install.sh \
    && rm -f /tmp/uv-install.sh \
    && test "$(uv --version | cut -d ' ' -f 1-2)" = 'uv 0.13.0'

# Create non-root user
RUN useradd --create-home --shell /bin/bash research && \
    chown -R research:research /home/research

USER research
WORKDIR /home/research/template

# Copy dependency files first (cache layer)
COPY --chown=research:research pyproject.toml uv.lock .python-version ./

# Resolve the copied project pin; the cache layer has no package source yet.
RUN uv sync --frozen --no-dev --no-install-project
ENV PATH=/home/research/template/.venv/bin:$PATH

# Copy project files
COPY --chown=research:research . .

# Install project in editable mode with dev dependencies
RUN uv sync --frozen \
    && test "$(uv --version | cut -d ' ' -f 1-2)" = 'uv 0.13.0' \
    && python -c "import pathlib, re, sys; pins = [line.split('#', 1)[0].strip() for line in pathlib.Path('.python-version').read_text().splitlines() if line.split('#', 1)[0].strip()]; assert len(pins) == 1 and re.fullmatch(r'3\.\d+(?:\.\d+)?', pins[0]); expected = tuple(map(int, pins[0].split('.'))); assert sys.version_info[:len(expected)] == expected, (sys.version_info, expected)"

# Create volume mount point for data persistence
VOLUME ["/home/research/template/output"]

# Default command
CMD ["bash"]
