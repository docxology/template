# arXiv submission package

Build a `.tar.gz` for manual arXiv upload from project manuscript and build outputs.

```python
from infrastructure.publishing.arxiv import prepare_arxiv_submission

tar_path = prepare_arxiv_submission(Path("projects/my_project/output"), metadata)
```

See [AGENTS.md](AGENTS.md).
