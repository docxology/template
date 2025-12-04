# scripts/ - Ways Database Setup Scripts

## Purpose

The `scripts/` directory contains thin orchestrators for ways of knowing database operations. Scripts import and use tested methods from `src/` modules - they never implement business logic themselves.

## Thin Orchestrator Pattern

### Core Principle
**All business logic lives in `src/`, scripts handle orchestration only.**

```
┌─────────────┐
│   src/      │ ← Ways analysis logic (100% tested)
│   database.py│
│   ways_analysis.py│
└──────┬──────┘
       │ import
       ↓
┌──────────────────┐
│   scripts/       │ ← Orchestration only
│   db_setup.py    │
└──────────────────┘
       │ generates
       ↓
┌──────────────────┐
│   db/            │ ← Database files
│   ways.db        │
└──────────────────┘
```

### What Scripts Do
✅ **Import** methods from `src/` modules  
✅ **Orchestrate** database initialization and setup  
✅ **Handle** file I/O and directory management  
✅ **Provide** clear error messages  
✅ **Demonstrate** integration patterns  

### What Scripts Don't Do
❌ **Implement** database logic (use `src/database.py`)  
❌ **Duplicate** business logic (import from `src/`)  
❌ **Contain** complex computations (delegate to `src/`)  

## Current Scripts

### db_setup.py
**Purpose**: Initialize and set up the ways of knowing database

**src/ Methods Used**:
- `WaysDatabase` - Database ORM initialization
- `WaysSQLQueries` - SQL query execution

**What It Generates**:
- `db/ways.db` - SQLite database file
- Database schema initialization
- Initial data loading if needed

**Key Pattern**: Shows how to initialize the ways database using `src/database.py` methods.

## Script Structure

### Standard Template

```python
#!/usr/bin/env python3
"""Script description.

This script demonstrates ways database setup using src/ modules.
"""
from __future__ import annotations

import os
import sys


def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path for imports."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def main() -> None:
    """Main script function."""
    # Ensure src/ is on path
    _ensure_src_on_path()
    
    # Import src/ methods
    try:
        from database import WaysDatabase
        print("✅ Successfully imported from src/")
    except ImportError as e:
        print(f"❌ Failed to import from src/: {e}")
        return
    
    # Use src/ methods for database setup
    db = WaysDatabase()
    db.initialize()
    
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    main()
```

## Import Pattern

### Step 1: Add src/ to Path
```python
def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

_ensure_src_on_path()
```

### Step 2: Import with Error Handling
```python
try:
    from database import WaysDatabase
    from ways_analysis import WaysAnalyzer
    print("✅ Successfully imported from src/")
except ImportError as e:
    print(f"❌ Failed to import from src/: {e}")
    print("   Ensure src/ modules exist and are importable")
    return
```

### Step 3: Use Imported Methods
```python
# Instead of implementing:
# db = sqlite3.connect('ways.db')  # ❌ Don't do this

# Use src/ methods:
db = WaysDatabase()  # ✅ Do this
db.initialize()
```

## Integration Examples

### Database Setup
```python
# ❌ BAD: Implementing database logic in script
def setup_database():
    conn = sqlite3.connect('ways.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE ways ...')

# ✅ GOOD: Using src/ methods
from database import WaysDatabase

def setup_database():
    db = WaysDatabase()
    db.initialize()
```

## Error Handling

### Import Errors
```python
try:
    from database import WaysDatabase
except ImportError as e:
    print(f"❌ Failed to import from src/: {e}")
    print("   1. Ensure src/database.py exists")
    print("   2. Verify src/ is on Python path")
    print("   3. Check for syntax errors in src/")
    return
```

### Database Errors
```python
try:
    db = WaysDatabase()
    db.initialize()
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    return
```

## Adding New Scripts

### Checklist
- [ ] Script imports from `src/` modules
- [ ] Uses `src/` methods for all computation
- [ ] Handles only I/O, orchestration
- [ ] Includes `_ensure_src_on_path()` function
- [ ] Has error handling for imports
- [ ] Provides clear progress messages
- [ ] Saves to appropriate directories
- [ ] Has clear documentation

### Development Process
1. **Identify needed functionality** - what does script need to do?
2. **Check if src/ has it** - look in `src/` modules
3. **If missing, add to src/ first** - implement and test in `src/`
4. **Create script** - import and use `src/` methods
5. **Test script** - add tests in `tests/`
6. **Integrate** - ensure build system runs it

## Integration with Build System

### Automatic Execution
The build pipeline automatically:
1. Runs all tests (validates `src/` works)
2. Executes all `*.py` files in `scripts/`
3. Captures output paths
4. Validates generated files exist
5. Fails build if any script fails

## Best Practices

### Do's
✅ Import extensively from `src/` modules  
✅ Use descriptive variable names  
✅ Handle errors gracefully  
✅ Print clear progress messages  
✅ Use type hints  
✅ Document what src/ methods are used  

### Don'ts
❌ Implement algorithms (add to `src/` instead)  
❌ Duplicate logic from `src/`  
❌ Skip error handling  
❌ Hardcode paths  
❌ Mix computation and orchestration logic  

## See Also

- [`README.md`](README.md) - Scripts overview and quick start
- [`../src/`](../src/) - Available ways analysis modules
- [`../tests/AGENTS.md`](../tests/AGENTS.md) - Testing scripts
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
