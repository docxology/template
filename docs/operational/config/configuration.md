# Configuration Guide

> **reference** for all configuration options and environment variables

**Quick Reference:** [Troubleshooting Guide](../troubleshooting/) | [Performance Optimization](performance-optimization.md) | [Pipeline Orchestration](../../RUN_GUIDE.md)

This guide documents all configuration options available in the Research Project Template, including environment variables, configuration files, and runtime settings.

## Configuration Methods

The template supports three configuration methods (in priority order):

1. **Environment Variables** (highest priority - override all)
2. **Configuration File** (`projects/{name}/manuscript/config.yaml`)
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

**Location**: `projects/{name}/manuscript/config.yaml`  
**Template**: `projects/{name}/manuscript/config.yaml.example`

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
| `CHECKPOINT_DIR` | `projects/{name}/output/.checkpoints` | Checkpoint directory |
| `CHECKPOINT_ENABLED` | `true` | Enable checkpoint saving |

**Usage:**
```bash
# Resume from checkpoint
export PIPELINE_RESUME=1
uv run python scripts/execute_pipeline.py --project {name} --core-only

# Disable checkpoints
export CHECKPOINT_ENABLED=false
```

### Retry Configuration

Retry behavior is configured programmatically via the retry decorators:

```python
from infrastructure.core.runtime.retry import retry_with_backoff

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

### fep_lean (optional Open Gauss CLI)

`fep_lean` lives under **`projects/fep_lean/`** (discovered by `./run.sh` when present). Used by `projects/fep_lean/src/gauss/cli.py` and related orchestration modules:

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `FEP_LEAN_REQUIRE_GAUSS` | (unset) | If truthy, pipeline validation fails when `gauss` is missing or `gauss doctor` fails |
| `FEP_LEAN_GAUSS_WORKFLOWS` | (unset) | If truthy, analysis runs `lake build` in `projects/fep_lean/lean/` |
| `FEP_LEAN_TEST_GAUSS_DOCTOR` | (unset) | If set, enables an opt-in pytest that runs a real `gauss doctor` |
| `GAUSS_HOME` | `~/.gauss` | Writable directory checked for math-inc tooling layout |

Project-local reference: [projects/fep_lean/docs/opengauss.md](../../../projects/fep_lean/docs/opengauss.md).

### Literature Search


**Key Variables:**
- `LITERATURE_DEFAULT_LIMIT` - Results per source (default: 25)
- `LITERATURE_MAX_RESULTS` - Maximum total results (default: 100)
- `SEMANTICSCHOLAR_API_KEY` - API key for Semantic Scholar

### LLM Integration

See [LLM Configuration](../../../infrastructure/llm/AGENTS.md) for options.

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
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

### Verbose Debugging

```bash
# Enable debug logging
export LOG_LEVEL=0

# Run with detailed output
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

### Resume from Checkpoint

```bash
# Enable resume
export PIPELINE_RESUME=1

# Pipeline will resume from last successful stage
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

### Performance Monitoring

```bash
# Enable performance tracking
export ENABLE_PERFORMANCE_MONITORING=1
export PERFORMANCE_LOG_FILE="output/performance.log"

# Run with monitoring
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

## Configuration Validation

The template validates configuration at startup:

```bash
# Check configuration
uv run python -c "from infrastructure.core.config.loader import load_config; print(load_config())"
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

- [Troubleshooting Guide](../troubleshooting/) - Common issues and solutions
- [Build System](../../RUN_GUIDE.md) - Build configuration
- [Performance Optimization](performance-optimization.md) - Performance tuning













