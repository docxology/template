# Code development — patterns

## Thin orchestrator (script)

```python
from pathlib import Path
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

def main() -> None:
    output_dir = Path("projects/<project>/output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Import computation from src/
    # Handle visualization only here
    print(output_path)  # for manifest collection
```

## Error handling

```python
from infrastructure.core.exceptions import TemplateError

class DomainError(TemplateError):
    pass
```

## API shape

- Keyword-only options after `*` where extensibility matters
- `Path` for filesystem locations
- Return typed structures or dataclasses, not bare dicts when stable

## Layer decision

| Criterion | infrastructure | project src |
| --- | --- | --- |
| Reusable across projects | yes | no |
| Domain-specific research | no | yes |
| Coverage floor | 60% | 90% |
