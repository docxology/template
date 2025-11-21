# .cursorrules/ - Modular Development Rules

## Overview

This directory contains modular, focused rules for development in this repository. Rather than maintaining a single monolithic `.cursorrules` file, rules are organized by topic for clarity and maintainability.

## Rule Modules

Each module is self-contained and covers a specific aspect of development:

### Core Principles
- [**core_architecture.md**](core_architecture.md) - Overall system design and principles
  - Thin orchestrator pattern
  - Component separation
  - Build pipeline architecture

### Development Standards
- [**source_code_standards.md**](source_code_standards.md) - Code quality and style
  - Type hints and documentation
  - Naming conventions
  - Error handling patterns

- [**testing.md**](testing.md) - Testing requirements and practices
  - 100% coverage requirement
  - No mock methods policy
  - Real data and integration tests

- [**logging.md**](logging.md) - Logging standards across all scripts
  - Consistent log levels
  - Structured formatting
  - Accessibility features

### Build and Documentation
- [**build_pipeline.md**](build_pipeline.md) - Build orchestration details
  - Rendering pipeline stages
  - Dependency validation
  - Error handling

- [**documentation.md**](documentation.md) - Documentation standards
  - AGENTS.md structure
  - README.md format
  - Cross-referencing patterns

- [**markdown_structure.md**](markdown_structure.md) - Manuscript organization
  - Section numbering scheme
  - Cross-reference format
  - Equation and figure labeling

### Content and Output
- [**figure_generation.md**](figure_generation.md) - Figure generation patterns
  - Script structure (thin orchestrator)
  - Deterministic output
  - Figure registration
  - Reproducibility

## Using These Rules

### For Development
1. Read [core_architecture.md](core_architecture.md) first for overall system
2. Check relevant module before implementing features
3. Use as reference during code review
4. Update modules when standards change

### For Orientation
1. Start with [README.md](README.md) (this file) for overview
2. Read [core_architecture.md](core_architecture.md) for context
3. Browse specific modules as needed
4. Refer to top-level project documentation

### For IDE Integration
- Cursor reads all `.cursorrules` files in this directory
- Referenced as contextual guidance during development
- Used for code generation and suggestions
- Available in IDE comments and documentation

## File Organization

```
.cursorrules/
├── README.md                    # This file - overview and navigation
├── core_architecture.md         # Overall system design
├── thin_orchestrator.md         # Pattern details and examples
├── testing.md                   # Testing standards
├── logging.md                   # Logging standards
├── documentation.md             # Documentation requirements
├── build_pipeline.md            # Build orchestration
├── markdown_structure.md         # Manuscript organization
├── source_code_standards.md     # Code quality standards
└── figure_generation.md         # Figure generation patterns
```

## Quick Reference

### Most Important Rules
1. **Thin Orchestrator Pattern** ([core_architecture.md](core_architecture.md), [thin_orchestrator.md](thin_orchestrator.md))
   - All business logic in `src/`
   - Scripts handle I/O and orchestration only
   - No algorithm duplication

2. **100% Test Coverage** ([testing.md](testing.md))
   - All `src/` modules must have 100% coverage
   - Use REAL data, never mock methods
   - Integration tests validate full pipeline

3. **Complete Documentation** ([documentation.md](documentation.md))
   - Every directory has AGENTS.md and README.md
   - Clear, well-commented code
   - Auto-generated where possible

## Maintenance

### Adding New Rules
1. Create new markdown file in `.cursorrules/`
2. Update this README with reference
3. Ensure file covers one focused topic
4. Cross-reference related rules

### Updating Existing Rules
1. Edit relevant module file
2. Update README if topic changes
3. Notify team of significant changes
4. Maintain backward compatibility

### Consolidating Rules
If rules become too granular:
1. Merge closely related modules
2. Update cross-references
3. Maintain clear section breaks
4. Update this README

## Cross-References

Rules reference each other for context:

- [core_architecture.md](core_architecture.md) → [thin_orchestrator.md](thin_orchestrator.md)
- [testing.md](testing.md) → [core_architecture.md](core_architecture.md)
- [figure_generation.md](figure_generation.md) → [thin_orchestrator.md](thin_orchestrator.md)
- [build_pipeline.md](build_pipeline.md) → [testing.md](testing.md)
- [documentation.md](documentation.md) → All other modules

## Reading Path

**For new developers:**
1. [core_architecture.md](core_architecture.md) - Understand the system
2. [thin_orchestrator.md](thin_orchestrator.md) - Learn the pattern
3. [testing.md](testing.md) - Understand quality standards
4. Other modules as needed

**For code reviews:**
1. [source_code_standards.md](source_code_standards.md) - Check code quality
2. [testing.md](testing.md) - Verify test coverage
3. [thin_orchestrator.md](thin_orchestrator.md) - Check architecture
4. [documentation.md](documentation.md) - Verify documentation

**For build issues:**
1. [build_pipeline.md](build_pipeline.md) - Understand pipeline
2. [logging.md](logging.md) - Check log output
3. [testing.md](testing.md) - Verify tests pass
4. [documentation.md](documentation.md) - Check markup

## Key Principles (Summary)

From across all modules:

✅ **Modular**: Clear separation of concerns  
✅ **Testable**: 100% coverage, real data, no mocks  
✅ **Documented**: Every level has AGENTS.md + README.md  
✅ **Orchestrated**: Scripts coordinate, src/ computes  
✅ **Reproducible**: Deterministic outputs, fixed seeds  
✅ **Composable**: Reusable functions, clear interfaces  
✅ **Logged**: Structured logging with consistency  
✅ **Integrated**: Everything works together

## See Also

- [AGENTS.md](../AGENTS.md) - Complete system documentation
- [README.md](../README.md) - Project overview
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Detailed architecture

