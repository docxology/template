# Logging Directory

> **Topic-specific logging guides** for the Research Project Template

## Quick Navigation

| Topic | Guide | Description |
|-------|-------|-------------|
| 🐍 **Python** | [python-logging.md](python-logging.md) | Python logging system |
| 🐚 **Bash** | [bash-logging.md](bash-logging.md) | Shell script logging |
| 📋 **Patterns** | [logging-patterns.md](logging-patterns.md) | Best practices, progress, troubleshooting |

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

- [Main Logging Guide](../logging-guide.md) - Overview
- [Error Handling Guide](../error-handling-guide.md) - Exception usage
- [Troubleshooting](../troubleshooting-guide.md) - Common issues
