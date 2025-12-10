# Configuration Guide

> **Complete reference** for all configuration options and environment variables

**Quick Reference:** [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) | [Performance Optimization](PERFORMANCE_OPTIMIZATION.md) | [Build System](BUILD_SYSTEM.md)

This guide documents all configuration options available in the Research Project Template, including environment variables, configuration files, and runtime settings.

## Configuration Methods

The template supports three configuration methods (in priority order):

1. **Environment Variables** (highest priority - override all)
2. **Configuration File** (`project/manuscript/config.yaml`)
3. **Default Values** (lowest priority)

## Core Configuration

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `1` | Logging verbosity: `0`=DEBUG, `1`=INFO, `2`=WARN, `3`=ERROR |
| `NO_EMOJI` | (unset) | Disable emoji in log output |
| `NO_COLOR` | (unset) | Disable colorized output |

**Example:**
```bash
export LOG_LEVEL=0  # Enable debug logging
export NO_EMOJI=1   # Disable emojis
```

### Paper Metadata

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTHOR_NAME` | `"Project Author"` | Primary author name |
| `AUTHOR_ORCID` | `"0000-0000-0000-0000"` | Author ORCID identifier |
| `AUTHOR_EMAIL` | `"author@example.com"` | Author contact email |
| `PROJECT_TITLE` | `"Project Title"` | Project/research title |
| `DOI` | `""` | Digital Object Identifier (optional) |

### Pipeline Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PIPELINE_RESUME` | (unset) | Resume from checkpoint if available |
| `PIPELINE_CLEAN` | (unset) | Clean output directories before run |

## Configuration File

### Location

**Location**: `project/manuscript/config.yaml`  
**Template**: `project/manuscript/config.yaml.example`

### Structure

```yaml
paper:
  title: "Your Research Title"
  subtitle: ""  # Optional
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "University of Example"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional
  journal: ""  # Optional
  volume: ""  # Optional
  pages: ""  # Optional

keywords:
  - "optimization"
  - "machine learning"

metadata:
  license: "Apache-2.0"
  language: "en"
```

### Benefits

- ✅ Version controllable (can be committed to git)
- ✅ Single file for all metadata
- ✅ Supports multiple authors with affiliations
- ✅ Structured format (YAML)
- ✅ Easy to edit and maintain

## Advanced Configuration

### Performance Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PERFORMANCE_MONITORING` | (unset) | Enable resource tracking |
| `PERFORMANCE_LOG_FILE` | (unset) | Path to performance log file |

### Checkpoint System

| Variable | Default | Description |
|----------|---------|-------------|
| `CHECKPOINT_DIR` | `project/output/.checkpoints` | Checkpoint directory |
| `CHECKPOINT_ENABLED` | `true` | Enable checkpoint saving |

**Usage:**
```bash
# Resume from checkpoint
export PIPELINE_RESUME=1
python3 scripts/run_all.py

# Disable checkpoints
export CHECKPOINT_ENABLED=false
```

### Retry Configuration

Retry behavior is configured programmatically via the retry decorators:

```python
from infrastructure.core.retry import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0
)
def risky_operation():
    # Will retry up to 3 times with exponential backoff
    pass
```

## Module-Specific Configuration

### Literature Search

See [Literature Search Configuration](../infrastructure/literature/AGENTS.md#configuration) for complete options.

**Key Variables:**
- `LITERATURE_DEFAULT_LIMIT` - Results per source (default: 25)
- `LITERATURE_MAX_RESULTS` - Maximum total results (default: 100)
- `SEMANTICSCHOLAR_API_KEY` - API key for Semantic Scholar

### LLM Integration

See [LLM Configuration](../infrastructure/llm/README.md) for complete options.

**Key Variables:**
- `OLLAMA_HOST` - Ollama server URL (default: `http://localhost:11434`)
- `LLM_MAX_INPUT_LENGTH` - Max characters to send (default: 500000)
- `LLM_REVIEW_TIMEOUT` - Timeout per review in seconds (default: 300)

### Rendering

| Variable | Default | Description |
|----------|---------|-------------|
| `RENDERING_FORMAT` | `pdf` | Output format: `pdf`, `html`, `slides` |
| `RENDERING_ENGINE` | `xelatex` | LaTeX engine: `xelatex`, `pdflatex`, `lualatex` |

## Configuration Examples

### Basic Setup

```bash
# Set author information
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_EMAIL="jane@example.edu"
export PROJECT_TITLE="My Research Project"

# Run pipeline
python3 scripts/run_all.py
```

### Verbose Debugging

```bash
# Enable debug logging
export LOG_LEVEL=0

# Run with detailed output
python3 scripts/run_all.py
```

### Resume from Checkpoint

```bash
# Enable resume
export PIPELINE_RESUME=1

# Pipeline will resume from last successful stage
python3 scripts/run_all.py
```

### Performance Monitoring

```bash
# Enable performance tracking
export ENABLE_PERFORMANCE_MONITORING=1
export PERFORMANCE_LOG_FILE="output/performance.log"

# Run with monitoring
python3 scripts/run_all.py
```

## Configuration Validation

The template validates configuration at startup:

```bash
# Check configuration
python3 -c "from infrastructure.core.config_loader import load_config; print(load_config())"
```

## Best Practices

1. **Use Configuration File** for persistent settings
2. **Use Environment Variables** for temporary overrides
3. **Version Control** configuration files (not secrets)
4. **Document** custom configurations in project README
5. **Validate** configuration before running pipeline

## Troubleshooting

### Configuration Not Applied

1. Check environment variable priority
2. Verify configuration file syntax (YAML)
3. Check for typos in variable names
4. Review log output for configuration errors

### See Also

- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) - Common issues and solutions
- [Build System](BUILD_SYSTEM.md) - Build configuration
- [Performance Optimization](PERFORMANCE_OPTIMIZATION.md) - Performance tuning





