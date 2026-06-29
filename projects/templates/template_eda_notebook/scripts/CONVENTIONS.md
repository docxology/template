# Script Conventions

Orchestration rules and integration patterns for `scripts/` in the
`template_eda_notebook` exemplar.

## Thin Orchestrator Rules

Scripts **coordinate** — they never **compute**:

```python
# ✅ CORRECT: import tested functions, then plot/write
from src.eda import clean_dataset, load_dataset, histogram_data

clean, report = clean_dataset(load_dataset())
hist = histogram_data(clean, "height_cm", bins=10)
# ... plot hist with matplotlib, savefig, print the path
```

```python
# ❌ WRONG: script computes statistics directly
def my_summary(frame):
    return frame.mean()  # Data logic belongs in src/eda/
```

If you find yourself writing analysis logic in `scripts/`, move it to
`src/eda/` first (with a test).

## Headless plotting

Set the Agg backend **before** importing pyplot:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt
```

## Import Patterns

```python
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import matplotlib.pyplot as plt  # noqa: E402
from src.eda import load_dataset, clean_dataset  # noqa: E402
```

- Use explicit imports (not `from module import *`).
- Resolve paths relative to the project root — never hardcode an absolute path.

## Output Directory Structure

Scripts write to the standard output layout via `src/project_paths.py`:

```mermaid
flowchart LR
    OUT[output/]
    OUT --> FIG[figures/<br/>Generated plots · PNG]
    OUT --> DAT[data/<br/>Summary tables · CSV]
    OUT --> REP[reports/<br/>Validation reports]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    class OUT,FIG,DAT,REP d
```

```python
from src.project_paths import project_output_dirs

dirs = project_output_dirs()
dirs["figures"].mkdir(parents=True, exist_ok=True)
dirs["data"].mkdir(parents=True, exist_ok=True)
```

## Manifest Output

Print every written path to stdout so the pipeline can collect it:

```python
for path in run_eda():
    print(path)
```

## Checklist

Before submitting a new or modified script, verify:

- [ ] All analysis logic lives in `src/eda/`, not in the script.
- [ ] `MPLBACKEND=Agg` is set before importing pyplot.
- [ ] Output goes to standard `output/` subdirectories via `project_output_dirs`.
- [ ] `Path` objects are used (no string concatenation) for file paths.
- [ ] Every written path is printed for manifest collection.

## See Also

- [AGENTS.md](AGENTS.md) — Script roles and run commands.
- [../src/STYLE.md](../src/STYLE.md) — Style guide for the code scripts import.
- [../docs/architecture.md](../docs/architecture.md) — Thin-orchestrator flow diagram.
