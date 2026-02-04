# Logging Directory

> **Topic-specific logging guides** for the Research Project Template

## Quick Navigation

| Topic | Guide | Description |
|-------|-------|-------------|
| 🐍 **Python** | [PYTHON_LOGGING.md](PYTHON_LOGGING.md) | Python logging system |
| 🐚 **Bash** | [BASH_LOGGING.md](BASH_LOGGING.md) | Shell script logging |
| 📋 **Patterns** | [LOGGING_PATTERNS.md](LOGGING_PATTERNS.md) | Best practices, progress, troubleshooting |

## Quick Start

### Python

```python
from infrastructure.core.logging_utils import get_logger
logger = get_logger(__name__)
logger.info("Processing started")
```

### Bash

```bash
source scripts/bash_utils.sh
log_success "Operation completed"
```

## See Also

- [Main Logging Guide](../LOGGING_GUIDE.md) - Overview
- [Error Handling Guide](../ERROR_HANDLING_GUIDE.md) - Exception usage
- [Troubleshooting](../TROUBLESHOOTING_GUIDE.md) - Common issues
