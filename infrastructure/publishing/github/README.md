# GitHub releases

Create GitHub releases and upload assets via the REST API.

```python
from infrastructure.publishing.github import create_github_release

url = create_github_release(
    tag_name="v1.0.0",
    release_name="Release 1.0.0",
    description="Notes",
    assets=[Path("paper.pdf")],
    token=os.environ["GITHUB_TOKEN"],
    repo="owner/repo",
)
```

See [AGENTS.md](AGENTS.md).
