# Infrastructure Modules

Reusable build tools, validation systems, and integration components that support research projects. These modules provide the foundation for reproducible, high-quality research workflows.

## Overview

The infrastructure layer provides generic, reusable functionality that can be applied across different research projects. All modules follow the **thin orchestrator pattern** - scripts coordinate business logic implemented in these infrastructure modules.

## Module Categories

### Core Infrastructure
- **[core/](core/)** - Fundamental utilities (logging, configuration, progress tracking)
- **[core/](core/)** - Custom exception hierarchy and error handling

### Document Processing
- **[documentation/](documentation/)** - Figure management and API documentation generation
- **[rendering/](rendering/)** - Multi-format output generation (PDF, HTML, slides)
- **[validation/](validation/)** - Quality assurance and content validation

### External Integrations
- **[llm/](llm/)** - Local Large Language Model integration
- **[publishing/](publishing/)** - Academic publishing workflows
- **[scientific/](scientific/)** - Scientific computing utilities

### Build & Quality
- **[reporting/](reporting/)** - Pipeline reporting and error aggregation

## Usage in Projects

Infrastructure modules are imported by project-specific scripts:

```python
# In project/scripts/analysis.py
from infrastructure.rendering import RenderManager
from infrastructure.validation import validate_markdown
from infrastructure.llm.core import LLMClient

# Use infrastructure components
renderer = RenderManager()
client = LLMClient()
```

## Testing

Infrastructure modules maintain **83.33% test coverage** (exceeds 60% requirement):

```bash
# Test all infrastructure
pytest tests/infrastructure/ --cov=infrastructure --cov-report=term-missing

# Test specific module
pytest tests/infrastructure/core/ -v
```

## Architecture Principles

### Thin Orchestrator Pattern
- **Business logic** resides in infrastructure modules
- **Scripts** provide thin orchestration layer
- **Clean separation** between reusable code and project-specific logic

### Real Data Policy
- **No mock methods** in business logic
- **Real computations** with actual data
- **Deterministic outputs** for reproducibility

### Comprehensive Validation
- **Quality assurance** for all outputs
- **Integration testing** across modules
- **Error handling** with informative messages

## Development

### Adding New Infrastructure

1. Create module in appropriate category
2. Implement business logic with comprehensive tests
3. Add AGENTS.md documentation
4. Update integration tests
5. Ensure 60%+ test coverage

### Module Structure
```
infrastructure/new_module/
├── __init__.py      # Public API exports
├── core.py          # Main functionality
├── utils.py         # Helper functions
├── cli.py           # Command-line interface (if needed)
├── AGENTS.md        # Technical documentation
└── README.md        # Quick reference
```

## Quality Standards

- **Test Coverage**: Minimum 60% for infrastructure modules
- **Documentation**: Complete AGENTS.md for all modules
- **Error Handling**: Comprehensive exception handling
- **Performance**: Efficient resource usage
- **Security**: Safe credential handling

## See Also

- [AGENTS.md](AGENTS.md) - Complete infrastructure documentation
- [../tests/infrastructure/](../tests/infrastructure/) - Infrastructure test suite
- [../scripts/](../scripts/) - Orchestration scripts