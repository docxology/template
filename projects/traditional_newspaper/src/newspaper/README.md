# `src/newspaper/`

Layout constants, section inventory, deterministic fixture copy, Pandoc/LaTeX snippet builders, and masthead rasterization for the Template Gazette exemplar.

## Imports

```python
from newspaper import (
    LAYOUT,
    fixture_copy,
    get_slice,
    render_masthead_png,
    PAGE_SLICES,
    multicol_begin,
    all_tracked_manuscript_basenames,
)
```

## See also

- [AGENTS.md](AGENTS.md)
