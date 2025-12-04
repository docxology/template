# Scripts Directory: Ways Database Setup

## Overview

The `scripts/` directory contains **thin orchestrators** for ways of knowing database operations. These scripts import and use tested methods from `src/` modules.

## Key Principles

### 🚫 What Scripts Should NOT Do
- **Implement database logic** (use `src/database.py` instead)
- **Duplicate business logic** (import from `src/` instead)
- **Contain complex computations** (delegate to `src/` instead)

### ✅ What Scripts SHOULD Do
- **Import** methods from `src/` modules
- **Orchestrate** database setup and initialization
- **Handle** file I/O and directory management
- **Provide** clear error messages and logging

## Current Scripts

### `db_setup.py` - Database Initialization
**Purpose**: Initialize and set up the ways of knowing database

**src/ Usage**:
- `WaysDatabase` - Database ORM initialization
- `WaysSQLQueries` - SQL query execution

**What it does**:
- Imports database classes from `src/database.py`
- Initializes SQLite database schema
- Sets up database connection and tables
- Provides database initialization workflow

### `generate_figures.py` - Figure Generation
**Purpose**: Generate publication-quality figures for ways analysis

**src/ Usage**:
- `WaysDatabase` - Database access for ways data
- `WaysSQLQueries` - SQL queries for statistical data
- `models.Way` - Way data structures
- `models.Room` - Room data structures

**Generated Figures** (7 total):
- `ways_network.png` - Network visualization of ways relationships using NetworkX
- `room_hierarchy.png` - Hierarchical bar chart of room distributions
- `type_distribution.png` - Bar chart of dialogue type frequencies
- `type_room_heatmap.png` - Heatmap of dialogue type × room cross-tabulation
- `framework_treemap.png` - Hierarchical visualization of framework distribution
- `partner_wordcloud.png` - Dialogue partner frequency distribution
- `example_length_violin.png` - Example length distribution by dialogue type

**What it does**:
- Loads ways and room data directly from database
- Constructs network graphs and statistical visualizations
- Saves publication-quality PNG files (300 DPI)
- Handles edge cases (empty data, missing connections)
- Provides validation of generated file sizes

### `comprehensive_analysis.py` - Statistical Analysis
**Purpose**: Generate comprehensive statistical analysis with JSON/CSV exports

**src/ Usage**:
- `WaysAnalyzer` - Main ways analysis framework
- `WaysNetworkAnalyzer` - Network analysis with centrality metrics
- `WaysDatabase` - Database access
- `WaysSQLQueries` - SQL queries for data extraction

**Generated Outputs**:
- `comprehensive_stats.json` - Complete statistical summary in JSON format
- `room_distribution.csv` - Room distribution with percentages
- `dialogue_type_distribution.csv` - Dialogue type distribution
- `type_room_crosstab.csv` - Cross-tabulation matrix
- `network_centrality.csv` - Network centrality metrics

**What it does**:
- Generates comprehensive statistical summaries
- Computes information-theoretic metrics (entropy, mutual information)
- Performs network analysis with centrality calculations
- Exports data in JSON and CSV formats for manuscript integration
- Provides text analysis of examples and keywords

### `collect_manuscript_data.py` - Data Inspection Utility
**Purpose**: Quick utility script for manual data inspection and debugging

**src/ Usage**:
- `WaysAnalyzer` - Basic characterization
- `WaysNetworkAnalyzer` - Network metrics
- `WaysDatabase` - Database access
- `WaysSQLQueries` - SQL queries

**What it does**:
- Prints key statistics to console for quick inspection
- Useful for debugging and manual data verification
- Provides network metrics, distributions, and cross-tabulations
- For comprehensive analysis with exports, use `comprehensive_analysis.py` instead

## Import Pattern

```python
def _ensure_src_on_path() -> None:
    """Ensure src/ is on Python path for imports."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

# Import src/ methods
from database import WaysDatabase
```

## Usage Pattern

```python
def setup_database():
    # Use src/ methods for database setup
    db = WaysDatabase()  # From src/database.py
    db.initialize()
    
    return db
```

## Integration Examples

### Database Setup with src/ Methods
```python
# Instead of implementing database logic in the script:
# conn = sqlite3.connect('ways.db')  # ❌ Don't do this

# Use src/ methods:
from database import WaysDatabase

db = WaysDatabase()  # ✅ Do this
db.initialize()
```

## Adding New Scripts

### Template
```python
#!/usr/bin/env python3
"""Script description.

This script demonstrates ways database operations using src/ modules.
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
    
    # Use src/ methods
    db = WaysDatabase()
    # ... use db methods ...

if __name__ == "__main__":
    main()
```

### Checklist
- [ ] Imports methods from `src/` modules
- [ ] Uses `src/` methods for all computation
- [ ] Script only handles I/O and orchestration
- [ ] Includes proper error handling
- [ ] Has clear documentation

## Best Practices

### Do's
- ✅ Import and use `src/` methods extensively
- ✅ Handle file I/O and directory management
- ✅ Provide clear error messages and logging
- ✅ Use type hints and docstrings
- ✅ Follow the established import pattern

### Don'ts
- ❌ Implement database logic
- ❌ Duplicate business logic from `src/`
- ❌ Create complex data processing functions
- ❌ Skip error handling for imports
- ❌ Mix computation and orchestration logic

## Integration with Build System

### Automatic Execution
The build pipeline automatically:
1. Runs all tests in `tests/` (ensuring coverage)
2. Executes all scripts in `scripts/`
3. Validates generated files exist
4. Fails build if any script fails

## Summary

The `scripts/` directory demonstrates the **thin orchestrator pattern** where:

- **`src/`** contains all ways analysis logic and database operations
- **`scripts/`** contains lightweight wrappers that use `src/` methods
- **`tests/`** ensures coverage of `src/` functionality
- **Build pipeline** orchestrates the entire workflow

This architecture ensures:
- **Maintainability**: Single source of truth for business logic
- **Testability**: Fully tested core functionality
- **Reusability**: Scripts can use any `src/` method
- **Clarity**: Clear separation of concerns
- **Quality**: Automated validation of the entire system
