# Refactoring Standards

## Core Principle: No Backward Compatibility

**CRITICAL RULE**: When refactoring or modularizing code:

1. **NO backward compatibility shims**
2. **NO deprecation warnings**
3. **NO legacy method wrappers**
4. **Clean break approach only**

### Rationale

- Backward compatibility adds technical debt
- Legacy code paths increase complexity and maintenance burden
- Clean breaks force comprehensive updates and prevent fragmented codebases
- All code should use the current, best structure

### Refactoring Process

When modularizing or restructuring:

1. **Create new modular structure** with clear separation of concerns
2. **Delete old files completely** - no leaving "deprecated" files around
3. **Update ALL imports** across the entire codebase immediately
4. **Update ALL tests** to use new imports
5. **Update ALL documentation** (AGENTS.md, README.md, docstrings)
6. **Run full test suite** to ensure nothing breaks
7. **Commit as single atomic change** with clear migration notes in commit message

### File Organization Best Practices

**Maximum file length**: 600 lines (excluding comprehensive docstrings)

**When to split a file**:
- Multiple independent classes/functions that could be separate modules
- Mixed concerns that would benefit from separation
- File exceeds 600 lines of actual code

**How to split**:
```
old_module.py (835 lines)
  ↓
new_structure/
├── __init__.py (exports all public API)
├── base.py (base classes, ~100 lines)
├── component_a.py (~250 lines)
├── component_b.py (~200 lines)
└── component_c.py (~200 lines)
```

### Import Updates

**Before refactoring**, search for all imports:
```bash
grep -r "from old_module import" .
grep -r "import old_module" .
```

**After refactoring**, update all imports:
- Infrastructure modules
- Test files
- Scripts
- Documentation examples

### Documentation Updates

Update in this order:
1. Module docstrings in new files
2. `__init__.py` exports with clear API
3. `AGENTS.md` with new architecture
4. `README.md` with new import examples
5. Any inline code examples in documentation

### Testing During Refactoring

1. **Before**: Ensure 100% test coverage of code being refactored
2. **During**: Update tests to import from new locations
3. **After**: Run full test suite with coverage report
4. **Verify**: No broken imports, all tests pass

### Example: Modularizing a Large File

**Bad** (backward compatibility approach):
```python
# old_api.py
import warnings
from new_module import *

warnings.warn("Use new_module instead", DeprecationWarning)
```

**Good** (clean break approach):
```python
# Delete old_api.py completely
# Update all imports:
# OLD: from old_api import Thing
# NEW: from new_module.things import Thing
```

### Commit Message Template

```
refactor: modularize [module_name] into focused submodules

BREAKING CHANGE: Split [old_file.py] into [new_structure/]

- Created new modular structure with clear separation
- Moved [Component A] to [new_location]
- Moved [Component B] to [new_location]
- Updated all imports across codebase
- Updated all tests
- Updated documentation (AGENTS.md, README.md)
- All tests passing with maintained coverage

Migration guide:
- OLD: from module.old import Thing
- NEW: from module.new.things import Thing
```

## Modularization Checklist

Before marking refactoring complete:

- [ ] New modular structure created
- [ ] Old file(s) deleted completely
- [ ] All infrastructure imports updated
- [ ] All test imports updated
- [ ] All script imports updated
- [ ] All documentation examples updated
- [ ] `__init__.py` exports public API clearly
- [ ] AGENTS.md reflects new structure
- [ ] README.md has updated examples
- [ ] Full test suite passes
- [ ] Test coverage maintained or improved
- [ ] No linter errors introduced
- [ ] Commit message documents migration

## Benefits of Clean Break Approach

1. **Clarity**: Only one way to import things
2. **Maintainability**: No legacy code paths to maintain
3. **Performance**: No deprecation warnings at runtime
4. **Quality**: Forces comprehensive updates
5. **Documentation**: Documentation stays current
6. **Testing**: Tests reflect actual usage
7. **Simplicity**: Codebase easier to understand

